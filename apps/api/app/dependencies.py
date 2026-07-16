"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session
from starlette.requests import HTTPConnection

from .config import Settings, get_settings
from .db.session import get_db_session
from .limits import SlidingWindowRateLimiter
from .session_identity import get_session_id
from .sessions import SessionRegistry
from .ws import BroadcastHub


def get_settings_dependency() -> Settings:
    """Expose service settings through FastAPI dependency injection."""

    return get_settings()


def get_session_registry_dependency(connection: HTTPConnection) -> SessionRegistry:
    """Expose the in-memory runtime session registry."""

    return connection.app.state.session_registry


def get_broadcast_hub_dependency(connection: HTTPConnection) -> BroadcastHub:
    """Expose the live broadcast hub."""

    return connection.app.state.broadcast_hub


def enforce_run_creation_rate_limit(
    connection: HTTPConnection,
    session_id: Annotated[str, Depends(get_session_id)],
) -> None:
    """Throttle run-creation requests per session id."""

    limiter: SlidingWindowRateLimiter = connection.app.state.run_creation_rate_limiter
    limiter.check(session_id)


SettingsDependency = Annotated[Settings, Depends(get_settings_dependency)]
DbSessionDependency = Annotated[Session, Depends(get_db_session)]
SessionRegistryDependency = Annotated[
    SessionRegistry,
    Depends(get_session_registry_dependency),
]
BroadcastHubDependency = Annotated[
    BroadcastHub,
    Depends(get_broadcast_hub_dependency),
]
SessionIdDependency = Annotated[str, Depends(get_session_id)]
RunCreationRateLimitDependency = Annotated[None, Depends(enforce_run_creation_rate_limit)]
