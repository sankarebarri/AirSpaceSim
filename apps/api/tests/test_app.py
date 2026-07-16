import pytest
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes.runs import create_run_route
from app.api.v1.routes.scenarios import create_scenario_route
from app.db.repositories import RunRepository
from app.main import create_app
from app.schemas.runs import RunCreateRequest
from app.schemas.scenarios import ScenarioCreateRequest

SESSION_ID = "test-session-a"


def test_app_registers_expected_routes():
    app = create_app()
    route_paths = {route.path for route in app.routes}
    cors_middleware = next(
        (
            middleware
            for middleware in app.user_middleware
            if middleware.cls is CORSMiddleware
        ),
        None,
    )

    assert "/health" in route_paths
    assert "/api/v1/airspaces" in route_paths
    assert "/api/v1/scenarios" in route_paths
    assert "/api/v1/runs" in route_paths
    assert "/api/v1/runs/practice" in route_paths
    assert "/api/v1/runs/{run_id}/commands" in route_paths
    assert "/api/v1/runs/{run_id}/stream" in route_paths
    assert cors_middleware is not None
    assert cors_middleware.kwargs["allow_origins"] == ["*"]
    assert cors_middleware.kwargs["allow_credentials"] is False
    assert hasattr(app.state, "session_registry")
    assert hasattr(app.state, "broadcast_hub")


@pytest.mark.anyio
async def test_app_lifespan_shutdown_clears_live_runtime_sessions(db_session):
    scenario = create_scenario_route(
        ScenarioCreateRequest(name="Lifespan Scenario"),
        db_session,
        SESSION_ID,
    )
    created_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="Lifespan Run"),
        db_session,
        SESSION_ID,
    )
    run_record = RunRepository(db_session).get(created_run.id, session_id=SESSION_ID)
    assert run_record is not None

    app = create_app()

    async with app.router.lifespan_context(app):
        registry = app.state.session_registry
        runtime_session = registry.start(
            run=run_record,
            scenario=run_record.scenario,
        )
        assert registry.get(run_record.id) is runtime_session
        assert runtime_session.runtime_status == "running"

    assert app.state.session_registry.list_sessions() == []
    assert app.state.session_registry.get(run_record.id) is None
