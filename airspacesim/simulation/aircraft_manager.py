# simulation/aircraft_manager.py
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
        self.threads = []  # List to track active threads
        self.lock = threading.Lock()  # Thread safety

    def add_aircraft(self, id, route_name, callsign="Unknown", stop_flag=None, speed=None):
        """
        Adds a new aircraft and starts its simulation.
        """
        if route_name not in self.routes:
            logger.error("Route '%s' does not exist.", route_name)
            raise ValueError(f"Route '{route_name}' does not exist.")

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
                if stop_flag.is_set():
                    logger.info("⛔ Simulation for %s interrupted.", aircraft.id)
                    return
                aircraft.update_position(settings.SIMULATION_UPDATE_INTERVAL)
                self.save_aircraft_data()
                time.sleep(settings.SIMULATION_UPDATE_INTERVAL)
            logger.info("✅ %s has completed its route.", aircraft.id)
        except Exception as e:
            logger.exception("Error during simulation for aircraft %s", aircraft.id)

    def save_aircraft_data(self):
        """
        Saves the current positions, callsigns, and speeds of all aircraft to JSON.
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
            except Exception as e:
                logger.exception("Failed to write aircraft data to file.")

    def monitor_new_aircraft(self, stop_flag):
        """
        Continuously checks `new_aircraft.json` for new aircraft and adds them dynamically.
        """
        while not stop_flag.is_set():
            try:
                with open(settings.NEW_AIRCRAFT_FILE, "r") as f:
                    new_data = json.load(f)

                if new_data.get("aircraft"):
                    for ac in new_data["aircraft"]:
                        if "route" not in ac:
                            logger.error("New aircraft entry missing 'route': %s", ac)
                            continue  # Skip entries without a route
                        self.add_aircraft(
                            ac["id"],
                            ac["route"],
                            ac.get("callsign", "Unknown"),
                            stop_flag,
                            ac.get("speed", None)
                        )
                    with open(settings.NEW_AIRCRAFT_FILE, "w") as f:
                        json.dump({"aircraft": []}, f, indent=4)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning("Error reading new_aircraft.json: %s", e)
            except Exception as e:
                logger.exception("Unexpected error in monitor_new_aircraft.")
            time.sleep(2)


    def terminate_simulations(self):
        """
        Waits for all threads to terminate.
        """
        for thread in self.threads:
            thread.join()
        logger.info("All simulation threads have terminated.")
