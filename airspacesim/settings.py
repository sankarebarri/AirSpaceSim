import os
from pathlib import Path


class Settings:
    """Engine settings: domain constants plus workspace-aware file paths.

    The file paths back the engine's optional JSON contract IO (scenario
    loading defaults, trajectory/state outputs, inbox events). Hosted
    applications typically disable file output entirely
    (`AircraftManager(enable_file_output=False)`) and pass configuration
    explicitly; these paths exist for headless/library workflows.
    """

    def __init__(self, workspace_root=None):
        # Constants
        self.EARTH_RADIUS_NM = 3440.065  # Nautical Miles
        self.NM_TO_METERS = 1852  # 1 NM in meters
        self.SIMULATION_UPDATE_INTERVAL = 1.0  # Seconds (simulation update time step)
        # NOTE: the process-wide SIMULATION_SPEED multiplier was removed in 0.2.0.
        # Time acceleration is now per-manager: AircraftManager(sim_rate=...) /
        # AircraftManager.set_simulation_speed().
        self.DEFAULT_SPEED_KNOTS = 400  # Default aircraft speed in knots
        # Speed guardrails (knots).
        self.REALISTIC_ENROUTE_SPEED_WARNING_KTS = 700.0
        self.MAX_ABSURD_SPEED_KTS = 1200.0
        # One of: "reject", "clamp", "off"
        self.SPEED_GUARDRAIL_MODE = "reject"
        # Default traffic-flow centre for the bundled fictional Nerava
        # training environment. Environment-specific: managers accept an
        # explicit airspace_center, and Simulation derives it from the
        # loaded airspace data.
        self.AIRSPACE_CENTER = (33.5, -41.0)

        self._package_root = Path(__file__).resolve().parent
        self._package_data_dir = self._package_root / "data"

        # Default File Paths (library seed data shipped in the wheel)
        self.DEFAULT_SCENARIO_AIRSPACE_FILE = self._package_data_path(
            "scenario_airspace.v1.json"
        )
        self.DEFAULT_SCENARIO_FILE = self._package_data_path("scenario.v0.1.json")
        self.DEFAULT_SCENARIO_AIRCRAFT_FILE = self._package_data_path(
            "scenario_aircraft.v1.json"
        )

        self.refresh_paths(workspace_root=workspace_root)

    def refresh_paths(self, workspace_root=None):
        """Re-resolve workspace-aware paths after a cwd change or custom bootstrap."""
        self._workspace_root = Path(workspace_root or os.getcwd()).resolve()
        self._workspace_data_dir = self._workspace_root / "data"

        self.WORKSPACE_ROOT = str(self._workspace_root)
        self.WORKSPACE_DATA_DIR = str(self._workspace_data_dir)

        # Scenario inputs: workspace overrides fall back to packaged seeds.
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
        # Runtime outputs/inputs always live in the writable workspace.
        self.AIRCRAFT_FILE = self.get_workspace_runtime_path("aircraft_data.json")
        self.AIRCRAFT_STATE_FILE = self.get_workspace_runtime_path(
            "aircraft_state.v1.json"
        )
        self.TRAJECTORY_FILE = self.get_workspace_runtime_path("trajectory.v0.1.json")
        self.INBOX_EVENTS_FILE = self.get_workspace_runtime_path(
            "inbox_events.v1.json"
        )
        self.NEW_AIRCRAFT_FILE = self.get_workspace_runtime_path(
            "aircraft_ingest.json"
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
