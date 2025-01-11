import os
import json

class Settings:
    """Global settings manager for AirSpaceSim with user-defined options."""
    def __init__(self):
        # Constants
        self.EARTH_RADIUS_NM = 3440.065  # Nautical Miles
        self.NM_TO_METERS = 1852  # 1 NM in meters
        self.SIMULATION_UPDATE_INTERVAL = 1.0  # Seconds
        self.DEFAULT_SPEED_KNOTS = 400  # Default aircraft speed in knots
        self.AIRSPACE_CENTER = (16.25, -0.03)  # Gao Airspace default center
        self.DEFAULT_ZOOM_LEVEL = 8

        # Default File Paths (Library)
        self.DEFAULT_AIRSPACE_FILE = os.path.join(os.path.dirname(__file__), "data", "gao_airspace.json")
        self.DEFAULT_AIRCRAFT_FILE = os.path.join(os.path.dirname(__file__), "data", "aircraft_data.json")
        self.DEFAULT_NEW_AIRCRAFT_FILE = os.path.join(os.path.dirname(__file__), "data", "new_aircraft.json")

        # User-defined overides (if they exist)
        self.AIRSPACE_FILE = self.get_user_override("gao_airspace.json", self.DEFAULT_AIRSPACE_FILE)
        self.AIRCRAFT_FILE = self.get_user_override("aircraft_data.json", self.DEFAULT_AIRCRAFT_FILE)
        self.NEW_AIRCRAFT_FILE = self.get_user_override("new_aircraft.json", self.DEFAULT_NEW_AIRCRAFT_FILE)


    def get_user_override(self, filename, default_path):
        """Check if the user has provided a file in the working directory"""
        user_path = os.path.join(os.getcwd(), filename)
        return user_path if os.path.exists(user_path) else default_path

    def set(self, key, value):
        """Allows modifying global settings dynamically."""
        if hasattr(self, key):
            setattr(self, key, value)

    def get(self, key):
        """Retrieve a setting value."""
        return getattr(self, key, None)

settings = Settings()