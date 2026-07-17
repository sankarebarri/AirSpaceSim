"""General separation standards and loss-of-separation monitoring.

Semantics (ported from the previously frontend-side monitor so behaviour is
preserved, per docs/repository-audit/03 §5):

- A pair is validly separated when EITHER the horizontal minimum OR the
  vertical minimum is satisfied; separation is never judged on horizontal
  distance alone.
- One continuous violation by the same pair counts as one loss-of-separation
  event from `separation_loss_started` until `separation_loss_ended` —
  never one event per tick. A pair that regains separation and later loses
  it again starts a new event.
- Aircraft that are not active (finished/removed) cannot be in violation;
  a violation involving an aircraft that becomes inactive ends.
- Vertical separation compares flight levels (FL × 100 ft), matching the
  displayed authoritative levels. Horizontal distance uses haversine.

Scenario-specific Practice success criteria do NOT belong here; this is the
general monitor (brief non-negotiable #7).
"""

from dataclasses import dataclass

from airspacesim.core.engine_events import (
    SEPARATION_LOSS_ENDED,
    SEPARATION_LOSS_STARTED,
    EngineEvent,
)
from airspacesim.utils.conversions import haversine


@dataclass(frozen=True)
class SeparationStandard:
    """Applicable separation minima for a simulation."""

    horizontal_nm: float = 10.0
    vertical_ft: float = 1000.0

    def is_separated(self, horizontal_nm, vertical_ft):
        return (
            horizontal_nm >= self.horizontal_nm or vertical_ft >= self.vertical_ft
        )

    def as_dict(self):
        return {"horizontal_nm": self.horizontal_nm, "vertical_ft": self.vertical_ft}


def pair_measurements(first, second):
    """Measure horizontal (NM) and vertical (ft) separation between two states.

    States are dicts with `position_dd` ([lat, lon]) and `flight_level` (int).
    """
    horizontal_nm = haversine(
        float(first["position_dd"][0]),
        float(first["position_dd"][1]),
        float(second["position_dd"][0]),
        float(second["position_dd"][1]),
    )
    vertical_ft = abs(int(first["flight_level"]) - int(second["flight_level"])) * 100.0
    return horizontal_nm, vertical_ft


class SeparationMonitor:
    """Track pairwise loss-of-separation state transitions across all aircraft."""

    def __init__(self, standard=None):
        self.standard = standard or SeparationStandard()
        self.loss_event_count = 0
        self._violating = {}

    def update(self, states, time_seconds):
        """Evaluate all active pairs; return started/ended EngineEvents."""
        events = []
        active = [
            state for state in states if state.get("status", "active") == "active"
        ]

        current = {}
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                first, second = active[i], active[j]
                horizontal_nm, vertical_ft = pair_measurements(first, second)
                if not self.standard.is_separated(horizontal_nm, vertical_ft):
                    key = tuple(sorted((first["id"], second["id"])))
                    current[key] = {
                        "horizontal_nm": horizontal_nm,
                        "vertical_ft": vertical_ft,
                    }

        for key, measurements in current.items():
            if key in self._violating:
                self._violating[key].update(measurements)
                continue
            self._violating[key] = {
                "started_at_seconds": time_seconds,
                **measurements,
            }
            self.loss_event_count += 1
            events.append(
                EngineEvent(
                    SEPARATION_LOSS_STARTED,
                    time_seconds,
                    {"pair": list(key), **measurements},
                )
            )

        for key in list(self._violating):
            if key not in current:
                violation = self._violating.pop(key)
                events.append(
                    EngineEvent(
                        SEPARATION_LOSS_ENDED,
                        time_seconds,
                        {
                            "pair": list(key),
                            "started_at_seconds": violation["started_at_seconds"],
                        },
                    )
                )
        return events

    def active_violations(self):
        """Currently violating pairs with their latest measurements."""
        return [
            {
                "pair": list(key),
                "horizontal_nm": violation["horizontal_nm"],
                "vertical_ft": violation["vertical_ft"],
                "started_at_seconds": violation["started_at_seconds"],
            }
            for key, violation in sorted(self._violating.items())
        ]

    def as_dict(self):
        return {
            "standard": self.standard.as_dict(),
            "active_violations": self.active_violations(),
            "loss_of_separation_count": self.loss_event_count,
        }
