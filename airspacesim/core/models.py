"""Typed core domain models used by simulation orchestration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Waypoint:
    id: str
    position_dd: tuple[float, float]


@dataclass(frozen=True)
class AircraftDefinition:
    id: str
    route_id: str
    speed_kt: float
    callsign: str | None = None
    flight_level: int | None = None
    altitude_ft: float = 0.0
    vertical_rate_fpm: float = 0.0


@dataclass(frozen=True)
class ScenarioBundle:
    """Unified scenario model used by core-facing interfaces."""

    points: dict[str, Waypoint]
    routes: dict[str, tuple[str, ...]]
    aircraft: tuple[AircraftDefinition, ...]


@dataclass(frozen=True)
class TrajectoryTrack:
    id: str
    route_id: str
    position_dd: tuple[float, float]
    status: str
    updated_utc: str
    callsign: str | None = None
    speed_kt: float | None = None
    flight_level: int | None = None
    altitude_ft: float | None = None
    vertical_rate_fpm: float | None = None

    def as_contract_dict(self):
        payload = {
            "id": self.id,
            "route_id": self.route_id,
            "position_dd": [self.position_dd[0], self.position_dd[1]],
            "status": self.status,
            "updated_utc": self.updated_utc,
        }
        if self.callsign is not None:
            payload["callsign"] = self.callsign
        if self.speed_kt is not None:
            payload["speed_kt"] = self.speed_kt
        if self.flight_level is not None:
            payload["flight_level"] = self.flight_level
        if self.altitude_ft is not None:
            payload["altitude_ft"] = self.altitude_ft
        if self.vertical_rate_fpm is not None:
            payload["vertical_rate_fpm"] = self.vertical_rate_fpm
        return payload
