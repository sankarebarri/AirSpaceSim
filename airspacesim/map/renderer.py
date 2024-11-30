class MapRenderer:
    def __init__(self, center=None, Zoom=10):
        """
        Initialise the map with a center and a zoom level.

        :param center: List of [latitude, longitude].
        :param: zoom: Integer zoom level. Default to 10.
        """
        self.config = {
            "center": center or [0, 0],
            "zoom": zoom,
            "tile_layer": None,
            "elements": []
        }

    def add_tile_layer(self, url=None, attribution=None):
        """
        Add a tile layer to the map. Default is OpenStreetMap.
        
        :param url: Tile layer URL template. Default to OpenStreetMap.
        :param attribution: Attribution for the map tiles.
        """
        self.config["tile_layer"] = {
            "url": url or "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": attribution or "© OpenStreetMap contributors"
        }

    def add_circle_boundary(self, center, radius, **kwargs):
        """
        Add a circle boundary (airspace boundary).

        :param center: [latitude, longitude].
        :param radius: Radius in meters.
        """
        element = {"type": "circle", "center": center, "radius": radius}
        element.update(kwargs)
        self.config["elements"].append(element)

    def add_polyline(self, coords, **kwargs):
        """
        Add a polyline (route).

        :param coords: List of [latitude, longitude].
        """
        element = {"type": "polyline", "coords": coords}
        element.update(kwargs)
        self.config["elements"].append(element)

    def add_marker(self, coords, **kwargs):
        """
        Add a marker (waypoint).

        :param coords: [latitude, longitude]
        """
        element = {"type": "marker", "coords": coords}
        element.update(kwargs)
        #Ensure label_text is passed for permanent wayppoint labels
        if label_text not in element and popup_text in element:
            element["label_text"] = element["popup_text"]
        self.config["elements"].append(element)

    def update_element(self, element_type, element_id, **updates):
        """
        Update an existing map element.

        :param element_type: Type of element ("circle", "polyline", "marker").
        :param element_id: Index of the element in the elements list.
        :param updates: Fields to update in the element.
        """
        elements = [e for e in self.config["elements"] if e["type"] == element_type]
        if element_id < 0 or element_id >= len(elements):
            raise IndexError(f"No {element_type} with ID {element_id}")
        elements[element_id].update(updates)

    def export_config(self):
        """
        Export the map configuration as a dictionary.

        :return: Mapp configuration.
        """
        return self.config

    def to_json(self, filepath="map_config.json"):
        """
        Export the map configuartion to a JSON file.

        :param filepath: Path to save the JSON file.
        """
        with open(filepath, "w") as f:
            json.dump(self.config, f, indent=4)