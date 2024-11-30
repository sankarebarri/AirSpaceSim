import json

class MapRenderer:
    def __init__(self, center=None, zoom=10):
        """
        Initialize the map with a center and zoom level.

        :param center: List of [latitude, longitude] for the map center. Default: [0, 0].
        :param zoom: Integer zoom level. Default: 10.
        """
        self.config = {
            "center": center or [0, 0],
            "zoom": zoom,
            "tile_layer": None,
            "elements": []
        }

    def add_element(self, element_type, **kwargs):
        """
        Generalized method to add elements to the map.
        :param element_type: Type of the element ('circle', 'polyline', 'marker').
        """
        element = {"type": element_type, **kwargs}
        self.config["elements"].append(element)

    def add_tile_layer(self, url=None, attribution=None):
        """
        Add a tile layer to the map. Default is OpenStreetMap.

        :param url: Tile layer URL template. Default: OpenStreetMap.
        :param attribution: Attribution for the map tiles.
        """
        self.config["tile_layer"] = {
            "url": url or "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": attribution or "© OpenStreetMap contributors"
        }

    def export_config(self):
        """
        Export the map configuration as a dictionary.

        :return: Map configuration.
        """
        return self.config

    def to_json(self, filepath="map_config.json"):
        """
        Export the map configuration to a JSON file.

        :param filepath: Path to save the JSON file.
        """
        with open(filepath, "w") as f:
            json.dump(self.config, f, indent=4)
