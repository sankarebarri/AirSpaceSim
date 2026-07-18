"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.requests import HTTPConnection

from .config import Settings, get_settings
from .db.models import UserRecord
from .db.session import get_db_session
from .limits import SlidingWindowRateLimiter
from .services.auth import resolve_auth_session
from .session_identity import SESSION_HEADER_NAME, SESSION_QUERY_PARAM, get_session_id
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


def get_optional_session_id(connection: HTTPConnection) -> str | None:
    """The guest session id when present/valid, else None (auth endpoints)."""

    candidate = connection.headers.get(SESSION_HEADER_NAME) or connection.query_params.get(
        SESSION_QUERY_PARAM
    )
    if not candidate:
        return None
    try:
        return get_session_id(connection)
    except HTTPException:
        return None


def get_optional_current_user(
    connection: HTTPConnection,
    db: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> UserRecord | None:
    """The signed-in user from the session cookie, else None (guest)."""

    token = connection.cookies.get(settings.auth_cookie_name)
    if not token:
        return None
    return resolve_auth_session(db, token)


def get_required_current_user(
    user: Annotated[UserRecord | None, Depends(get_optional_current_user)],
) -> UserRecord:
    """Reject guests on protected persistence routes."""

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to use this feature.",
        )
    return user


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
OptionalSessionIdDependency = Annotated[str | None, Depends(get_optional_session_id)]
CurrentUserDependency = Annotated[UserRecord, Depends(get_required_current_user)]
OptionalUserDependency = Annotated[
    UserRecord | None, Depends(get_optional_current_user)
]
RunCreationRateLimitDependency = Annotated[None, Depends(enforce_run_creation_rate_limit)]
