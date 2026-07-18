"""Scenario persistence models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from ..base import Base


def utcnow() -> datetime:
    """Return an aware UTC timestamp for ORM defaults."""

    return datetime.now(timezone.utc)


class ScenarioRecord(Base):
    """Durable scenario definition for the hosted application."""

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    airspace_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    aircraft_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metadata_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    runs = relationship("RunRecord", back_populates="scenario")
