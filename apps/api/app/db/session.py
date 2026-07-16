"""SQLAlchemy engine and session management."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_settings
from . import models  # noqa: F401
from .base import Base


def _sqlite_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


@lru_cache
def get_engine() -> Engine:
    """Create and cache the SQLAlchemy engine."""

    settings = get_settings()
    database_path = settings.database_path
    if database_path is not None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        settings.database_url,
        echo=settings.database_echo,
        future=True,
        connect_args=_sqlite_connect_args(settings.database_url),
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the configured SQLAlchemy session factory."""

    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def init_db() -> None:
    """Create the configured schema for local development and tests."""

    Base.metadata.create_all(bind=get_engine())


def get_db_session():
    """Yield a request-scoped database session."""

    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
