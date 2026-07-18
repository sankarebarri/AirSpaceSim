"""User accounts, server-side auth sessions, and learning progress."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .scenario import utcnow


class UserRecord(Base):
    """Minimal user account: authentication plus profile preferences."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(254), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    preferred_language: Mapped[str] = mapped_column(
        String(8), default="en", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    auth_sessions = relationship(
        "AuthSessionRecord", back_populates="user", cascade="all, delete-orphan"
    )
    progress_entries = relationship(
        "LearningProgressRecord", back_populates="user", cascade="all, delete-orphan"
    )


class AuthSessionRecord(Base):
    """Server-side login session; the browser holds only an opaque token.

    The token itself is never stored — only its SHA-256 hash — so a leaked
    database cannot be replayed as live sessions.
    """

    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("UserRecord", back_populates="auth_sessions")


class LearningProgressRecord(Base):
    """Per-user lesson/stage completion for signed-in learners.

    Guests keep progress in browser storage only (decision Q10).
    """

    __tablename__ = "learning_progress"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "concept_id", "stage_key", name="uq_progress_user_concept_stage"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(String(80), nullable=False)
    stage_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    user = relationship("UserRecord", back_populates="progress_entries")
