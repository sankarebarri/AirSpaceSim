"""Simulation run persistence models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from ..base import Base
from .scenario import utcnow


class RunRecord(Base):
    """Durable run metadata and lifecycle state."""

    __tablename__ = "runs"

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
    scenario_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("scenarios.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    sim_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    scenario = relationship("ScenarioRecord", back_populates="runs")
    commands = relationship(
        "RunCommandRecord",
        back_populates="run",
        cascade="all, delete-orphan",
    )
    checkpoints = relationship(
        "RunCheckpointRecord",
        back_populates="run",
        cascade="all, delete-orphan",
    )
