"""Shared API response models."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Simple placeholder response model."""

    detail: str

