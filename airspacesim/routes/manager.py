from airspacesim.utils.conversions import dms_to_decimal

class RouteManager:
    def __init__(self, name):
        """
        Initialise a route with a name

        :param name: Name of the route
        """
        self.name = name
        self.waypoints = [] # List of waypoints, each as [lat, lon, name]

    def add_waypoint(self, coords, name=None, distance=None, altitude=None):
        """
        Add a waypoint to the route

        :param coords: {"lat": (degrees, minutes, seconds, direction), "lon": (degrees, minutes, seconds, direction)}.
        :param name: Optional name for the waypoint.
        :param distance: Optional distance to the next waypoint.
        :param altitude: Optiona altitude for the waypoint
        """
        # Ensure coords is in the correct format
        if not isinstance(coords, dict) or "lat" not in coords or "lon" not in coords:
            raise ValueError(
                f"Invalid coordinates format: {coords}. Expected a dictionary with a 'lat' and 'lon' keys."
            )
        # Convert DMS coords to decimal coords. Needed by leaflet.js
        dec_coords = [
            dms_to_decimal(*coords["lat"]),
            dms_to_decimal(*coords["lon"])
        ]
        self.waypoints.append({
            "coords": coords,
            "dec_coords": dec_coords,
            "name": name,
            "distance": distance,
            "altitude": altitude
        })

    def remove_waypoint(self, index):
        """
        Remove a waypoint by its index.

        :param index: Index of the waypoint to remove.
        """
        if 0 <= index < len(self.waypoints):
            del waypoints["index"]
        else:
            raise IndexError("Invalid waypoint index.")

    def get_waypoints(self):
        """
        Get all waypoints in the route.

        :return: List of waypoints as dictionaries.
        """
        return self.waypoints

    def visualise_on(self, map_renderer):
        """
        Visualise the route on a map.__annotations__
        
        :param map_renderer: Instance of MapRenderer to render the route.
        """
        coords = [wp["dec_coords"] for wp in self.waypoints]
        map_renderer.add_polyline(coords, color="red", name=self.name)
        for wp in self.waypoints:
            popup_text = f"Waypoint {wp['name'] or 'Unnamed'}<br>"
            if wp.get("distance"):
                popup_text += f"Distance to next: {wp['distance']} NM <br>"
            if wp.get("altitude"):
                popup_text += f"Altitude: {wp['altitude']} ft"
            map_renderer.add_marker(wp["coords"], popup_text=wp["name"])