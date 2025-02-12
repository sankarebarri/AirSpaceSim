import threading
import json
import time
from airspacesim.simulation.aircraft import Aircraft
from airspacesim.settings import settings
from airspacesim.utils.conversions import dms_to_decimal

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

    def add_aircraft(self, id, route_name, callsign="Unknown", stop_flag=None):
        """
        Adds a new aircraft and starts its simulation.

        :param id: Unique aircraft identifier.
        :param route_name: The name of the predefined route.
        :param callsign: Optional callsign for display.
        :param stop_flag: Threading event to stop simulation gracefully.
        """
        if route_name not in self.routes:
            raise ValueError(f"Route '{route_name}' does not exist.")

        # Convert waypoints from DMS to Decimal
        waypoints = [
            [dms_to_decimal(*wp["coords"]["lat"]), dms_to_decimal(*wp["coords"]["lon"])]
            for wp in self.routes[route_name]
        ]

        # Create the Aircraft instance
        aircraft = Aircraft(id, route_name, waypoints, callsign=callsign)
        self.aircraft_list.append(aircraft)

        # Start the simulation in a new thread
        thread = threading.Thread(target=self.simulate_aircraft, args=(aircraft, stop_flag))
        thread.start()
        self.threads.append(thread)

    def simulate_aircraft(self, aircraft, stop_flag):
        total_steps = 100  # Number of steps between waypoints
        step_fraction = 1 / total_steps
        cumulative_fraction = 0

        print(f"🛫 Starting simulation for {aircraft.id} ({aircraft.callsign})...")

        while aircraft.current_index < len(aircraft.waypoints) - 1:
            if stop_flag.is_set():  # Check if the stop flag is set
                print(f"⛔ Simulation for {aircraft.id} interrupted.")
                return

            cumulative_fraction += step_fraction
            if not aircraft.move(cumulative_fraction):
                cumulative_fraction = 0

            self.save_aircraft_data()
            time.sleep(settings.SIMULATION_UPDATE_INTERVAL)

        print(f"✅ {aircraft.id} has completed its route.")

    def save_aircraft_data(self):
        """
        Saves the current positions of all aircraft to JSON.
        """
        with self.lock:
            data = {
                "aircraft_data": [
                    {"id": ac.id, "position": ac.position, "callsign": ac.callsign}
                    for ac in self.aircraft_list
                ]
            }
            with open(settings.AIRCRAFT_FILE, "w") as f:
                json.dump(data, f, indent=4)

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
                        self.add_aircraft(ac["id"], ac["route"], ac["callsign"], stop_flag)

                    # Clear new aircraft data after processing
                    with open(settings.NEW_AIRCRAFT_FILE, "w") as f:
                        json.dump({"aircraft": []}, f, indent=4)

            except (json.JSONDecodeError, FileNotFoundError):
                pass

            time.sleep(2)  # Check for new aircraft every 2 seconds

    def terminate_simulations(self):
        """
        Waits for all threads to terminate.
        """
        for thread in self.threads:
            thread.join()
