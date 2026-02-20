"""Stable core interfaces for scenario input, stepping, and trajectory output."""

from typing import Protocol

from airspacesim.core.models import ScenarioBundle, TrajectoryTrack


class ScenarioProvider(Protocol):
    def load(self) -> ScenarioBundle:
        """Load and normalize scenario input to core models."""


class SimulationStepper(Protocol):
    def step(self, time_step_seconds: float) -> list[TrajectoryTrack]:
        """Advance simulation and return current trajectory tracks."""


class TrajectorySink(Protocol):
    def publish(self, tracks: list[TrajectoryTrack], generated_utc: str) -> None:
        """Publish trajectory tracks to output contract(s)."""
