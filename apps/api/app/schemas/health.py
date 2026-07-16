"""Health route response models."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Minimal health payload."""

    status: str
    service: str
    database: str
