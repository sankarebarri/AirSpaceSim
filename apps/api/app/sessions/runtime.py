"""In-memory runtime session orchestration for simulation runs."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any

from airspacesim.core.models import TrajectoryTrack
from airspacesim.simulation.events import apply_events_idempotent
from airspacesim.simulation.scenario_runner import initialize_manager_from_scenarios


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SimulationRuntimeSession:
    """Manage one in-memory simulation session for a persisted run."""

    def __init__(
        self,
        *,
        run_id: str,
        scenario_airspace: dict[str, Any],
        scenario_aircraft: dict[str, Any],
        sim_rate: float,
        update_interval_seconds: float = 0.25,
        state_publisher=None,
    ) -> None:
        self.run_id = run_id
        self.sim_rate = float(sim_rate)
        self.update_interval_seconds = max(float(update_interval_seconds), 0.05)
        self.runtime_status = "draft"
        self.last_updated_utc = _utc_now_iso()
        self.last_error: str | None = None
        self._state_publisher = state_publisher

        self._state_lock = threading.Lock()
        self._tick_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self.manager = initialize_manager_from_scenarios(
            scenario_airspace,
            scenario_aircraft,
            execution_mode="batched",
        )
        # Hosted runtime sessions should not write shared JSON files.
        self.manager.save_aircraft_data = lambda: None

    def start(self) -> None:
        with self._state_lock:
            if self.runtime_status not in {"draft", "paused"}:
                raise ValueError(
                    f"Cannot start runtime session in state {self.runtime_status}."
                )
            self.runtime_status = "running"
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(
                    target=self._run_loop,
                    name=f"airspacesim-run-{self.run_id}",
                    daemon=True,
                )
                self._thread.start()
            self.last_updated_utc = _utc_now_iso()
        self._emit_state("started")

    def pause(self) -> None:
        with self._state_lock:
            if self.runtime_status != "running":
                raise ValueError(
                    f"Cannot pause runtime session in state {self.runtime_status}."
                )
            self.runtime_status = "paused"
            self.last_updated_utc = _utc_now_iso()
        self._emit_state("paused")

    def resume(self) -> None:
        with self._state_lock:
            if self.runtime_status != "paused":
                raise ValueError(
                    f"Cannot resume runtime session in state {self.runtime_status}."
                )
            self.runtime_status = "running"
            self.last_updated_utc = _utc_now_iso()
        self._emit_state("resumed")

    def stop(self) -> None:
        with self._state_lock:
            if self.runtime_status == "stopped":
                return
            self.runtime_status = "stopped"
            self.last_updated_utc = _utc_now_iso()
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self.manager.request_shutdown()
        self.manager.terminate_simulations(timeout_seconds=1.0)
        self._emit_state("stopped")

    def apply_command(
        self,
        *,
        command_id: str,
        command_type: str,
        payload: dict[str, Any],
    ) -> dict[str, list[Any]]:
        """Apply a command directly to the live manager without file IO."""

        with self._state_lock:
            runtime_status = self.runtime_status

        if runtime_status in {"stopped", "completed", "error"}:
            return {
                "applied": [],
                "skipped": [],
                "rejected": [
                    (
                        command_id,
                        f"runtime session is {runtime_status}",
                    )
                ],
            }

        if command_type == "SET_SIMULATION_SPEED":
            sim_rate = payload.get("sim_rate")
            if not isinstance(sim_rate, (int, float)) or sim_rate <= 0:
                return {
                    "applied": [],
                    "skipped": [],
                    "rejected": [(command_id, "invalid sim_rate")],
                }
            with self._state_lock:
                self.sim_rate = float(sim_rate)
                self.last_updated_utc = _utc_now_iso()
            self._emit_state("command")
            return {"applied": [command_id], "skipped": [], "rejected": []}

        normalized_event = {
            "event_id": command_id,
            "type": command_type,
            "payload": self._normalize_command_payload(command_type, payload),
        }
        with self._tick_lock:
            original_save = self.manager.save_aircraft_data
            self.manager.save_aircraft_data = lambda: None
            try:
                result = apply_events_idempotent(self.manager, [normalized_event])
            finally:
                self.manager.save_aircraft_data = original_save
        self.last_updated_utc = _utc_now_iso()
        self._emit_state("command")
        return result

    def state_snapshot(self) -> dict[str, Any]:
        """Return the current live runtime state for API serialization."""

        with self._state_lock:
            runtime_status = self.runtime_status
            sim_rate = self.sim_rate
            updated_utc = self.last_updated_utc
            last_error = self.last_error

        with self.manager.lock:
            aircraft_list = list(self.manager.aircraft_list)

        aircraft_items = []
        active_count = 0
        finished_count = 0
        for aircraft in aircraft_list:
            status = "finished" if hasattr(aircraft, "finished_time") else "active"
            if status == "active":
                active_count += 1
            else:
                finished_count += 1
            raw_flight_level = getattr(aircraft, "flight_level", None)
            flight_level = (
                int(round(float(raw_flight_level)))
                if raw_flight_level is not None
                else int(round(float(aircraft.altitude_ft) / 100.0))
            )
            aircraft_items.append(
                {
                    "id": aircraft.id,
                    "callsign": aircraft.callsign,
                    "aircraft_type": getattr(aircraft, "aircraft_type", "UNKNOWN"),
                    "route_id": aircraft.route,
                    "position_dd": [float(aircraft.position[0]), float(aircraft.position[1])],
                    "speed_kt": float(aircraft.speed),
                    "flight_level": flight_level,
                    "target_flight_level": getattr(
                        aircraft,
                        "target_flight_level",
                        flight_level,
                    ),
                    "altitude_ft": float(aircraft.altitude_ft),
                    "vertical_rate_fpm": float(aircraft.vertical_rate_fpm),
                    "heading_deg": float(getattr(aircraft, "heading_deg", 0.0)),
                    "assigned_heading_deg": getattr(
                        aircraft,
                        "assigned_heading_deg",
                        None,
                    ),
                    "assigned_radial_deg": getattr(
                        aircraft,
                        "assigned_radial_deg",
                        None,
                    ),
                    "radial_deviation_deg": getattr(
                        aircraft,
                        "radial_deviation_deg",
                        None,
                    ),
                    "radial_cross_track_nm": getattr(
                        aircraft,
                        "radial_cross_track_nm",
                        None,
                    ),
                    "lateral_mode": getattr(aircraft, "lateral_mode", "route"),
                    "direct_to_fix_id": getattr(aircraft, "direct_to_fix_id", None),
                    "hold_fix_id": getattr(aircraft, "hold_fix_id", None),
                    "traffic_flow": getattr(aircraft, "traffic_flow", "unknown"),
                    "status": status,
                    "updated_utc": updated_utc,
                }
            )

        return {
            "runtime_status": runtime_status,
            "sim_rate": sim_rate,
            "updated_utc": updated_utc,
            "last_error": last_error,
            "aircraft": aircraft_items,
            "metrics": {
                "aircraft_count": len(aircraft_items),
                "active_aircraft_count": active_count,
                "finished_aircraft_count": finished_count,
            },
        }

    def trajectory_snapshot(self) -> dict[str, Any]:
        """Return trajectory-style live track records for the API."""

        snapshot = self.state_snapshot()
        tracks = [
            TrajectoryTrack(
                id=item["id"],
                callsign=item["callsign"],
                route_id=item["route_id"],
                position_dd=(item["position_dd"][0], item["position_dd"][1]),
                speed_kt=item["speed_kt"],
                flight_level=item["flight_level"],
                altitude_ft=item["altitude_ft"],
                vertical_rate_fpm=item["vertical_rate_fpm"],
                status=item["status"],
                updated_utc=item["updated_utc"],
            ).as_contract_dict()
            for item in snapshot["aircraft"]
        ]
        return {
            "runtime_status": snapshot["runtime_status"],
            "updated_utc": snapshot["updated_utc"],
            "tracks": tracks,
        }

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._state_lock:
                runtime_status = self.runtime_status
                sim_rate = self.sim_rate

            if runtime_status != "running":
                time.sleep(0.05)
                continue

            try:
                self._step_all_aircraft(self.update_interval_seconds, sim_rate)
                self.last_updated_utc = _utc_now_iso()
                self._emit_state("tick")
                if self._all_aircraft_finished():
                    with self._state_lock:
                        if self.runtime_status == "running":
                            self.runtime_status = "completed"
                    self._emit_state("completed")
                    break
            except Exception as exc:
                with self._state_lock:
                    self.last_error = str(exc)
                    self.runtime_status = "error"
                self._emit_state("error")
                break
            time.sleep(self.update_interval_seconds)

    def _step_all_aircraft(self, interval_seconds: float, sim_rate: float) -> None:
        with self._tick_lock, self.manager.lock:
            aircraft_list = list(self.manager.aircraft_list)
            for aircraft in aircraft_list:
                if aircraft.current_index < len(aircraft.waypoints) - 1:
                    aircraft.update_position(interval_seconds * sim_rate)
                    if aircraft.current_index >= len(aircraft.waypoints) - 1 and not hasattr(
                        aircraft,
                        "finished_time",
                    ):
                        aircraft.finished_time = time.time()

    def _all_aircraft_finished(self) -> bool:
        with self.manager.lock:
            return all(
                aircraft.current_index >= len(aircraft.waypoints) - 1
                for aircraft in self.manager.aircraft_list
            )

    def _normalize_command_payload(
        self, command_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        normalized = dict(payload)
        if command_type == "ADD_AIRCRAFT" and "route_id" not in normalized:
            route_value = normalized.get("route") or normalized.get("route_name")
            if route_value is not None:
                normalized["route_id"] = route_value
        if command_type == "SET_SPEED" and "speed_kt" not in normalized:
            speed_value = normalized.get("speed")
            if speed_value is not None:
                normalized["speed_kt"] = speed_value
        return normalized

    def _emit_state(self, checkpoint_type: str) -> None:
        if self._state_publisher is not None:
            self._state_publisher(
                self.run_id,
                self.state_snapshot(),
                checkpoint_type,
            )
