import threading
import json
import time
from airspacesim.simulation.aircraft import Aircraft
from airspacesim.settings import settings
from airspacesim.utils.conversions import dms_to_decimal
from airspacesim.utils.logging_config import default_logger as logger

class AircraftManager:
    def __init__(self, routes):
        """
        Initialize an Aircraft Manager to handle multiple aircraft simulations.
        
        :param routes: Dictionary of predefined routes with waypoints in DMS format.
        """
        self.aircraft_list = []  # Stores active aircraft
        self.routes = routes  # Available routes
        self.threads = []  # List to track active simulation threads
        self.lock = threading.Lock()  # Thread safety

    def add_aircraft(self, id, route_name, callsign="Unknown", stop_flag=None, speed=None):
        """
        Adds a new aircraft and starts its simulation.
        """
        if route_name not in self.routes:
            logger.error("Route '%s' does not exist.", route_name)
            raise ValueError(f"Route '{route_name}' does not exist.")

        # Convert waypoints to decimal degrees.
        waypoints = []
        for wp in self.routes[route_name]:
            if "dec_coords" in wp:
                coords = wp["dec_coords"]
            else:
                try:
                    coords = [
                        dms_to_decimal(*wp["coords"]["lat"]),
                        dms_to_decimal(*wp["coords"]["lon"])
                    ]
                except Exception as e:
                    logger.exception("Error converting DMS to decimal for waypoint: %s", wp)
                    raise
            waypoints.append(coords)

        try:
            aircraft = Aircraft(
                id,
                route_name,
                waypoints,
                speed=speed if speed is not None else settings.DEFAULT_SPEED_KNOTS,
                callsign=callsign
            )
            self.aircraft_list.append(aircraft)
        except Exception as e:
            logger.exception("Error creating Aircraft instance for ID: %s", id)
            raise

        thread = threading.Thread(target=self.simulate_aircraft, args=(aircraft, stop_flag))
        thread.start()
        self.threads.append(thread)
        logger.info("Aircraft %s added on route %s with callsign %s.", id, route_name, callsign)

    def simulate_aircraft(self, aircraft, stop_flag):
        """
        Simulate the aircraft's movement based on its speed.
        """
        logger.info("🛫 Starting simulation for %s (%s)...", aircraft.id, aircraft.callsign)
        try:
            while aircraft.current_index < len(aircraft.waypoints) - 1:
                if stop_flag and stop_flag.is_set():
                    logger.info("⛔ Simulation for %s interrupted.", aircraft.id)
                    return
                aircraft.update_position(settings.SIMULATION_UPDATE_INTERVAL)
                self.save_aircraft_data()
                time.sleep(settings.SIMULATION_UPDATE_INTERVAL)
            # Mark aircraft as finished and record the finish time.
            aircraft.finished_time = time.time()
            logger.info("✅ %s has completed its route at %s.", aircraft.id, aircraft.finished_time)
        except Exception as e:
            logger.exception("Error during simulation for aircraft %s", aircraft.id)

    def save_aircraft_data(self):
        """
        Saves the current positions, callsigns, and speeds of all aircraft to JSON.
        Also logs the number and IDs of aircraft being saved.
        """
        with self.lock:
            data = {
                "aircraft_data": [
                    {
                        "id": ac.id,
                        "position": ac.position,
                        "callsign": ac.callsign,
                        "speed": ac.speed
                    }
                    for ac in self.aircraft_list
                ]
            }
            try:
                with open(settings.AIRCRAFT_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                ids = [ac["id"] for ac in data["aircraft_data"]]
                logger.debug("Saved aircraft data: %d aircraft in list. IDs: %s", len(ids), ids)
            except Exception as e:
                logger.exception("Failed to write aircraft data to file.")

    def monitor_new_aircraft(self, stop_flag):
        """
        Continuously checks `new_aircraft.json` for new aircraft and adds them dynamically.
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
                        elif "aircraft" in entry and isinstance(entry["aircraft"], list):
                            batch.extend(entry["aircraft"])
                        else:
                            logger.error("New aircraft entry missing 'route': %s", entry)

                    for ac in batch:
                        if "route" not in ac:
                            logger.error("New aircraft entry missing 'route': %s", ac)
                            continue
                        self.add_aircraft(
                            ac["id"],
                            ac["route"],
                            ac.get("callsign", "Unknown"),
                            stop_flag,
                            ac.get("speed", None)
                        )
                    # Clear the JSON file after processing.
                    with open(settings.NEW_AIRCRAFT_FILE, "w") as f:
                        json.dump({"aircraft": []}, f, indent=4)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning("Error reading new_aircraft.json: %s", e)
            except Exception as e:
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
            with self.lock:
                current_time = time.time()
                # Log status of finished aircraft.
                finished_aircraft = [
                    (ac.id, ac.finished_time, current_time - ac.finished_time)
                    for ac in self.aircraft_list if hasattr(ac, "finished_time")
                ]
                if finished_aircraft:
                    for ac_id, finish_time, elapsed in finished_aircraft:
                        logger.debug("Aircraft %s finished at %s, elapsed time: %.2f sec", ac_id, finish_time, elapsed)
                else:
                    logger.debug("No aircraft marked as finished in this cycle.")

                before_cleanup = len(self.aircraft_list)
                self.aircraft_list = [
                    ac for ac in self.aircraft_list
                    if not hasattr(ac, "finished_time") or (current_time - ac.finished_time) < 120
                ]
                after_cleanup = len(self.aircraft_list)
                cleaned_count = before_cleanup - after_cleanup
                if cleaned_count > 0:
                    logger.info("Cleaned up %d finished aircraft.", cleaned_count)
                    self.save_aircraft_data()
                else:
                    logger.debug("No aircraft cleaned up in this cycle.")
            time.sleep(10)
        logger.info("Cleanup thread terminating.")

    def delete_aircraft(self, aircraft_id):
        """
        Deletes an aircraft from the active list by its ID.
        """
        with self.lock:
            initial_count = len(self.aircraft_list)
            self.aircraft_list = [ac for ac in self.aircraft_list if ac.id != aircraft_id]
            if len(self.aircraft_list) < initial_count:
                logger.info("Aircraft %s deleted.", aircraft_id)
            else:
                logger.warning("Aircraft %s not found for deletion.", aircraft_id)

    def terminate_simulations(self):
        """
        Waits for all simulation threads to terminate.
        """
        for thread in self.threads:
            thread.join()
        logger.info("All simulation threads have terminated.")
