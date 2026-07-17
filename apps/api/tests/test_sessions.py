import time

from app.db.repositories import RunCheckpointRepository
from app.services.runs import create_run
from app.services.scenarios import resolve_scenario_contracts
from app.sessions import SessionRegistry
from app.sessions.runtime import SimulationRuntimeSession

SESSION_ID = "test-session-a"


def build_runtime_session(*, sim_rate: float = 1.0, state_publisher=None) -> SimulationRuntimeSession:
    scenario_airspace, scenario_aircraft = resolve_scenario_contracts(None)
    return SimulationRuntimeSession(
        run_id="runtime-test-run",
        scenario_airspace=scenario_airspace,
        scenario_aircraft=scenario_aircraft,
        sim_rate=sim_rate,
        update_interval_seconds=0.01,
        state_publisher=state_publisher,
    )


def test_runtime_session_add_aircraft_command_normalizes_route_payload():
    published_events: list[tuple[str, dict]] = []
    runtime_session = build_runtime_session(
        state_publisher=lambda run_id, snapshot, checkpoint_type: published_events.append(
            (checkpoint_type, snapshot)
        )
    )

    before_snapshot = runtime_session.state_snapshot()
    result = runtime_session.apply_command(
        command_id="cmd-add",
        command_type="ADD_AIRCRAFT",
        payload={
            "id": "AC990",
            "route": "UL602",
            "callsign": "OPS990",
        },
    )
    after_snapshot = runtime_session.state_snapshot()

    assert result["applied"] == ["cmd-add"]
    assert after_snapshot["metrics"]["aircraft_count"] == (
        before_snapshot["metrics"]["aircraft_count"] + 1
    )
    added_aircraft = next(
        item for item in after_snapshot["aircraft"] if item["id"] == "AC990"
    )
    assert added_aircraft["callsign"] == "OPS990"
    assert added_aircraft["route_id"] == "UL602"
    assert published_events[-1][0] == "command"


def test_runtime_session_set_speed_normalizes_speed_key_and_enforces_aircraft_id_lookup():
    runtime_session = build_runtime_session()
    baseline_snapshot = runtime_session.state_snapshot()
    target_aircraft = next(
        item for item in baseline_snapshot["aircraft"] if item["callsign"]
    )

    skipped_result = runtime_session.apply_command(
        command_id="cmd-skip",
        command_type="SET_SPEED",
        payload={
            "aircraft_id": target_aircraft["callsign"],
            "speed": 499,
        },
    )
    applied_result = runtime_session.apply_command(
        command_id="cmd-speed",
        command_type="SET_SPEED",
        payload={
            "aircraft_id": target_aircraft["id"],
            "speed": 499,
        },
    )
    updated_snapshot = runtime_session.state_snapshot()
    updated_aircraft = next(
        item for item in updated_snapshot["aircraft"] if item["id"] == target_aircraft["id"]
    )

    assert skipped_result["applied"] == []
    assert "matched callsign" in skipped_result["skipped"][0][1]
    assert applied_result["applied"] == ["cmd-speed"]
    assert updated_aircraft["speed_kt"] == 499.0


def test_runtime_session_simulation_speed_validation_and_terminal_rejection():
    runtime_session = build_runtime_session()

    rejected_result = runtime_session.apply_command(
        command_id="cmd-invalid-rate",
        command_type="SET_SIMULATION_SPEED",
        payload={"sim_rate": 0},
    )
    applied_result = runtime_session.apply_command(
        command_id="cmd-valid-rate",
        command_type="SET_SIMULATION_SPEED",
        payload={"sim_rate": 2.5},
    )
    runtime_session.stop()
    stopped_result = runtime_session.apply_command(
        command_id="cmd-after-stop",
        command_type="ADD_AIRCRAFT",
        payload={"aircraft_id": "AC999", "route_id": "UL602"},
    )

    assert rejected_result["rejected"] == [("cmd-invalid-rate", "invalid sim_rate")]
    assert applied_result["applied"] == ["cmd-valid-rate"]
    assert runtime_session.state_snapshot()["sim_rate"] == 2.5
    assert stopped_result["rejected"] == [
        ("cmd-after-stop", "runtime session is stopped")
    ]


def test_session_registry_stop_discards_runtime_and_persists_stopped_checkpoint(db_session):
    run = create_run(db_session, session_id=SESSION_ID, name="Registry Test Run")
    registry = SessionRegistry(
        update_interval_seconds=0.01,
        checkpoint_interval_seconds=60.0,
    )

    try:
        runtime_session = registry.start(run=run, scenario=None)
        assert registry.get(run.id) is runtime_session

        time.sleep(0.05)
        registry.stop(run.id)

        latest_checkpoint = RunCheckpointRepository(db_session).latest_for_run(run.id)

        assert registry.get(run.id) is None
        assert registry.list_sessions() == []
        assert latest_checkpoint is not None
        assert latest_checkpoint.checkpoint_type == "stopped"
        assert run.id not in registry._last_checkpoint_at
    finally:
        registry.shutdown()
