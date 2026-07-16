from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_engine, get_session_factory, init_db
from app.sessions import SessionRegistry
from app.ws import BroadcastHub


def _reset_api_caches() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def db_session(tmp_path, monkeypatch) -> Iterator[Session]:
    db_path = tmp_path / "airspacesim-api-test.db"
    monkeypatch.setenv("AIRSPACESIM_API_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AIRSPACESIM_API_AUTO_CREATE_SCHEMA", "1")
    _reset_api_caches()

    init_db()
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()

    _reset_api_caches()


@pytest.fixture
def broadcast_hub() -> BroadcastHub:
    return BroadcastHub()


@pytest.fixture
def session_registry(broadcast_hub) -> Iterator[SessionRegistry]:
    registry = SessionRegistry(update_interval_seconds=0.01, broadcast_hub=broadcast_hub)
    try:
        yield registry
    finally:
        registry.shutdown()
