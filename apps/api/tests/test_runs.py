from queue import Empty

import pytest
from fastapi import HTTPException

from app.api.v1.routes.commands import submit_command
from app.api.v1.routes.runs import (
    create_run_route,
    create_practice_run_route,
    export_run_csv,
    get_run_state,
    list_runs,
    pause_run,
    resume_run,
    start_run,
    stop_run,
    get_run_trajectory,
)
from app.api.v1.routes.scenarios import create_scenario_route
from app.config import get_settings
from app.db.repositories import RunCheckpointRepository
from app.schemas.commands import RunCommandCreateRequest
from app.schemas.runs import PracticeRunCreateRequest, RunCreateRequest
from app.schemas.scenarios import ScenarioCreateRequest
from app.sessions import SessionRegistry

SESSION_ID = "test-session-a"


def _drain_events(subscriber):
    events = []
    while True:
        try:
            events.append(subscriber.queue.get_nowait())
        except Empty:
            return events


def test_run_lifecycle_and_command_persistence(
    db_session,
    session_registry,
    broadcast_hub,
):
    settings = get_settings()
    scenario = create_scenario_route(
        ScenarioCreateRequest(name="Lifecycle Scenario"),
        db_session,
        SESSION_ID,
    )
    created_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="Morning Session"),
        db_session,
        SESSION_ID,
    )
    assert created_run.status == "draft"

    subscriber = broadcast_hub.subscribe(created_run.id)
    inactive_state = get_run_state(created_run.id, db_session, session_registry, SESSION_ID)
    assert inactive_state.runtime_status == "inactive"

    started_run = start_run(
        created_run.id, db_session, session_registry, SESSION_ID, settings
    )
    assert started_run.status == "running"
    assert started_run.started_at is not None
    assert any(
        event["type"] == "run_state.updated" for event in _drain_events(subscriber)
    )

    running_state = get_run_state(created_run.id, db_session, session_registry, SESSION_ID)
    assert running_state.runtime_status == "running"
    assert running_state.metrics.aircraft_count >= 1
    initial_aircraft_count = running_state.metrics.aircraft_count

    paused_run = pause_run(created_run.id, db_session, session_registry, SESSION_ID)
    assert paused_run.status == "paused"

    paused_state = get_run_state(created_run.id, db_session, session_registry, SESSION_ID)
    assert paused_state.runtime_status == "paused"

    resumed_run = resume_run(created_run.id, db_session, session_registry, SESSION_ID)
    assert resumed_run.status == "running"

    command = submit_command(
        created_run.id,
        RunCommandCreateRequest(
            command_type="ADD_AIRCRAFT",
            payload={"id": "AC900", "route": "UA612"},
        ),
        db_session,
        session_registry,
        broadcast_hub,
        SESSION_ID,
    )
    assert command.command.command_type == "ADD_AIRCRAFT"
    assert command.command.payload["id"] == "AC900"
    assert command.command.status == "applied"
    assert command.result.state == "applied"
    command_events = _drain_events(subscriber)
    assert any(event["type"] == "run_command.result" for event in command_events)

    state_response = get_run_state(created_run.id, db_session, session_registry, SESSION_ID)
    assert state_response.run.status == "running"
    assert state_response.runtime_status == "running"
    assert state_response.metrics.aircraft_count == initial_aircraft_count + 1

    trajectory_response = get_run_trajectory(
        created_run.id, db_session, session_registry, SESSION_ID
    )
    assert trajectory_response.runtime_status == "running"
    assert len(trajectory_response.tracks) == state_response.metrics.aircraft_count

    stopped_run = stop_run(created_run.id, db_session, session_registry, SESSION_ID)
    assert stopped_run.status == "stopped"
    assert stopped_run.ended_at is not None

    stopped_state = get_run_state(created_run.id, db_session, session_registry, SESSION_ID)
    assert stopped_state.runtime_status == "stopped"
    assert any(
        event["type"] == "run_state.updated" for event in _drain_events(subscriber)
    )

    list_response = list_runs(db_session, SESSION_ID)
    assert len(list_response.items) == 1
    broadcast_hub.unsubscribe(subscriber)


