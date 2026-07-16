import os
from pathlib import Path


class Settings:
    """Global settings manager for AirSpaceSim with user-defined options."""

    def __init__(self, workspace_root=None):
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

        self._package_root = Path(__file__).resolve().parent
        self._package_data_dir = self._package_root / "data"

        # Default File Paths (Library seed data)
        self.DEFAULT_AIRSPACE_FILE = self._package_data_path("airspace_config.json")
        self.DEFAULT_AIRSPACE_DATA_FILE = self._package_data_path("airspace_data.json")
        self.DEFAULT_SCENARIO_AIRSPACE_FILE = self._package_data_path(
            "scenario_airspace.v1.json"
        )
        self.DEFAULT_SCENARIO_FILE = self._package_data_path("scenario.v0.1.json")
        self.DEFAULT_SCENARIO_AIRCRAFT_FILE = self._package_data_path(
            "scenario_aircraft.v1.json"
        )
        self.DEFAULT_INBOX_EVENTS_FILE = self._package_data_path(
            "inbox_events.v1.json"
        )
        self.DEFAULT_RENDER_PROFILE_FILE = self._package_data_path(
            "render_profile.v1.json"
        )
        self.DEFAULT_AIRCRAFT_FILE = self._package_data_path("aircraft_data.json")
        self.DEFAULT_AIRCRAFT_STATE_FILE = self._package_data_path(
            "aircraft_state.v1.json"
        )
        self.DEFAULT_TRAJECTORY_FILE = self._package_data_path("trajectory.v0.1.json")
        self.DEFAULT_NEW_AIRCRAFT_FILE = self._package_data_path(
            "aircraft_ingest.json"
        )

        self.refresh_paths(workspace_root=workspace_root)

    def refresh_paths(self, workspace_root=None):
        """Re-resolve workspace-aware paths after a cwd change or custom bootstrap."""
        self._workspace_root = Path(workspace_root or os.getcwd()).resolve()
        self._workspace_data_dir = self._workspace_root / "data"

        self.WORKSPACE_ROOT = str(self._workspace_root)
        self.WORKSPACE_DATA_DIR = str(self._workspace_data_dir)

        # User-defined overrides (if they exist)
        self.AIRSPACE_FILE = self.get_user_override(
            ["airspace_config.json", "gao_airspace.json", "gao_airspace_config.json"],
            self.DEFAULT_AIRSPACE_FILE,
        )
        self.AIRSPACE_DATA_FILE = self.get_user_override(
            "airspace_data.json", self.DEFAULT_AIRSPACE_DATA_FILE
        )
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
        self.RENDER_PROFILE_FILE = self.get_user_override(
            "render_profile.v1.json",
            self.DEFAULT_RENDER_PROFILE_FILE,
        )
        self.AIRCRAFT_FILE = self.get_workspace_runtime_path("aircraft_data.json")
        self.AIRCRAFT_STATE_FILE = self.get_workspace_runtime_path(
            "aircraft_state.v1.json"
        )
        self.TRAJECTORY_FILE = self.get_workspace_runtime_path("trajectory.v0.1.json")
        self.INBOX_EVENTS_FILE = self.get_workspace_runtime_path(
            "inbox_events.v1.json"
        )
        self.NEW_AIRCRAFT_FILE = self.get_workspace_runtime_path(
            ["aircraft_ingest.json", "new_aircraft.json"],
        )

    def _package_data_path(self, filename):
        return str(self._package_data_dir / filename)

    def _normalize_filenames(self, filename):
        return [filename] if isinstance(filename, str) else list(filename)

    def _workspace_candidates(self, filename):
        filenames = self._normalize_filenames(filename)
        candidates = []
        for name in filenames:
            candidates.extend(
                [
                    self._workspace_data_dir / name,
                    self._workspace_root / name,
                ]
            )
        return candidates

    def get_user_override(self, filename, default_path):
        """
        Check whether the user has provided a file override.
        Resolution order:
        1) cwd/data/<filename>
        2) cwd/<filename> (legacy)
        3) package default
        """
        for user_path in self._workspace_candidates(filename):
            if user_path.exists():
                return str(user_path)
        return str(default_path)

    def get_workspace_runtime_path(self, filename):
        """
        Resolve a writable workspace path.

        Runtime outputs should never default back into package data because
        installed packages are often read-only.
        """
        filenames = self._normalize_filenames(filename)
        for user_path in self._workspace_candidates(filenames):
            if user_path.exists():
                return str(user_path)
        return str(self._workspace_data_dir / filenames[0])


settings = Settings()
