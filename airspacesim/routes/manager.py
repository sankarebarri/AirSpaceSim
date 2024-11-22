class RouteManager:
    def __init__(self, name):
        """
        Initialize a route with a name.

        :param name: Name of the route.
        """
        self.name = name
        self.waypoints = [] # List of waypoints, each as [lat, lon, name]

    def add_waypoint(self, coords, name=None):
        """
        Add a waypoint to the route.

        :param coords: [latitude, longitude] of the waypoint.
        :param name: Optional name for the waypoint.
        """
        self.waypoints.append({"coords": coords, "name": name})

    def remove_waypoint(self, index):
        """
        Remove a waypoint by its index.

        :param index: Index of the waypoint to remove.
        """
        if 0 <= index < len(self.waypoints):
            del waypoints[index]
        else:
            raise IndexError("Invalid waypoint index.")

    def get_waypoints(self):
        """
        Get all waypoints in the route.

        :return: List of waypoints as dictionaries.
        """
        return self.waypoints

    def viusalise_on(self, map_renderer):
        """
        Visualize the route on a map.

        :param map_renderer: Instance of MapRenderer to render the route.
        """
        coords = [wp["coords"] for wp in self.waypoints]
        map_renderer.add_polyline(coords, color="blue", name=self.name)
        for wp in self.waypoints:
            map_renderer.add_marker(wp["coords"], popup_text=wp["name"])