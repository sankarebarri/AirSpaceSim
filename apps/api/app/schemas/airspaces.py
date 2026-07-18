"""Airspace package API schemas."""

from pydantic import BaseModel, Field


class AirspaceScenarioSummary(BaseModel):
    """Scenario listed by an airspace package manifest."""

    id: str
    title: str
    path: str
    description: str | None = None
    service_type: str | None = None
    training_mode: str | None = None
    difficulty: str | None = None


class AirspaceLessonSummary(BaseModel):
    """Lesson listed by an airspace package manifest."""

    id: str
    title: str
    path: str
    scenario_id: str | None = None
    service_type: str | None = None
    training_mode: str | None = None
    level: str | None = None
    duration_minutes: float | None = None


class AirspacePackageSummary(BaseModel):
    """Discoverable airspace package summary."""

    id: str
    version: str | None = None
    name: str
    description: str
    package_type: str
    service_types: list[str] = Field(default_factory=list)
    difficulty: str
    training_modes: list[str] = Field(default_factory=list)
    airspace_file: str
    default_scenario: str | None = None
    map: dict = Field(default_factory=dict)
    scenarios: list[AirspaceScenarioSummary] = Field(default_factory=list)
    lessons: list[AirspaceLessonSummary] = Field(default_factory=list)


class AirspacePackageListResponse(BaseModel):
    """Airspace package list envelope."""

    items: list[AirspacePackageSummary]
