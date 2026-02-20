import os

class Settings:
    """Global settings manager for AirSpaceSim with user-defined options."""
    def __init__(self):
        # Constants
        self.EARTH_RADIUS_NM = 3440.065  # Nautical Miles
        self.NM_TO_METERS = 1852  # 1 NM in meters
        self.SIMULATION_UPDATE_INTERVAL = 1.0  # Seconds (simulation update time step)
        self.SIMULATION_SPEED = 1.0  # Simulation speed multiplier (1.0 = normal speed, 2.0 = twice as fast, etc.)
        self.DEFAULT_SPEED_KNOTS = 400  # Default aircraft speed in knots
        # Speed guardrails (knots).
        self.REALISTIC_ENROUTE_SPEED_WARNING_KTS = 700.0
        self.MAX_ABSURD_SPEED_KTS = 1200.0
        # One of: "reject", "clamp", "off"
        self.SPEED_GUARDRAIL_MODE = "reject"
        self.AIRSPACE_CENTER = (16.25, -0.03)  # Default map center
        self.DEFAULT_ZOOM_LEVEL = 8

        # Default File Paths (Library)
        self.DEFAULT_AIRSPACE_FILE = os.path.join(os.path.dirname(__file__), "data", "airspace_config.json")
        self.DEFAULT_AIRSPACE_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "airspace_data.json")
        self.DEFAULT_SCENARIO_AIRSPACE_FILE = os.path.join(
            os.path.dirname(__file__),
            "data",
            "scenario_airspace.v1.json",
        )
        self.DEFAULT_SCENARIO_FILE = os.path.join(
            os.path.dirname(__file__),
            "data",
            "scenario.v0.1.json",
        )
        self.DEFAULT_SCENARIO_AIRCRAFT_FILE = os.path.join(
            os.path.dirname(__file__),
            "data",
            "scenario_aircraft.v1.json",
        )
        self.DEFAULT_INBOX_EVENTS_FILE = os.path.join(
            os.path.dirname(__file__),
            "data",
            "inbox_events.v1.json",
        )
        self.DEFAULT_RENDER_PROFILE_FILE = os.path.join(
            os.path.dirname(__file__),
            "data",
            "render_profile.v1.json",
        )
        self.DEFAULT_AIRCRAFT_FILE = os.path.join(os.path.dirname(__file__), "data", "aircraft_data.json")
        self.DEFAULT_AIRCRAFT_STATE_FILE = os.path.join(
            os.path.dirname(__file__),
            "data",
            "aircraft_state.v1.json",
        )
        self.DEFAULT_TRAJECTORY_FILE = os.path.join(
            os.path.dirname(__file__),
            "data",
            "trajectory.v0.1.json",
        )
        self.DEFAULT_NEW_AIRCRAFT_FILE = os.path.join(os.path.dirname(__file__), "data", "aircraft_ingest.json")

        # User-defined overrides (if they exist)
        self.AIRSPACE_FILE = self.get_user_override(
            ["airspace_config.json", "gao_airspace.json", "gao_airspace_config.json"],
            self.DEFAULT_AIRSPACE_FILE,
        )
        self.AIRSPACE_DATA_FILE = self.get_user_override("airspace_data.json", self.DEFAULT_AIRSPACE_DATA_FILE)
        self.SCENARIO_AIRSPACE_FILE = self.get_user_override(
            "scenario_airspace.v1.json",
            self.DEFAULT_SCENARIO_AIRSPACE_FILE,
        )
        self.SCENARIO_FILE = self.get_user_override(
            "scenario.v0.1.json",
            self.DEFAULT_SCENARIO_FILE,
        )
        self.SCENARIO_AIRCRAFT_FILE = self.get_user_override(
            "scenario_aircraft.v1.json",
            self.DEFAULT_SCENARIO_AIRCRAFT_FILE,
        )
        self.INBOX_EVENTS_FILE = self.get_user_override(
            "inbox_events.v1.json",
            self.DEFAULT_INBOX_EVENTS_FILE,
        )
        self.RENDER_PROFILE_FILE = self.get_user_override(
            "render_profile.v1.json",
            self.DEFAULT_RENDER_PROFILE_FILE,
        )
        self.AIRCRAFT_FILE = self.get_user_override("aircraft_data.json", self.DEFAULT_AIRCRAFT_FILE)
        self.AIRCRAFT_STATE_FILE = self.get_user_override(
            "aircraft_state.v1.json",
            self.DEFAULT_AIRCRAFT_STATE_FILE,
        )
        self.TRAJECTORY_FILE = self.get_user_override(
            "trajectory.v0.1.json",
            self.DEFAULT_TRAJECTORY_FILE,
        )
        self.NEW_AIRCRAFT_FILE = self.get_user_override(
            ["aircraft_ingest.json", "new_aircraft.json"],
            self.DEFAULT_NEW_AIRCRAFT_FILE,
        )

    def get_user_override(self, filename, default_path):
        """
        Check whether the user has provided a file override.
        Resolution order:
        1) cwd/data/<filename>
        2) cwd/<filename> (legacy)
        3) package default
        """
        filenames = [filename] if isinstance(filename, str) else list(filename)
        cwd = os.getcwd()
        candidates = []
        for name in filenames:
            candidates.extend([
                os.path.join(cwd, "data", name),
                os.path.join(cwd, name),
            ])
        for user_path in candidates:
            if os.path.exists(user_path):
                return user_path
        return default_path

settings = Settings()