def test_create_practice_run_from_lesson_starts_runtime(db_session, session_registry):
    settings = get_settings()
    created_run = create_practice_run_route(
        PracticeRunCreateRequest(
            airspace_id="training_alpha",
            lesson_id="enroute_heading_vs_radial_intro",
            name="Heading Versus Radial Practice",
        ),
        db_session,
        session_registry,
        SESSION_ID,
        settings,
    )

    assert created_run.status == "running"
    assert created_run.scenario_id is not None
    state_response = get_run_state(created_run.id, db_session, session_registry, SESSION_ID)
    assert state_response.runtime_status == "running"
    # beginner_mix schedules 4 aircraft at t=0 and 4 with appear_after_seconds
    # of 10-40s; scheduled entries are engine-owned since Phase 2, so the run
    # starts with 4 live aircraft and 4 pending instead of all 8 at once.
    assert state_response.metrics.aircraft_count == 4
    assert state_response.metrics.pending_aircraft_count == 4
    assert state_response.aircraft[0].callsign.startswith("ALP")


def test_restarting_same_lesson_replaces_previous_active_practice_run(
    db_session,
    session_registry,
):
    settings = get_settings()
    settings.max_concurrent_runs_per_session = 3

    created_runs = [
        create_practice_run_route(
            PracticeRunCreateRequest(
                airspace_id="training_alpha",
                lesson_id="enroute_crossing_traffic_intro",
            ),
            db_session,
            session_registry,
            SESSION_ID,
            settings,
        )
        for _ in range(4)
    ]

    listed_runs = list_runs(db_session, SESSION_ID).items
    assert [run.status for run in created_runs] == ["running"] * 4
    assert sum(1 for run in listed_runs if run.status == "running") == 1
    assert sum(1 for run in listed_runs if run.status == "stopped") == 3
    assert session_registry.get(created_runs[-1].id) is not None
    assert all(session_registry.get(run.id) is None for run in created_runs[:-1])


def test_invalid_run_transition_returns_conflict(db_session, session_registry):
    created_run = create_run_route(RunCreateRequest(), db_session, SESSION_ID)

    with pytest.raises(HTTPException) as excinfo:
        pause_run(created_run.id, db_session, session_registry, SESSION_ID)

    assert excinfo.value.status_code == 409


def test_command_without_runtime_session_is_queued(
    db_session,
    session_registry,
    broadcast_hub,
):
    created_run = create_run_route(RunCreateRequest(), db_session, SESSION_ID)

    response = submit_command(
        created_run.id,
        RunCommandCreateRequest(
            command_type="ADD_AIRCRAFT",
            payload={"id": "AC901", "route": "UA612"},
        ),
        db_session,
        session_registry,
        broadcast_hub,
        SESSION_ID,
    )

    assert response.command.status == "accepted"
    assert response.result.state == "queued"


def test_export_run_csv_returns_live_runtime_snapshot(
    db_session,
    session_registry,
):
    settings = get_settings()
    scenario = create_scenario_route(
        ScenarioCreateRequest(name="Export Scenario"),
        db_session,
        SESSION_ID,
    )
    created_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="Export Session"),
        db_session,
        SESSION_ID,
    )
    start_run(created_run.id, db_session, session_registry, SESSION_ID, settings)

    response = export_run_csv(created_run.id, db_session, session_registry, SESSION_ID)
    csv_text = response.body.decode("utf-8")

    assert response.status_code == 200
    assert response.media_type == "text/csv"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert "id,callsign,route_id,status" in csv_text
    assert len(csv_text.strip().splitlines()) >= 2


def test_command_is_rejected_when_runtime_is_missing_for_running_run(
    db_session,
    session_registry,
    broadcast_hub,
):
    settings = get_settings()
    scenario = create_scenario_route(
        ScenarioCreateRequest(name="Recovery Scenario"),
        db_session,
        SESSION_ID,
    )
    created_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="Recovery Session"),
        db_session,
        SESSION_ID,
    )
    start_run(created_run.id, db_session, session_registry, SESSION_ID, settings)

    orphaned_registry = SessionRegistry(update_interval_seconds=0.01)
    try:
        response = submit_command(
            created_run.id,
            RunCommandCreateRequest(
                command_type="SET_SPEED",
                payload={"id": "A0", "speed_kt": 420},
            ),
            db_session,
            orphaned_registry,
            broadcast_hub,
            SESSION_ID,
        )
    finally:
        orphaned_registry.shutdown()

    assert response.command.status == "rejected"
    assert response.result.state == "rejected"
    assert "live recovery is not implemented yet" in response.result.rejected[0].reason


