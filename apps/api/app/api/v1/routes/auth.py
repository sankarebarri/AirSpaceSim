"""Authentication routes: register, login, logout, current user, profile."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from starlette.requests import HTTPConnection

from ....config import Settings
from ....db.models import UserRecord
from ....dependencies import (
    CurrentUserDependency,
    DbSessionDependency,
    OptionalSessionIdDependency,
    SettingsDependency,
    get_optional_current_user,
)
from ....schemas.auth import (
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    UserResponse,
)
from ....services.auth import (
    adopt_guest_data,
    authenticate_user,
    create_auth_session,
    register_user,
    revoke_auth_session,
    update_profile,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(
    response: Response, settings: Settings, token: str
) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.auth_session_ttl_days * 24 * 3600,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path="/",
    )


def _start_session(
    db,
    response: Response,
    settings: Settings,
    user: UserRecord,
    guest_session_id: str | None,
) -> UserResponse:
    adopt_guest_data(db, user=user, guest_session_id=guest_session_id)
    _, token = create_auth_session(
        db, user=user, ttl_days=settings.auth_session_ttl_days
    )
    _set_session_cookie(response, settings, token)
    return UserResponse.model_validate(user)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register(
    payload: RegisterRequest,
    response: Response,
    db: DbSessionDependency,
    settings: SettingsDependency,
    guest_session_id: OptionalSessionIdDependency,
) -> UserResponse:
    """Create an account and sign in; adopts the guest session's data."""

    user = register_user(
        db,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    return _start_session(db, response, settings, user, guest_session_id)


@router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: DbSessionDependency,
    settings: SettingsDependency,
    guest_session_id: OptionalSessionIdDependency,
) -> UserResponse:
    """Sign in with email and password; adopts the guest session's data."""

    user = authenticate_user(db, email=payload.email, password=payload.password)
    return _start_session(db, response, settings, user, guest_session_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    connection: HTTPConnection,
    response: Response,
    db: DbSessionDependency,
    settings: SettingsDependency,
) -> Response:
    """Revoke the server-side session and clear the cookie."""

    token = connection.cookies.get(settings.auth_cookie_name)
    if token:
        revoke_auth_session(db, token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(settings.auth_cookie_name, path="/")
    return response


@router.get("/me", response_model=UserResponse)
def current_user(
    user: Annotated[UserRecord | None, Depends(get_optional_current_user)],
) -> UserResponse:
    """Return the signed-in user, or 401 for guests."""

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not signed in.",
        )
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
def update_current_user(
    payload: ProfileUpdateRequest,
    user: CurrentUserDependency,
    db: DbSessionDependency,
) -> UserResponse:
    """Update display name and/or preferred language (protected)."""

    updated = update_profile(
        db,
        user=user,
        display_name=payload.display_name,
        preferred_language=payload.preferred_language,
    )
    return UserResponse.model_validate(updated)
