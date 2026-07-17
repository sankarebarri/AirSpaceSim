"""Core simulation domain: typed models, stable interfaces, and the façade."""

from airspacesim.core.clock import SimulationClock
from airspacesim.core.engine_events import EngineEvent
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
from airspacesim.core.separation import SeparationMonitor, SeparationStandard
from airspacesim.core.simulation import Simulation
from airspacesim.core.stepper import ManagerStepper

__all__ = [
    "AircraftDefinition",
    "EngineEvent",
    "ManagerStepper",
    "ScenarioBundle",
    "ScenarioProvider",
    "SeparationMonitor",
    "SeparationStandard",
    "Simulation",
    "SimulationClock",
    "SimulationStepper",
    "TrajectorySink",
    "TrajectoryTrack",
    "Waypoint",
]
