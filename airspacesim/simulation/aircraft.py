#simulation/aircraft.py

# from math import radians, sin, cos, atan2, degrees, asin
# from airspacesim.utils.conversions import haversine
# from airspacesim.utils.calculate_bearing import calculate_bearing
# from airspacesim.settings import settings

# class Aircraft:
#     """
#     Class to simulate an aircraft moving along a predefined route.
#     """

#     def __init__(self, id, route, waypoints, speed=None, callsign=None):
#         """
#         Initialize the aircraft.

#         :param id: Unique identifier for the aircraft.
#         :param route: Route name associated with the aircraft.
#         :param waypoints: List of waypoints in decimal degrees [(lat, lon), ...].
#         :param speed: Speed of the aircraft in knots. Defaults to settings.DEFAULT_SPEED_KNOTS.
#         :param callsign: Optional callsign for the aircraft.
#         """
#         self.id = id
#         self.route = route
#         self.waypoints = waypoints
#         self.speed = speed or settings.DEFAULT_SPEED_KNOTS  # Default speed from settings
#         self.callsign = callsign
#         self.current_index = 0  # Current waypoint index
#         self.position = waypoints[0]  # Start at the first waypoint
#         self.bearing = self.calculate_next_bearing()

#     def calculate_next_bearing(self):
#         """
#         Calculate the bearing to the next waypoint using `calculate_bearing`.
#         """
#         if self.current_index >= len(self.waypoints) - 1:
#             return None  # No more waypoints to calculate

#         lat1, lon1 = self.position
#         lat2, lon2 = self.waypoints[self.current_index + 1]
#         return calculate_bearing(lat1, lon1, lat2, lon2)

#     def update_position(self, time_step):
#         """
#         Update the aircraft's position based on speed and bearing.

#         :param time_step: Time elapsed in seconds since the last update.
#         """
#         if self.current_index >= len(self.waypoints) - 1:
#             return  # No more waypoints to move towards

#         # Calculate the distance to travel in this time step
#         distance_to_travel = (self.speed * time_step) / 3600  # Convert knots to nautical miles
#         lat1, lon1 = map(radians, self.position)

#         # Recalculate the bearing dynamically
#         self.bearing = self.calculate_next_bearing()
#         if self.bearing is None:
#             return  # No movement if there's no next waypoint

#         # Calculate the new position using the bearing
#         bearing_rad = radians(self.bearing)
#         R = settings.EARTH_RADIUS_NM  # Earth's radius in nautical miles

#         lat2 = asin(sin(lat1) * cos(distance_to_travel / R) +
#                     cos(lat1) * sin(distance_to_travel / R) * cos(bearing_rad))
#         lon2 = lon1 + atan2(sin(bearing_rad) * sin(distance_to_travel / R) * cos(lat1),
#                             cos(distance_to_travel / R) - sin(lat1) * sin(lat2))

#         # Update the aircraft's position
#         self.position = [degrees(lat2), degrees(lon2)]

#         # Check if the waypoint is reached
#         self.check_waypoint_reached()

#     def check_waypoint_reached(self):
#         """
#         Check if the aircraft has reached or passed the current waypoint.
#         """
#         if self.current_index >= len(self.waypoints) - 1:
#             return  # No more waypoints to check

#         next_waypoint = self.waypoints[self.current_index + 1]
#         distance_to_next_waypoint = haversine(self.position[0], self.position[1],
#                                               next_waypoint[0], next_waypoint[1])

#         if distance_to_next_waypoint < 0.1:  # Threshold in nautical miles
#             self.current_index += 1
#             if self.current_index < len(self.waypoints):
#                 self.bearing = self.calculate_next_bearing()

from airspacesim.utils.conversions import haversine
from airspacesim.simulation.interpolation import interpolate_position

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
        self.segment_progress = 0  # Distance (in nautical miles) travelled along the current segment.

    def update_position(self, time_step):
        """
        Update the aircraft's position based on its speed and elapsed time.

        :param time_step: Time elapsed in seconds since the last update.
        """
        if self.current_index >= len(self.waypoints) - 1:
            return

        # Calculate travel distance for this time step (in nautical miles)
        travel_distance = (self.speed * time_step) / 3600.0

        # Process travel distance, accounting for potential overshoot of waypoints
        while travel_distance > 0 and self.current_index < len(self.waypoints) - 1:
            start = self.waypoints[self.current_index]
            end = self.waypoints[self.current_index + 1]

            segment_distance = haversine(start[0], start[1], end[0], end[1])
            remaining_distance = segment_distance - self.segment_progress

            if travel_distance < remaining_distance:
                self.segment_progress += travel_distance
                fraction = self.segment_progress / segment_distance
                self.position = interpolate_position(start, end, fraction)
                travel_distance = 0
            else:
                self.current_index += 1
                self.position = end
                travel_distance -= remaining_distance
                self.segment_progress = 0
                if self.current_index >= len(self.waypoints) - 1:
                    break
