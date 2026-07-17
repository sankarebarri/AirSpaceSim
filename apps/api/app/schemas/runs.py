"""Run API schemas."""

from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field


class RunCreateRequest(BaseModel):
    """Payload for creating a run shell."""

    scenario_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)


class PracticeRunCreateRequest(BaseModel):
    """Payload for creating a live practice run from package content."""

    airspace_id: str = Field(min_length=1, max_length=120)
    scenario_id: str | None = Field(default=None, min_length=1, max_length=120)
    lesson_id: str | None = Field(default=None, min_length=1, max_length=160)
    name: str | None = Field(default=None, min_length=1, max_length=120)


class RunResponse(BaseModel):
    """Durable run representation."""

    id: str
    scenario_id: str | None
    name: str | None
    status: str
    sim_rate: float
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    summary: dict | None = Field(
        default=None,
        validation_alias=AliasChoices("summary_json", "summary"),
    )

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    """Run list envelope."""

    items: list[RunResponse]


class RunAircraftStateResponse(BaseModel):
    """Live aircraft state rendered for the hosted API."""

    id: str
    callsign: str | None
    aircraft_type: str = "UNKNOWN"
    route_id: str
    position_dd: list[float]
    speed_kt: float
    flight_level: int
    target_flight_level: int | None = None
    altitude_ft: float
    vertical_rate_fpm: float
    heading_deg: float = 0.0
    assigned_heading_deg: float | None = None
    assigned_radial_deg: float | None = None
    radial_deviation_deg: float | None = None
    radial_cross_track_nm: float | None = None
    lateral_mode: str = "route"
    direct_to_fix_id: str | None = None
    hold_fix_id: str | None = None
    traffic_flow: str
    status: str
    updated_utc: str


class RunMetricsResponse(BaseModel):
    """Minimal runtime counters for the simulation session."""

    aircraft_count: int
    active_aircraft_count: int
    finished_aircraft_count: int
    pending_aircraft_count: int = 0


class RunSeparationViolationResponse(BaseModel):
    """One currently violating aircraft pair from the engine monitor."""

    pair: list[str]
    horizontal_nm: float
    vertical_ft: float
    started_at_seconds: float


class RunSeparationResponse(BaseModel):
    """Engine separation-monitor state for a run."""

    standard: dict
    active_violations: list[RunSeparationViolationResponse] = Field(
        default_factory=list
    )
    loss_of_separation_count: int = 0


class RunStateResponse(BaseModel):
    """Live run state, combining durable metadata and runtime session info."""

    run: RunResponse
    runtime_status: str
    sim_rate: float
    updated_utc: str | None = None
    source: str
    last_error: str | None = None
    time_seconds: float | None = None
    aircraft: list[RunAircraftStateResponse] = Field(default_factory=list)
    separation: RunSeparationResponse | None = None
    summary: dict | None = None
    metrics: RunMetricsResponse


class RunTrajectoryTrackResponse(BaseModel):
    """Live trajectory track item."""

    id: str
    route_id: str
    position_dd: list[float]
    status: str
    updated_utc: str
    callsign: str | None = None
    speed_kt: float | None = None
    flight_level: int | None = None
    altitude_ft: float | None = None
    vertical_rate_fpm: float | None = None


class RunTrajectoryResponse(BaseModel):
    """Live trajectory snapshot for a run."""

    run_id: str
    runtime_status: str
    updated_utc: str | None = None
    tracks: list[RunTrajectoryTrackResponse]
