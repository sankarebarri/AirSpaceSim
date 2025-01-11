#simulation/engine.py
from math import radians, sin, cos, atan2, degrees, asin
from airspacesim.utils.conversions import haversine
from airspacesim.utils.calculate_bearing import calculate_bearing
from airspacesim.settings import settings

class Aircraft:
    def __init__(self, route, speed=None):
        """
        Initialize the aircraft.

        :param route: List of waypoints in decimal degrees [(lat, lon), ...].
        :param speed: Speed of the aircraft in knots. Default is 400 knots.
        """
        self.route = route
        self.speed = speed or settings.DEFAULT_SPEED_KNOTS  # knots
        self.position = route[0]  # Start at the first waypoint
        self.current_waypoint_index = 1  # Start moving towards the second waypoint
        self.bearing = self.calculate_next_bearing()

    def calculate_next_bearing(self):
        """
        Calculate the bearing to the next waypoint using `calculate_bearing`.
        """
        if self.current_waypoint_index >= len(self.route):
            return None  # No more waypoints to calculate
        lat1, lon1 = self.position
        lat2, lon2 = self.route[self.current_waypoint_index]
        return calculate_bearing(lat1, lon1, lat2, lon2)

    def update_position(self, time_step):
        """
        Update the aircraft's position based on speed and bearing.

        :param time_step: Time elapsed in seconds since the last update.
        """
        if self.current_waypoint_index >= len(self.route):
            return  # No more waypoints to move towards

        # Calculate the distance to travel in this time step
        distance_to_travel = (self.speed * time_step) / 3600  # Convert knots to nautical miles
        lat1, lon1 = map(radians, self.position)

        # Recalculate the bearing dynamically
        self.bearing = self.calculate_next_bearing()

        # Calculate the new position using the bearing
        bearing_rad = radians(self.bearing)
        R = settings.EARTH_RADIUS_NM  # Earth's radius in nautical miles
        lat2 = asin(sin(lat1) * cos(distance_to_travel / R) +
                    cos(lat1) * sin(distance_to_travel / R) * cos(bearing_rad))
        lon2 = lon1 + atan2(sin(bearing_rad) * sin(distance_to_travel / R) * cos(lat1),
                            cos(distance_to_travel / R) - sin(lat1) * sin(lat2))

        # Update the aircraft's position
        self.position = [degrees(lat2), degrees(lon2)]

        # Check if the waypoint is reached
        self.check_waypoint_reached()

    def check_waypoint_reached(self):
        """
        Check if the aircraft has reached or passed the current waypoint.
        """
        if self.current_waypoint_index >= len(self.route):
            return  # No more waypoints to check
        next_waypoint = self.route[self.current_waypoint_index]
        distance_to_next_waypoint = haversine(self.position[0], self.position[1],
                                              next_waypoint[0], next_waypoint[1])

        if distance_to_next_waypoint < 0.1:  # Threshold in nautical miles
            self.current_waypoint_index += 1
            if self.current_waypoint_index < len(self.route):
                self.bearing = self.calculate_next_bearing()
