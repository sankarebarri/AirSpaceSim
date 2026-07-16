# simulation/aircraft_manager.py
import threading
import json
import time
import os
import tempfile
from datetime import datetime, timezone
from airspacesim.core.models import TrajectoryTrack
from airspacesim.simulation.aircraft import Aircraft
from airspacesim.io.contracts import build_envelope, validate_trajectory_v01
from airspacesim.settings import settings
from airspacesim.utils.conversions import dms_to_decimal, haversine
from airspacesim.utils.logging_config import default_logger as logger


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".airspacesim.", suffix=".tmp", dir=os.path.dirname(path)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(payload, tmp_file, indent=4)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _resolve_flight_level_for_output(aircraft):
    raw_flight_level = getattr(aircraft, "flight_level", None)
    if isinstance(raw_flight_level, (int, float)):
        return int(round(float(raw_flight_level)))
    altitude_ft = float(getattr(aircraft, "altitude_ft", 0.0))
    if altitude_ft < 0:
        altitude_ft = 0.0
    return int(round(altitude_ft / 100.0))


class AircraftManager:
    def __init__(
        self,
        routes,
        execution_mode="thread_per_aircraft",
        sim_rate=1.0,
        enable_file_output=True,
    ):
        """
        Initialize an Aircraft Manager to handle multiple aircraft simulations.

        :param routes: Dictionary of predefined routes with waypoints in DMS format.
        :param execution_mode: "thread_per_aircraft" (legacy) or "batched".
        :param sim_rate: Time-acceleration multiplier applied by this manager's
            own loops (simulated seconds per real second). Scoped per manager,
            not process-wide.
        :param enable_file_output: When False, save_aircraft_data() is a no-op
            so embedding applications (for example the hosted API) can drive
            the manager without JSON file side effects.
        """
        self.aircraft_list = []  # Stores active aircraft
        self.routes = routes  # Available routes
        self.execution_mode = execution_mode
        self.sim_rate = float(sim_rate)
        self.enable_file_output = bool(enable_file_output)
        self.threads = []  # List to track active simulation threads
        self.lock = threading.Lock()  # Thread safety
        self.stop_event = threading.Event()
        self._batch_thread = None

    def _is_near_airspace_center(self, point_dd):
        if not isinstance(point_dd, (list, tuple)) or len(point_dd) != 2:
            return False
        center_lat, center_lon = settings.AIRSPACE_CENTER
        distance_nm = haversine(
            float(point_dd[0]),
            float(point_dd[1]),
            float(center_lat),
            float(center_lon),
        )
        return distance_nm <= 1.0

    def classify_traffic_flow_from_waypoints(self, waypoints):
        """
        Classify aircraft flow relative to configured airspace center:
        - outbound: starts near center and leaves
        - inbound: ends near center
        - transit: crosses/contains center internally
        - unknown: cannot infer from route geometry
        """
        if not isinstance(waypoints, list) or len(waypoints) < 2:
            return "unknown"

        start_near_center = self._is_near_airspace_center(waypoints[0])
        end_near_center = self._is_near_airspace_center(waypoints[-1])
        if start_near_center and not end_near_center:
            return "outbound"
        if end_near_center and not start_near_center:
            return "inbound"

        if any(self._is_near_airspace_center(point) for point in waypoints[1:-1]):
            return "transit"

        if start_near_center and end_near_center:
            return "transit"

        return "unknown"

    def set_simulation_speed(self, sim_rate):
        """
        Set this manager's simulation speed multiplier (simulated seconds per
        real second), applied by the manager's own stepping loops.
        """
        value = float(sim_rate)
        if value <= 0:
            raise ValueError("Simulation speed multiplier must be > 0")
        self.sim_rate = value
        logger.info("Simulation speed multiplier set to %.3f", value)
        self.save_aircraft_data()

    def add_aircraft(
        self,
        id,
        route_name,
        callsign="Unknown",
        stop_flag=None,
        speed=None,
        altitude_ft=0.0,
        vertical_rate_fpm=0.0,
        flight_level=None,
        aircraft_type="UNKNOWN",
    ):
        """
        Adds a new aircraft and starts its simulation.
        """
        if route_name not in self.routes:
            logger.error("Route '%s' does not exist.", route_name)
            raise ValueError(f"Route '{route_name}' does not exist.")

        # Convert waypoints to decimal degrees.
        waypoints = []
        waypoint_ids = []
        for wp in self.routes[route_name]:
            waypoint_ids.append(str(wp.get("id") or wp.get("name") or len(waypoint_ids)))
            if "dec_coords" in wp:
                coords = wp["dec_coords"]
            else:
                try:
                    coords = [
                        dms_to_decimal(*wp["coords"]["lat"]),
                        dms_to_decimal(*wp["coords"]["lon"]),
                    ]
                except Exception:
                    logger.exception(
                        "Error converting DMS to decimal for waypoint: %s", wp
                    )
                    raise
            waypoints.append(coords)

        try:
            aircraft = Aircraft(
                id,
                route_name,
                waypoints,
                speed=speed if speed is not None else settings.DEFAULT_SPEED_KNOTS,
                callsign=callsign,
                altitude_ft=altitude_ft,
                vertical_rate_fpm=vertical_rate_fpm,
                flight_level=flight_level,
                aircraft_type=aircraft_type,
                waypoint_ids=waypoint_ids,
            )
            aircraft.traffic_flow = self.classify_traffic_flow_from_waypoints(waypoints)
            with self.lock:
                self.aircraft_list.append(aircraft)
        except Exception:
            logger.exception("Error creating Aircraft instance for ID: %s", id)
            raise

        if self.execution_mode == "batched":
            logger.debug(
                "Aircraft %s added on route %s (batched mode).", id, route_name
            )
            return

        active_stop_flag = stop_flag or self.stop_event
        thread = threading.Thread(
            target=self.simulate_aircraft, args=(aircraft, active_stop_flag)
        )
        thread.start()
        with self.lock:
            self.threads.append(thread)
        logger.info(
            "Aircraft %s added on route %s with callsign %s.", id, route_name, callsign
        )

    def simulate_aircraft(self, aircraft, stop_flag):
        """
        Simulate the aircraft's movement based on its speed.
        """
        logger.info(
            "🛫 Starting simulation for %s (%s)...", aircraft.id, aircraft.callsign
        )
        try:
            while aircraft.current_index < len(aircraft.waypoints) - 1:
                if stop_flag and stop_flag.is_set():
                    logger.info("⛔ Simulation for %s interrupted.", aircraft.id)
                    return
                aircraft.update_position(
                    settings.SIMULATION_UPDATE_INTERVAL * self.sim_rate
                )
                self.save_aircraft_data()
                time.sleep(settings.SIMULATION_UPDATE_INTERVAL)
            # Mark aircraft as finished and record the finish time.
            aircraft.finished_time = time.time()
            self.save_aircraft_data()
            logger.info(
                "✅ %s has completed its route at %s.",
                aircraft.id,
                aircraft.finished_time,
            )
        except Exception:
            logger.exception("Error during simulation for aircraft %s", aircraft.id)

    def save_aircraft_data(self):
        """
        Saves the current positions, callsigns, and speeds of all aircraft to JSON.
        Also logs the number and IDs of aircraft being saved.

        No-op when the manager was created with enable_file_output=False.
        """
        if not self.enable_file_output:
            return
        with self.lock:
            timestamp = _utc_now_iso()
            legacy_aircraft_rows = [
                {
                    "id": ac.id,
                    "position": ac.position,
                    "callsign": ac.callsign,
                    "aircraft_type": getattr(ac, "aircraft_type", "UNKNOWN"),
                    "speed": ac.speed,
                    "flight_level": _resolve_flight_level_for_output(ac),
                    "target_flight_level": getattr(ac, "target_flight_level", None),
                    "altitude_ft": ac.altitude_ft,
                    "vertical_rate_fpm": ac.vertical_rate_fpm,
                    "heading_deg": getattr(ac, "heading_deg", 0.0),
                    "assigned_heading_deg": getattr(ac, "assigned_heading_deg", None),
                    "assigned_radial_deg": getattr(ac, "assigned_radial_deg", None),
                    "radial_deviation_deg": getattr(ac, "radial_deviation_deg", None),
                    "radial_cross_track_nm": getattr(ac, "radial_cross_track_nm", None),
                    "lateral_mode": getattr(ac, "lateral_mode", "route"),
                    "traffic_flow": getattr(ac, "traffic_flow", "unknown"),
                }
                for ac in self.aircraft_list
            ]
            legacy_data = {
                **build_envelope(
                    schema_name="airspacesim.aircraft_data",
                    source="airspacesim.simulation.aircraft_manager",
                    generated_utc=timestamp,
                    data={"aircraft_data": legacy_aircraft_rows},
                ),
                # Compatibility shim for legacy UI readers.
                "aircraft_data": legacy_aircraft_rows,
            }
            canonical_data = build_envelope(
                schema_name="airspacesim.aircraft_state",
                source="airspacesim.simulation.aircraft_manager",
                generated_utc=timestamp,
                data={
                    "aircraft": [
                        {
                            "id": ac.id,
                            "callsign": ac.callsign,
                            "aircraft_type": getattr(ac, "aircraft_type", "UNKNOWN"),
                            "speed_kt": ac.speed,
                            "flight_level": _resolve_flight_level_for_output(ac),
                            "target_flight_level": getattr(
                                ac,
                                "target_flight_level",
                                None,
                            ),
                            "altitude_ft": ac.altitude_ft,
                            "vertical_rate_fpm": ac.vertical_rate_fpm,
                            "heading_deg": getattr(ac, "heading_deg", 0.0),
                            "assigned_heading_deg": getattr(
                                ac,
                                "assigned_heading_deg",
                                None,
                            ),
                            "assigned_radial_deg": getattr(
                                ac,
                                "assigned_radial_deg",
                                None,
                            ),
                            "radial_deviation_deg": getattr(
                                ac,
                                "radial_deviation_deg",
                                None,
                            ),
                            "radial_cross_track_nm": getattr(
                                ac,
                                "radial_cross_track_nm",
                                None,
                            ),
                            "lateral_mode": getattr(ac, "lateral_mode", "route"),
                            "direct_to_fix_id": getattr(ac, "direct_to_fix_id", None),
                            "hold_fix_id": getattr(ac, "hold_fix_id", None),
                            "traffic_flow": getattr(ac, "traffic_flow", "unknown"),
                            "route_id": ac.route,
                            "position_dd": ac.position,
                            "status": "finished"
                            if hasattr(ac, "finished_time")
                            else "active",
                            "updated_utc": timestamp,
                        }
                        for ac in self.aircraft_list
                    ]
                },
            )
            trajectory_data = build_envelope(
                schema_name="airspacesim.trajectory",
                schema_version="0.1",
                source="airspacesim.simulation.aircraft_manager",
                generated_utc=timestamp,
                data={
                    "tracks": [
                        TrajectoryTrack(
                            id=ac.id,
                            callsign=ac.callsign,
                            route_id=ac.route,
                            position_dd=(float(ac.position[0]), float(ac.position[1])),
                            speed_kt=float(ac.speed),
                            flight_level=_resolve_flight_level_for_output(ac),
                            altitude_ft=float(ac.altitude_ft),
                            vertical_rate_fpm=float(ac.vertical_rate_fpm),
                            status="finished"
                            if hasattr(ac, "finished_time")
                            else "active",
                            updated_utc=timestamp,
                        ).as_contract_dict()
                        for ac in self.aircraft_list
                    ],
                },
            )
            try:
                validate_trajectory_v01(trajectory_data)
                _atomic_write_json(settings.AIRCRAFT_FILE, legacy_data)
                _atomic_write_json(settings.AIRCRAFT_STATE_FILE, canonical_data)
                _atomic_write_json(settings.TRAJECTORY_FILE, trajectory_data)
                ids = [ac["id"] for ac in legacy_data["aircraft_data"]]
                logger.debug(
                    "Saved aircraft data: %d aircraft in list. IDs: %s", len(ids), ids
                )
            except Exception:
                logger.exception("Failed to write aircraft data to file.")

    def monitor_new_aircraft(self, stop_flag):
        """
        Continuously checks the configured ingest file for new aircraft and adds them dynamically.
        Supports both flat and nested structures, processing entries in a batch.
        """
        while not stop_flag.is_set():
            try:
                with open(settings.NEW_AIRCRAFT_FILE, "r") as f:
                    new_data = json.load(f)

                batch = []
                if new_data.get("aircraft"):
                    for entry in new_data["aircraft"]:
                        if "route" in entry:
                            batch.append(entry)
                        elif "aircraft" in entry and isinstance(
                            entry["aircraft"], list
                        ):
                            batch.extend(entry["aircraft"])
                        else:
                            logger.error(
                                "New aircraft entry missing 'route': %s", entry
                            )

                    for ac in batch:
                        if "route" not in ac:
                            logger.error("New aircraft entry missing 'route': %s", ac)
                            continue
                        self.add_aircraft(
                            ac["id"],
                            ac["route"],
                            ac.get("callsign", "Unknown"),
                            stop_flag,
                            ac.get("speed", None),
                            ac.get("altitude_ft", 0.0),
                            ac.get("vertical_rate_fpm", 0.0),
                            ac.get("flight_level"),
                            ac.get("aircraft_type", "UNKNOWN"),
                        )
                    # Clear the JSON file after processing.
                    with open(settings.NEW_AIRCRAFT_FILE, "w") as f:
                        json.dump({"aircraft": []}, f, indent=4)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning("Error reading aircraft ingest file: %s", e)
            except Exception:
                logger.exception("Unexpected error in monitor_new_aircraft.")
            time.sleep(2)

    def cleanup_finished_aircraft(self, stop_flag):
        """
        Periodically scans the active aircraft list and removes any aircraft
        that have been finished for more than 2 minutes (120 seconds) in real time.
        After cleanup, it updates the aircraft_data.json file.
        """
        logger.info("Starting cleanup thread for finished aircraft.")
        while not stop_flag.is_set():
            should_save = False
            with self.lock:
                current_time = time.time()
                # Log status of finished aircraft.
                finished_aircraft = [
                    (ac.id, ac.finished_time, current_time - ac.finished_time)
                    for ac in self.aircraft_list
                    if hasattr(ac, "finished_time")
                ]
                if finished_aircraft:
                    for ac_id, finish_time, elapsed in finished_aircraft:
                        logger.debug(
                            "Aircraft %s finished at %s, elapsed time: %.2f sec",
                            ac_id,
                            finish_time,
                            elapsed,
                        )
                else:
                    logger.debug("No aircraft marked as finished in this cycle.")

                before_cleanup = len(self.aircraft_list)
                self.aircraft_list = [
                    ac
                    for ac in self.aircraft_list
                    if not hasattr(ac, "finished_time")
                    or (current_time - ac.finished_time) < 120
                ]
                after_cleanup = len(self.aircraft_list)
                cleaned_count = before_cleanup - after_cleanup
                if cleaned_count > 0:
                    logger.info("Cleaned up %d finished aircraft.", cleaned_count)
                    should_save = True
                else:
                    logger.debug("No aircraft cleaned up in this cycle.")
            if should_save:
                self.save_aircraft_data()
            time.sleep(10)
        logger.info("Cleanup thread terminating.")

    def delete_aircraft(self, aircraft_id):
        """
        Deletes an aircraft from the active list by its ID.
        """
        with self.lock:
            initial_count = len(self.aircraft_list)
            self.aircraft_list = [
                ac for ac in self.aircraft_list if ac.id != aircraft_id
            ]
            if len(self.aircraft_list) < initial_count:
                logger.info("Aircraft %s deleted.", aircraft_id)
            else:
                logger.warning("Aircraft %s not found for deletion.", aircraft_id)

    def request_shutdown(self):
        """Signal all simulation workers to stop at the next safe check."""
        self.stop_event.set()

    def run_batched_for(self, duration_seconds, update_interval=None):
        """
        Run all aircraft in a single scheduler loop for a fixed duration.
        This mode scales better for high aircraft counts than thread-per-aircraft.
        """
        if self.execution_mode != "batched":
            raise ValueError(
                "run_batched_for is only available when execution_mode='batched'"
            )
        interval = (
            update_interval
            if update_interval is not None
            else settings.SIMULATION_UPDATE_INTERVAL
        )
        end_time = time.time() + duration_seconds
        while time.time() < end_time and not self.stop_event.is_set():
            self._step_all_aircraft(interval)
            self.save_aircraft_data()
            time.sleep(interval)

    def _step_all_aircraft(self, interval):
        simulated_seconds = float(interval) * self.sim_rate
        with self.lock:
            aircraft_list = list(self.aircraft_list)
        for aircraft in aircraft_list:
            if aircraft.current_index < len(aircraft.waypoints) - 1:
                aircraft.update_position(simulated_seconds)
                if aircraft.current_index >= len(
                    aircraft.waypoints
                ) - 1 and not hasattr(aircraft, "finished_time"):
                    aircraft.finished_time = time.time()

    def terminate_simulations(self, timeout_seconds=None):
        """
        Force-stop simulation workers and wait for thread termination.
        """
        self.request_shutdown()
        for thread in self.threads:
            thread.join(timeout=timeout_seconds)
            if thread.is_alive():
                logger.warning("Simulation thread did not terminate within timeout.")
        if self._batch_thread is not None:
            self._batch_thread.join(timeout=timeout_seconds)
            if self._batch_thread.is_alive():
                logger.warning(
                    "Batched simulation thread did not terminate within timeout."
                )
        logger.info("All simulation threads have terminated.")

    def wait_for_completion(self, timeout_seconds=None):
        """
        Wait until all aircraft reach final destination without forcing interruption.
        """
        timed_out = False
        if self.execution_mode == "batched":
            interval = settings.SIMULATION_UPDATE_INTERVAL
            start_time = time.time()
            while True:
                with self.lock:
                    has_active_aircraft = any(
                        ac.current_index < len(ac.waypoints) - 1
                        for ac in self.aircraft_list
                    )
                if not has_active_aircraft:
                    break
                if (
                    timeout_seconds is not None
                    and (time.time() - start_time) > timeout_seconds
                ):
                    logger.warning(
                        "Timed out while waiting for batched simulations to complete."
                    )
                    timed_out = True
                    break
                if self.stop_event.is_set():
                    logger.info("Completion wait interrupted by stop event.")
                    break
                self._step_all_aircraft(interval)
                self.save_aircraft_data()
                time.sleep(interval)
            if timed_out:
                logger.info("Simulation wait ended before all aircraft completed.")
            else:
                logger.info("All simulations completed.")
            return

        start_time = time.time()
        for thread in self.threads:
            if timeout_seconds is None:
                thread.join()
            else:
                elapsed = time.time() - start_time
                remaining = max(timeout_seconds - elapsed, 0)
                thread.join(timeout=remaining)
                if thread.is_alive():
                    logger.warning("Timed out while waiting for simulation completion.")
                    timed_out = True
                    break
        if timed_out:
            logger.info("Simulation wait ended before all aircraft completed.")
        else:
            logger.info("All simulations completed.")