def test_run_state_and_trajectory_fall_back_to_checkpoint(
    db_session,
    session_registry,
    broadcast_hub,
):
    settings = get_settings()
    scenario = create_scenario_route(
        ScenarioCreateRequest(name="Checkpoint Scenario"),
        db_session,
        SESSION_ID,
    )
    created_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="Checkpoint Session"),
        db_session,
        SESSION_ID,
    )

    start_run(created_run.id, db_session, session_registry, SESSION_ID, settings)
    submit_command(
        created_run.id,
        RunCommandCreateRequest(
            command_type="ADD_AIRCRAFT",
            payload={"id": "AC902", "route": "UA612"},
        ),
        db_session,
        session_registry,
        broadcast_hub,
        SESSION_ID,
    )
    stop_run(created_run.id, db_session, session_registry, SESSION_ID)

    restarted_registry = SessionRegistry(update_interval_seconds=0.01)
    checkpoint_state = get_run_state(
        created_run.id, db_session, restarted_registry, SESSION_ID
    )

    assert checkpoint_state.source == "checkpoint"
    assert checkpoint_state.runtime_status == "stopped"
    assert checkpoint_state.metrics.aircraft_count >= 1
    assert any(item.id == "AC902" for item in checkpoint_state.aircraft)

    checkpoint_trajectory = get_run_trajectory(
        created_run.id,
        db_session,
        restarted_registry,
        SESSION_ID,
    )
    assert checkpoint_trajectory.runtime_status == "stopped"
    assert len(checkpoint_trajectory.tracks) == checkpoint_state.metrics.aircraft_count
    assert any(track.id == "AC902" for track in checkpoint_trajectory.tracks)

    export_response = export_run_csv(
        created_run.id, db_session, restarted_registry, SESSION_ID
    )
    export_csv = export_response.body.decode("utf-8")
    assert export_response.status_code == 200
    assert "AC902" in export_csv
    assert "route_id" in export_csv


def test_resume_requires_live_runtime_when_only_checkpoint_state_exists(
    db_session,
    session_registry,
):
    settings = get_settings()
    scenario = create_scenario_route(
        ScenarioCreateRequest(name="Resume Scenario"),
        db_session,
        SESSION_ID,
    )
    created_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="Resume Session"),
        db_session,
        SESSION_ID,
    )
    start_run(created_run.id, db_session, session_registry, SESSION_ID, settings)
    pause_run(created_run.id, db_session, session_registry, SESSION_ID)

    orphaned_registry = SessionRegistry(update_interval_seconds=0.01)
    try:
        with pytest.raises(HTTPException) as excinfo:
            resume_run(created_run.id, db_session, orphaned_registry, SESSION_ID)
    finally:
        orphaned_registry.shutdown()

    assert excinfo.value.status_code == 409
    assert "live recovery is not implemented yet" in excinfo.value.detail


def test_run_creation_rejected_past_concurrency_cap(db_session, session_registry):
    settings = get_settings()
    settings.max_concurrent_runs_per_session = 1

    scenario = create_scenario_route(
        ScenarioCreateRequest(name="Capacity Scenario"),
        db_session,
        SESSION_ID,
    )
    first_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="First Session"),
        db_session,
        SESSION_ID,
    )
    start_run(first_run.id, db_session, session_registry, SESSION_ID, settings)

    second_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="Second Session"),
        db_session,
        SESSION_ID,
    )
    with pytest.raises(HTTPException) as excinfo:
        start_run(second_run.id, db_session, session_registry, SESSION_ID, settings)

    assert excinfo.value.status_code == 429


def test_checkpoint_retention_prunes_older_checkpoints_per_run(
    db_session,
    broadcast_hub,
):
    scenario = create_scenario_route(
        ScenarioCreateRequest(name="Retention Scenario"),
        db_session,
        SESSION_ID,
    )
    created_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="Retention Session"),
        db_session,
        SESSION_ID,
    )
    retained_registry = SessionRegistry(
        update_interval_seconds=0.01,
        checkpoint_retention_per_run=3,
        broadcast_hub=broadcast_hub,
    )
    settings = get_settings()
    try:
        start_run(created_run.id, db_session, retained_registry, SESSION_ID, settings)
        pause_run(created_run.id, db_session, retained_registry, SESSION_ID)
        resume_run(created_run.id, db_session, retained_registry, SESSION_ID)
        stop_run(created_run.id, db_session, retained_registry, SESSION_ID)
    finally:
        retained_registry.shutdown()

    repository = RunCheckpointRepository(db_session)
    checkpoints = repository.list_for_run(created_run.id, newest_first=False)

    assert len(checkpoints) == 3
    assert checkpoints[-1].checkpoint_type == "stopped"
    assert "started" not in {checkpoint.checkpoint_type for checkpoint in checkpoints}
