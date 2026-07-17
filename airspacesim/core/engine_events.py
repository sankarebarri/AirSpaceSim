"""Typed events emitted by the core simulation."""

from dataclasses import dataclass, field


AIRCRAFT_ENTERED = "aircraft_entered"
AIRCRAFT_EXITED = "aircraft_exited"
SEPARATION_LOSS_STARTED = "separation_loss_started"
SEPARATION_LOSS_ENDED = "separation_loss_ended"
COMMAND_APPLIED = "command_applied"
SIMULATION_COMPLETED = "simulation_completed"


@dataclass(frozen=True)
class EngineEvent:
    """One meaningful simulation occurrence, stamped with simulated time."""

    type: str
    time_seconds: float
    payload: dict = field(default_factory=dict)

    def as_dict(self):
        return {
            "type": self.type,
            "time_seconds": self.time_seconds,
            "payload": dict(self.payload),
        }
