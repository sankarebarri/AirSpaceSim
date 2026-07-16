"""Public AirSpaceSim engine API.

The hosted API and React app live outside this package. Keep top-level exports
limited to reusable simulation engine primitives.
"""

from airspacesim.core import (
    AircraftDefinition,
    ManagerStepper,
    ScenarioBundle,
    ScenarioProvider,
    SimulationStepper,
    TrajectorySink,
    TrajectoryTrack,
    Waypoint,
)
from airspacesim.io import (
    ValidationError,
    build_envelope,
    export_trajectory_json_to_csv,
    export_trajectory_payload_to_csv,
    serialize_trajectory_payload_to_csv,
)
from airspacesim.simulation.aircraft import Aircraft
from airspacesim.simulation.aircraft_manager import AircraftManager
from airspacesim.simulation.events import apply_events_idempotent
from airspacesim.simulation.performance_database import (
    get_aircraft_performance_profile,
    hold_speed_kt,
    max_flight_level,
    speed_limits_kt,
    turn_rate_deg_per_sec,
)
from airspacesim.simulation.scenario_runner import (
    initialize_manager_from_scenarios,
    load_scenario_bundle,
    load_scenarios,
)

__all__ = [
    "Aircraft",
    "AircraftDefinition",
    "AircraftManager",
    "ManagerStepper",
    "ScenarioBundle",
    "ScenarioProvider",
    "SimulationStepper",
    "TrajectorySink",
    "TrajectoryTrack",
    "ValidationError",
    "Waypoint",
    "apply_events_idempotent",
    "build_envelope",
    "export_trajectory_json_to_csv",
    "export_trajectory_payload_to_csv",
    "get_aircraft_performance_profile",
    "hold_speed_kt",
    "initialize_manager_from_scenarios",
    "load_scenario_bundle",
    "load_scenarios",
    "max_flight_level",
    "serialize_trajectory_payload_to_csv",
    "speed_limits_kt",
    "turn_rate_deg_per_sec",
]
