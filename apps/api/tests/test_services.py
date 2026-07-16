import pytest
from fastapi import HTTPException

from app.airspace_packages import resolve_airspace_package_dir
from app.services.practice_runs import create_practice_run
from app.services.runs import (
    RUN_STATUS_RUNNING,
    RUN_STATUS_STOPPED,
    create_run,
    missing_runtime_detail,
    pause_run,
    record_run_command,
    resume_run,
    start_run,
    stop_run,
)
from app.services.airspaces import list_airspace_packages
from app.services.scenarios import create_scenario, update_scenario

SESSION_ID = "test-session-a"


def test_create_scenario_assigns_unique_slug_and_normalizes_contracts(db_session):
    first = create_scenario(
        db_session,
        session_id=SESSION_ID,
        name="Demo Scenario",
        description="Baseline scenario",
        airspace_payload={},
        aircraft_payload={},
        metadata_payload={"seed": "demo"},
    )
    second = create_scenario(
        db_session,
        session_id=SESSION_ID,
        name="Demo Scenario",
        description=None,
        airspace_payload={},
        aircraft_payload={},
        metadata_payload={},
    )

    assert first.slug == "demo-scenario"
    assert second.slug == "demo-scenario-2"
    assert first.airspace_payload["schema"]["name"] == "airspacesim.scenario_airspace"
    assert first.aircraft_payload["schema"]["name"] == "airspacesim.scenario_aircraft"


def test_list_airspace_packages_reads_package_manifests():
    packages = list_airspace_packages()
    package_by_id = {package["id"]: package for package in packages}

    assert "gao_demo" in package_by_id
    assert "training_alpha" in package_by_id
    assert package_by_id["gao_demo"]["default_scenario"] == "mixed_traffic_demo"
    assert package_by_id["training_alpha"]["lessons"][0]["id"] == (
        "enroute_heading_vs_radial_intro"
    )


def test_update_scenario_preserves_slug_and_updates_mutable_fields(db_session):
    scenario = create_scenario(
        db_session,
        session_id=SESSION_ID,
        name="Update Scenario",
        description="Before",
        airspace_payload={},
        aircraft_payload={},
        metadata_payload={"seed": "before"},
    )

    updated = update_scenario(
        db_session,
        scenario,
        name="Updated Scenario",
        description="After",
        metadata_payload={"seed": "after"},
    )

    assert updated.slug == "update-scenario"
    assert updated.name == "Updated Scenario"
    assert updated.description == "After"
    assert updated.metadata_payload == {"seed": "after"}


def test_create_run_uses_attached_scenario_name_by_default(db_session):
    scenario = create_scenario(
        db_session,
        session_id=SESSION_ID,
        name="Morning Flow",
        description=None,
        airspace_payload={},
        aircraft_payload={},
        metadata_payload={},
    )

    run = create_run(db_session, session_id=SESSION_ID, scenario_id=scenario.id)

    assert run.scenario_id == scenario.id
    assert run.name == "Morning Flow Run"
    assert run.status == "draft"


def test_create_run_rejects_unknown_scenario(db_session):
    with pytest.raises(HTTPException) as excinfo:
        create_run(db_session, session_id=SESSION_ID, scenario_id="missing-scenario")

    assert excinfo.value.status_code == 404
    assert "Scenario not found" in excinfo.value.detail


def test_create_run_rejects_scenario_owned_by_another_session(db_session):
    scenario = create_scenario(
        db_session,
        session_id=SESSION_ID,
        name="Other Session Flow",
        description=None,
        airspace_payload={},
        aircraft_payload={},
        metadata_payload={},
    )

    with pytest.raises(HTTPException) as excinfo:
        create_run(db_session, session_id="test-session-b", scenario_id=scenario.id)

    assert excinfo.value.status_code == 404


def test_run_lifecycle_transitions_set_started_and_ended_timestamps_once(db_session):
    run = create_run(db_session, session_id=SESSION_ID, name="Lifecycle Run")

    started = start_run(db_session, run)
    first_started_at = started.started_at
    assert started.status == RUN_STATUS_RUNNING
    assert first_started_at is not None

    paused = pause_run(db_session, started)
    assert paused.status == "paused"

    resumed = resume_run(db_session, paused)
    assert resumed.status == RUN_STATUS_RUNNING
    assert resumed.started_at == first_started_at

    stopped = stop_run(db_session, resumed)
    assert stopped.status == RUN_STATUS_STOPPED
    assert stopped.started_at == first_started_at
    assert stopped.ended_at is not None


def test_record_run_command_persists_default_status_and_payload(db_session):
    run = create_run(db_session, session_id=SESSION_ID, name="Command Service Run")

    command = record_run_command(
        db_session,
        run=run,
        command_type="SET_SPEED",
        payload={"aircraft_id": "AC500", "speed_kt": 410},
    )

    assert command.run_id == run.id
    assert command.command_type == "SET_SPEED"
    assert command.status == "accepted"
    assert command.payload == {"aircraft_id": "AC500", "speed_kt": 410}


def test_missing_runtime_detail_matches_run_state_and_checkpoint_context(db_session):
    run = create_run(db_session, session_id=SESSION_ID, name="Recovery Run")

    run.status = RUN_STATUS_RUNNING
    assert (
        missing_runtime_detail(run, has_checkpoint=True)
        == f"Run {run.id} has persisted checkpoint state, but live recovery is not implemented yet."
    )

    run.status = RUN_STATUS_STOPPED
    assert (
        missing_runtime_detail(run)
        == f"Run {run.id} is stopped and cannot accept live runtime operations."
    )

    run.status = "draft"
    assert missing_runtime_detail(run) == f"Runtime session not active for run: {run.id}"


def test_resolve_airspace_package_dir_rejects_traversal():
    with pytest.raises(ValueError):
        resolve_airspace_package_dir("../../etc")


def test_resolve_airspace_package_dir_accepts_known_package():
    resolved = resolve_airspace_package_dir("training_alpha")
    assert resolved.name == "training_alpha"


def test_create_practice_run_rejects_traversal_airspace_id(db_session):
    with pytest.raises(HTTPException) as excinfo:
        create_practice_run(
            db_session,
            session_id=SESSION_ID,
            airspace_id="../../etc",
        )

    assert excinfo.value.status_code == 400
