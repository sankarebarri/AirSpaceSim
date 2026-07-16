"""Run command API schemas."""

from datetime import datetime
from typing import Literal
from typing import Any

from pydantic import BaseModel, Field


class RunCommandCreateRequest(BaseModel):
    """Payload for storing an operator command."""

    command_type: str = Field(min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class RunCommandResponse(BaseModel):
    """Durable operator command representation."""

    id: str
    run_id: str
    command_type: str
    status: str
    payload: dict[str, Any]
    created_at: datetime
    applied_at: datetime | None

    model_config = {"from_attributes": True}


class CommandResultItem(BaseModel):
    """One skipped or rejected command result item."""

    command_id: str
    reason: str


class RunCommandResultResponse(BaseModel):
    """Authoritative command handling result."""

    state: Literal["queued", "applied", "skipped", "rejected"]
    applied: list[str] = Field(default_factory=list)
    skipped: list[CommandResultItem] = Field(default_factory=list)
    rejected: list[CommandResultItem] = Field(default_factory=list)


class RunCommandSubmissionResponse(BaseModel):
    """Persisted command plus immediate handling outcome."""

    command: RunCommandResponse
    result: RunCommandResultResponse
