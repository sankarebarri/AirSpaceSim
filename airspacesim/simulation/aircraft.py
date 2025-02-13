#simulation/aircraft.py
from airspacesim.utils.conversions import haversine
from airspacesim.simulation.interpolation import interpolate_position
from airspacesim.settings import settings  # To access SIMULATION_SPEED

class Aircraft:
    def __init__(self, id, route, waypoints, speed=400, callsign=None):
        """
        Initialize the aircraft.

        :param id: Unique identifier for the aircraft.
        :param route: Route name associated with the aircraft.
        :param waypoints: List of waypoints in decimal degrees [(lat, lon), ...].
        :param speed: Speed of the aircraft in knots. Defaults to 400.
        :param callsign: Optional callsign for the aircraft.
        """
        self.id = id
        self.route = route
        self.waypoints = waypoints
        self.speed = speed
        self.callsign = callsign
        self.current_index = 0  # Current waypoint index.
        self.position = waypoints[0]  # Start at the first waypoint.
        self.segment_progress = 0  # Nautical miles travelled along the current segment.

    def update_position(self, time_step):
        """
        Update the aircraft's position based on its speed and elapsed time.
        This version processes only one update step per call, so that any change in the
        simulation speed is applied on the next tick to all aircraft.
        
        :param time_step: Time elapsed in seconds since the last update.
        """
        if self.current_index >= len(self.waypoints) - 1:
            return

        # Compute the effective time using the current simulation speed.
        effective_time = time_step * settings.SIMULATION_SPEED
        # Distance to travel during this update (nautical miles).
        travel_distance = (self.speed * effective_time) / 3600.0

        start = self.waypoints[self.current_index]
        end = self.waypoints[self.current_index + 1]
        segment_distance = haversine(start[0], start[1], end[0], end[1])
        remaining_distance = segment_distance - self.segment_progress

        if travel_distance < remaining_distance:
            # Advance within the current segment.
            self.segment_progress += travel_distance
            fraction = self.segment_progress / segment_distance
            self.position = interpolate_position(start, end, fraction)
        else:
            # Complete the current segment.
            self.current_index += 1
            self.position = end
            self.segment_progress = 0
