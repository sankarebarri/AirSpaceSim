"""Aircraft performance profile loading for simulation behavior."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def load_aircraft_performance_profiles() -> dict[str, dict[str, Any]]:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads(
        (root / "data" / "aircraft_performance.v1.json").read_text(encoding="utf-8")
    )
    return payload["data"]["aircraft_types"]


def get_aircraft_performance_profile(aircraft_type: str | None) -> dict[str, Any]:
    profiles = load_aircraft_performance_profiles()
    normalized_type = str(aircraft_type or "B737").strip().upper()
    return profiles.get(normalized_type) or profiles["B737"]


def assigned_level_vertical_rate_fpm(
    aircraft_type: str | None,
    current_altitude_ft: float,
    target_flight_level: int,
) -> float:
    target_altitude_ft = float(target_flight_level) * 100.0
    if abs(target_altitude_ft - float(current_altitude_ft)) < 1.0:
        return 0.0

    vertical = get_aircraft_performance_profile(aircraft_type)["vertical"]
    if target_altitude_ft > float(current_altitude_ft):
        return float(vertical["default_climb_fpm"])
    return -float(vertical["default_descent_fpm"])


def speed_limits_kt(aircraft_type: str | None) -> tuple[float, float]:
    speed = get_aircraft_performance_profile(aircraft_type)["speed"]
    minimum = float(speed["min_clean_kt"])
    maximum = max(
        float(speed["max_operating_kt"]),
        float(speed["default_cruise_kt"]) * 1.5,
    )
    return minimum, maximum


def max_flight_level(aircraft_type: str | None) -> int:
    limits = get_aircraft_performance_profile(aircraft_type)["limits"]
    return int(round(float(limits["max_fl"])))


def turn_rate_deg_per_sec(
    aircraft_type: str | None,
    speed_kt: float | None = None,
) -> float:
    turning = get_aircraft_performance_profile(aircraft_type)["turning"]
    standard_rate = float(turning["standard_rate_deg_per_sec"])
    if speed_kt is None:
        return standard_rate

    minimum_radius_nm = float(turning["min_turn_radius_nm"])
    speed_nm_per_sec = max(float(speed_kt), 0.0) / 3600.0
    if minimum_radius_nm <= 0 or speed_nm_per_sec <= 0:
        return standard_rate

    radius_limited_rate = math.degrees(speed_nm_per_sec / minimum_radius_nm)
    return min(standard_rate, radius_limited_rate)


def hold_speed_kt(aircraft_type: str | None) -> float:
    holding = get_aircraft_performance_profile(aircraft_type)["holding"]
    return float(holding["hold_speed_kt"])
