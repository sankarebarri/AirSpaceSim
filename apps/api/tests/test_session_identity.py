import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.session import get_engine, get_session_factory
from app.main import create_app


def _reset_api_caches() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def build_client(tmp_path, monkeypatch):
    """Build a TestClient against a fresh SQLite database with overridable env."""

    def _build(**env_overrides) -> TestClient:
        db_path = tmp_path / f"session-identity-{len(env_overrides)}-{id(env_overrides)}.db"
        monkeypatch.setenv("AIRSPACESIM_API_DATABASE_URL", f"sqlite:///{db_path}")
        monkeypatch.setenv("AIRSPACESIM_API_AUTO_CREATE_SCHEMA", "1")
        for key, value in env_overrides.items():
            monkeypatch.setenv(key, value)
        _reset_api_caches()
        app = create_app()
        return TestClient(app)

    yield _build
    _reset_api_caches()


def test_missing_session_header_is_rejected(build_client):
    client = build_client()
    with client:
        response = client.get("/api/v1/runs")

    assert response.status_code == 400


def test_invalid_session_header_is_rejected(build_client):
    client = build_client()
    with client:
        response = client.get(
            "/api/v1/runs", headers={"X-Airspacesim-Session": "a b!"}
        )

    assert response.status_code == 400


def test_session_query_param_is_accepted(build_client):
    client = build_client()
    with client:
        response = client.get("/api/v1/runs?sid=session-via-query-1234")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_runs_are_isolated_between_sessions(build_client):
    client = build_client()
    with client:
        session_a_headers = {"X-Airspacesim-Session": "session-a-0000"}
        session_b_headers = {"X-Airspacesim-Session": "session-b-0000"}

        created = client.post(
            "/api/v1/runs", json={"name": "Session A Run"}, headers=session_a_headers
        )
        assert created.status_code == 201
        run_id = created.json()["id"]

        owner_list = client.get("/api/v1/runs", headers=session_a_headers)
        assert [item["id"] for item in owner_list.json()["items"]] == [run_id]

        other_list = client.get("/api/v1/runs", headers=session_b_headers)
        assert other_list.json()["items"] == []

        other_get = client.get(f"/api/v1/runs/{run_id}", headers=session_b_headers)
        assert other_get.status_code == 404

        owner_get = client.get(f"/api/v1/runs/{run_id}", headers=session_a_headers)
        assert owner_get.status_code == 200


def test_run_creation_rate_limit_returns_429(build_client):
    client = build_client(AIRSPACESIM_API_RATE_LIMIT_RUN_CREATES_PER_MINUTE="2")
    with client:
        headers = {"X-Airspacesim-Session": "rate-limit-session"}
        first = client.post("/api/v1/runs", json={"name": "First"}, headers=headers)
        second = client.post("/api/v1/runs", json={"name": "Second"}, headers=headers)
        third = client.post("/api/v1/runs", json={"name": "Third"}, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 429


def test_oversized_request_body_returns_413(build_client):
    client = build_client(AIRSPACESIM_API_MAX_REQUEST_BODY_BYTES="16")
    with client:
        response = client.post(
            "/api/v1/runs",
            json={"name": "x" * 200},
            headers={"X-Airspacesim-Session": "body-size-session"},
        )

    assert response.status_code == 413


def test_cors_wildcard_in_production_raises_at_startup(tmp_path, monkeypatch):
    db_path = tmp_path / "cors-guard.db"
    monkeypatch.setenv("AIRSPACESIM_API_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AIRSPACESIM_API_ENVIRONMENT", "production")
    monkeypatch.delenv("AIRSPACESIM_API_CORS_ALLOWED_ORIGINS", raising=False)
    _reset_api_caches()

    try:
        with pytest.raises(RuntimeError):
            create_app()
    finally:
        _reset_api_caches()
