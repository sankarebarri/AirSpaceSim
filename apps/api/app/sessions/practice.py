"""Server-side Practice outcome tracking.

Port of the scenario-specific evaluation previously computed only in the
browser (apps/web/src/lib/practiceOutcome.ts), so outcomes can be persisted
with the run. This is deliberately application-level orchestration: Practice
success criteria are scenario-specific and stay OUT of the engine's general
separation monitor (brief non-negotiable #7).

The evaluation question: was valid required separation (horizontal OR
vertical) established before the conflicting aircraft reached their crossing
point, and maintained through the encounter?
"""

from __future__ import annotations

from typing import Any

from airspacesim.core.separation import SeparationStandard, pair_measurements
from airspacesim.utils.conversions import haversine

PAST_MARGIN_NM = 0.5
DEFAULT_HORIZONTAL_NM = 10.0
DEFAULT_VERTICAL_FT = 1000.0


def _number_pair(value: Any) -> list[float] | None:
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(isinstance(item, (int, float)) for item in value)
    ):
        return [float(value[0]), float(value[1])]
    return None


class PracticeTracker:
    """Track one run's configured conflict pair and derive a final outcome."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.conflict_pair: list[str] = list(config["conflict_pair"])
        self.standard = SeparationStandard(
            horizontal_nm=float(
                config.get("required_horizontal_separation_nm", DEFAULT_HORIZONTAL_NM)
            ),
            vertical_ft=float(
                config.get("required_vertical_separation_ft", DEFAULT_VERTICAL_FT)
            ),
        )
        self.crossing_point = _number_pair(config.get("crossing_point"))
        self._encounter_min: dict[str, float] | None = None
        self._crossing_min: dict[str, float] | None = None
        self.outcome: dict[str, Any] | None = None

    @classmethod
    def from_metadata(cls, metadata_payload: dict[str, Any] | None) -> "PracticeTracker | None":
        practice = (metadata_payload or {}).get("practice")
        if not isinstance(practice, dict):
            return None
        pair = practice.get("conflict_pair")
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or not all(isinstance(item, str) for item in pair)
        ):
            return None
        return cls(practice)

    def observe(
        self,
        aircraft_items: list[dict[str, Any]],
        *,
        stopping: bool = False,
        commands_issued: int = 0,
    ) -> None:
        """Feed one state snapshot; freezes `self.outcome` when decidable."""
        if self.outcome is not None:
            return

        first = next(
            (item for item in aircraft_items if item["id"] == self.conflict_pair[0]),
            None,
        )
        second = next(
            (item for item in aircraft_items if item["id"] == self.conflict_pair[1]),
            None,
        )

        if first is None or second is None:
            if stopping:
                self._finish("manual_terminate", self._encounter_min, False, commands_issued)
            return

        horizontal_nm, vertical_ft = pair_measurements(first, second)
        if (
            self._encounter_min is None
            or horizontal_nm < self._encounter_min["horizontal_nm"]
        ):
            self._encounter_min = {
                "horizontal_nm": horizontal_nm,
                "vertical_ft": vertical_ft,
            }
        current = self._encounter_min

        if self.crossing_point is not None:
            dist_first = haversine(
                float(first["position_dd"][0]),
                float(first["position_dd"][1]),
                self.crossing_point[0],
                self.crossing_point[1],
            )
            dist_second = haversine(
                float(second["position_dd"][0]),
                float(second["position_dd"][1]),
                self.crossing_point[0],
                self.crossing_point[1],
            )
            next_first_min = (
                min(self._crossing_min["first"], dist_first)
                if self._crossing_min
                else dist_first
            )
            next_second_min = (
                min(self._crossing_min["second"], dist_second)
                if self._crossing_min
                else dist_second
            )
            self._crossing_min = {"first": next_first_min, "second": next_second_min}
            past_crossing = (
                dist_first > next_first_min + PAST_MARGIN_NM
                and dist_second > next_second_min + PAST_MARGIN_NM
            )
        else:
            # No crossing point configured: mutual closest approach is the
            # proxy for "the encounter has passed".
            past_crossing = horizontal_nm > current["horizontal_nm"] + PAST_MARGIN_NM

        if stopping:
            self._finish("manual_terminate", current, past_crossing, commands_issued)
            return

        if not self.standard.is_separated(
            current["horizontal_nm"], current["vertical_ft"]
        ):
            self._finish("loss_of_separation", current, False, commands_issued)
            return

        if past_crossing:
            self._finish("resolved", current, True, commands_issued)
            return

        if first.get("status") == "finished" and second.get("status") == "finished":
            self._finish("scenario_complete", current, True, commands_issued)

    def _finish(
        self,
        reason: str,
        current: dict[str, float] | None,
        resolution_confirmed: bool,
        commands_issued: int,
    ) -> None:
        if current is None:
            self.outcome = {
                "reason": reason,
                "separation_maintained": None,
                "conflict_resolved_before_crossing": None,
                "closest_horizontal_nm": None,
                "closest_vertical_ft": None,
                "applicable_form": None,
                "rating": None,
                "explanation": None,
                "commands_issued": commands_issued,
            }
            return

        separation_maintained = self.standard.is_separated(
            current["horizontal_nm"], current["vertical_ft"]
        )
        applicable_form = (
            "vertical"
            if current["vertical_ft"] >= self.standard.vertical_ft
            else "horizontal"
        )
        self.outcome = {
            "reason": reason,
            "separation_maintained": separation_maintained,
            "conflict_resolved_before_crossing": (
                reason != "loss_of_separation"
                and separation_maintained
                and resolution_confirmed
            ),
            "closest_horizontal_nm": current["horizontal_nm"],
            "closest_vertical_ft": current["vertical_ft"],
            "applicable_form": applicable_form,
            "rating": (
                "safe_effective" if separation_maintained else "loss_of_separation"
            ),
            "explanation": self._explanation(separation_maintained, applicable_form),
            "commands_issued": commands_issued,
        }

    def _explanation(self, separation_maintained: bool, applicable_form: str) -> str:
        if not separation_maintained:
            return (
                "Neither horizontal nor vertical separation was maintained "
                "when it was required."
            )
        if applicable_form == "vertical":
            return (
                f"Horizontal separation fell below "
                f"{self.standard.horizontal_nm:.0f} NM, but vertical separation "
                "was already established before the crossing."
            )
        return "Horizontal separation was maintained throughout the encounter."
