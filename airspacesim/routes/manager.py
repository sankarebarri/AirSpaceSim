# routes/manager.py
from airspacesim.utils.conversions import dms_to_decimal


class RouteManager:
    def __init__(self, name):
        """
        Initialize a route with a name.

        :param name: Name of the route.
        """
        self.name = name
        self.waypoints = []

    def add_waypoint(self, coords, name=None, distance=None, altitude=None):
        """
        Add a waypoint to the route.

        :param coords: {"lat": (degrees, minutes, seconds, direction), "lon": (degrees, minutes, seconds, direction)}.
        :param name: Optional name for the waypoint.
        :param distance: Optional distance to the next waypoint.
        :param altitude: Optional altitude for the waypoint.
        """
        if not isinstance(coords, dict) or "lat" not in coords or "lon" not in coords:
            raise ValueError(
                "Invalid coordinates format. Expected dict with 'lat' and 'lon'."
            )
        dec_coords = [dms_to_decimal(*coords["lat"]), dms_to_decimal(*coords["lon"])]
        self.waypoints.append(
            {
                "coords": coords,
                "dec_coords": dec_coords,
                "name": name,
                "distance": distance,
                "altitude": altitude,
            }
        )

    def get_waypoints(self):
        """
        Get all waypoints in the route.

        :return: List of waypoints as dictionaries.
        """
        return self.waypoints
