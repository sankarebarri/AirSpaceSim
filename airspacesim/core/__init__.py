"""Core simulation domain: typed models + stable interfaces."""

from airspacesim.core.interfaces import (
    ScenarioProvider,
    SimulationStepper,
    TrajectorySink,
)
from airspacesim.core.models import (
    AircraftDefinition,
    ScenarioBundle,
    TrajectoryTrack,
    Waypoint,
)
from airspacesim.core.stepper import ManagerStepper

__all__ = [
    "AircraftDefinition",
    "ManagerStepper",
    "ScenarioBundle",
    "ScenarioProvider",
    "SimulationStepper",
    "TrajectorySink",
    "TrajectoryTrack",
    "Waypoint",
]
