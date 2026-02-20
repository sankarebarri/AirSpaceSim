# map/marker_manager.py
class DynamicMarkerManager:
    def __init__(self):
        """
        Initialize a manager for dynamic markers.
        """
        self.markers = {}

    def add_marker(self, marker_id, call_sign, coords, heading=0, speed=0):
        """
        Add a new marker to the manager.

        :param marker_id: Unique identifier for the marker (aircraft ID).
        :param callsign: Aircraft callsign.
        :param coords: [latitude, longitude].
        :param heading: Aircraft heading in degrees.
        :param speed: Aircraft speed in knots.
        """
        if marker_id in self.markers:
            raise ValueError(f"Marker with ID '{marker_id}' already exists.")
        self.markers[marker_id] = {
            "call_sign": call_sign,
            "coords": coords,
            "heading": heading,
            "speed": speed,
        }

    def update_marker(self, marker_id, new_coords, new_heading=None, new_speed=None):
        """
        Update an existing marker's position or properties.

        :param marker_id: Unique identifier for the marker.
        :param new_coords: New [latitude, longitude].
        :param new_heading: Optional updated heading in degrees.
        :param new_speed: Optional updated speed in knots.
        """
        if marker_id not in self.markers:
            raise ValueError(f"Marker with ID '{marker_id}' does not exist.")
        marker = self.markers[marker_id]
        marker["coords"] = new_coords
        if new_heading is not None:
            marker["heading"] = new_heading
        if new_speed is not None:
            marker["speed"] = new_speed

    def remove_marker(self, marker_id):
        """
        Remove a marker from the manager.

        :param marker_id: Unique identifier for the marker.
        """
        if marker_id in self.markers:
            del self.markers[marker_id]

    def get_markers(self):
        """
        Get all managed markers.

        :return: List of marker configurations.
        """
        return [
            {"id": marker_id, **marker_data}
            for marker_id, marker_data in self.markers.items()
        ]

    def to_json(self):
        """
        Export all managed markers as a JSON serializable structure.
        :return: JSON-compatible dictionary.
        """
        return {"Aircraft": self.get_markers()}
