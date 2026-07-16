"""Scenario API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScenarioCreateRequest(BaseModel):
    """Payload for creating a durable scenario."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    airspace_payload: dict[str, Any] = Field(default_factory=dict)
    aircraft_payload: dict[str, Any] = Field(default_factory=dict)
    metadata_payload: dict[str, Any] = Field(default_factory=dict)


class ScenarioUpdateRequest(BaseModel):
    """Payload for updating a stored scenario."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    airspace_payload: dict[str, Any] | None = None
    aircraft_payload: dict[str, Any] | None = None
    metadata_payload: dict[str, Any] | None = None


class ScenarioResponse(BaseModel):
    """Durable scenario representation."""

    id: str
    slug: str
    name: str
    description: str | None
    airspace_payload: dict[str, Any]
    aircraft_payload: dict[str, Any]
    metadata_payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScenarioListResponse(BaseModel):
    """Scenario list envelope."""

    items: list[ScenarioResponse]
