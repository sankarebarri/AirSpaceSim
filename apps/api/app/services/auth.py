"""Account, session, and guest-adoption services.

Minimal by decision Q7: email/password with secure server-side sessions.
No organisations, roles, or RBAC. Guests keep full access; signing in adds
persistence — on login/register the caller's anonymous session data (runs,
scenarios) is adopted onto the account so nothing is lost.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..db.models import AuthSessionRecord, RunRecord, ScenarioRecord, UserRecord
from ..security import (
    hash_password,
    hash_session_token,
    new_session_token,
    verify_password,
)

SUPPORTED_LANGUAGES = {"en", "fr"}
MIN_PASSWORD_LENGTH = 8


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or len(normalized) < 5 or len(normalized) > 254:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid email address.",
        )
    return normalized


def _validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
            ),
        )


def get_user_by_email(session: Session, email: str) -> UserRecord | None:
    return session.scalar(select(UserRecord).where(UserRecord.email == email))


def register_user(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str | None = None,
) -> UserRecord:
    normalized_email = _normalize_email(email)
    _validate_password(password)
    if get_user_by_email(session, normalized_email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = UserRecord(
        email=normalized_email,
        password_hash=hash_password(password),
        display_name=(display_name or "").strip() or None,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, *, email: str, password: str) -> UserRecord:
    normalized_email = email.strip().lower()
    user = get_user_by_email(session, normalized_email)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    return user


def create_auth_session(
    session: Session, *, user: UserRecord, ttl_days: int
) -> tuple[AuthSessionRecord, str]:
    """Create a server-side session; returns (record, browser token)."""

    token = new_session_token()
    record = AuthSessionRecord(
        token_hash=hash_session_token(token),
        user_id=user.id,
        expires_at=_utcnow() + timedelta(days=ttl_days),
    )
    session.add(record)
    session.commit()
    return record, token


def resolve_auth_session(session: Session, token: str) -> UserRecord | None:
    """Return the user for a live (unexpired) session token, else None."""

    record = session.scalar(
        select(AuthSessionRecord).where(
            AuthSessionRecord.token_hash == hash_session_token(token)
        )
    )
    if record is None:
        return None
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= _utcnow():
        session.delete(record)
        session.commit()
        return None
    return session.get(UserRecord, record.user_id)


def revoke_auth_session(session: Session, token: str) -> None:
    record = session.scalar(
        select(AuthSessionRecord).where(
            AuthSessionRecord.token_hash == hash_session_token(token)
        )
    )
    if record is not None:
        session.delete(record)
        session.commit()


def adopt_guest_data(
    session: Session, *, user: UserRecord, guest_session_id: str | None
) -> int:
    """Attach the anonymous browser session's runs/scenarios to the account."""

    if not guest_session_id:
        return 0
    adopted = 0
    for model in (RunRecord, ScenarioRecord):
        result = session.execute(
            update(model)
            .where(
                model.session_id == guest_session_id,
                model.user_id.is_(None),
            )
            .values(user_id=user.id)
        )
        adopted += int(result.rowcount or 0)
    session.commit()
    return adopted


def update_profile(
    session: Session,
    *,
    user: UserRecord,
    display_name: str | None = None,
    preferred_language: str | None = None,
) -> UserRecord:
    if display_name is not None:
        user.display_name = display_name.strip() or None
    if preferred_language is not None:
        if preferred_language not in SUPPORTED_LANGUAGES:
            supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language. Supported languages: {supported}.",
            )
        user.preferred_language = preferred_language
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
