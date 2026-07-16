from datetime import timedelta

from app.db.models import RunCommandRecord, RunRecord, ScenarioRecord
from app.db.repositories import RunCommandRepository, RunRepository, ScenarioRepository
from app.db.models.scenario import utcnow

SESSION_ID = "test-session-a"


def test_scenario_repository_lists_newest_first_and_gets_by_slug(db_session):
    repository = ScenarioRepository(db_session)
    base_time = utcnow()

    older = repository.create(
        ScenarioRecord(
            session_id=SESSION_ID,
            slug="older-scenario",
            name="Older Scenario",
            created_at=base_time,
            updated_at=base_time,
        )
    )
    newer = repository.create(
        ScenarioRecord(
            session_id=SESSION_ID,
            slug="newer-scenario",
            name="Newer Scenario",
            created_at=base_time + timedelta(minutes=1),
            updated_at=base_time + timedelta(minutes=1),
        )
    )

    items = repository.list(session_id=SESSION_ID)

    assert [item.id for item in items] == [newer.id, older.id]
    assert repository.get_by_slug("older-scenario").id == older.id


def test_scenario_repository_get_is_scoped_to_session(db_session):
    repository = ScenarioRepository(db_session)
    scenario = repository.create(
        ScenarioRecord(
            session_id=SESSION_ID,
            slug="scoped-scenario",
            name="Scoped Scenario",
        )
    )

    assert repository.get(scenario.id, session_id=SESSION_ID) is not None
    assert repository.get(scenario.id, session_id="test-session-b") is None


def test_run_repository_lists_newest_first_and_loads_relations(db_session):
    scenario_repository = ScenarioRepository(db_session)
    run_repository = RunRepository(db_session)
    command_repository = RunCommandRepository(db_session)
    base_time = utcnow()

    scenario = scenario_repository.create(
        ScenarioRecord(
            session_id=SESSION_ID,
            slug="repo-scenario",
            name="Repository Scenario",
            created_at=base_time,
            updated_at=base_time,
        )
    )
    older_run = run_repository.create(
        RunRecord(
            session_id=SESSION_ID,
            scenario_id=scenario.id,
            name="Older Run",
            created_at=base_time,
            updated_at=base_time,
        )
    )
    newer_run = run_repository.create(
        RunRecord(
            session_id=SESSION_ID,
            scenario_id=scenario.id,
            name="Newer Run",
            created_at=base_time + timedelta(minutes=1),
            updated_at=base_time + timedelta(minutes=1),
        )
    )
    command_repository.create(
        RunCommandRecord(
            run_id=newer_run.id,
            command_type="SET_SPEED",
            payload={"aircraft_id": "AC100", "speed_kt": 420},
            created_at=base_time + timedelta(minutes=2),
        )
    )

    items = run_repository.list(session_id=SESSION_ID)
    fetched = run_repository.get(newer_run.id, session_id=SESSION_ID)

    assert [item.id for item in items] == [newer_run.id, older_run.id]
    assert fetched is not None
    assert fetched.scenario.id == scenario.id
    assert len(fetched.commands) == 1
    assert fetched.commands[0].command_type == "SET_SPEED"


def test_run_repository_get_is_scoped_to_session(db_session):
    run_repository = RunRepository(db_session)
    run = run_repository.create(RunRecord(session_id=SESSION_ID, name="Scoped Run"))

    assert run_repository.get(run.id, session_id=SESSION_ID) is not None
    assert run_repository.get(run.id, session_id="test-session-b") is None


def test_run_repository_counts_active_runs_for_session(db_session):
    run_repository = RunRepository(db_session)
    running = run_repository.create(
        RunRecord(session_id=SESSION_ID, name="Running", status="running")
    )
    run_repository.create(RunRecord(session_id=SESSION_ID, name="Draft", status="draft"))
    run_repository.create(
        RunRecord(session_id="test-session-b", name="Other Session", status="running")
    )

    assert run_repository.count_active_for_session(SESSION_ID) == 1
    assert running.status == "running"


def test_run_command_repository_lists_newest_first_for_one_run(db_session):
    run_repository = RunRepository(db_session)
    command_repository = RunCommandRepository(db_session)
    base_time = utcnow()

    run = run_repository.create(
        RunRecord(
            session_id=SESSION_ID,
            name="Command Run",
            created_at=base_time,
            updated_at=base_time,
        )
    )
    other_run = run_repository.create(
        RunRecord(
            session_id=SESSION_ID,
            name="Other Run",
            created_at=base_time + timedelta(minutes=1),
            updated_at=base_time + timedelta(minutes=1),
        )
    )
    older_command = command_repository.create(
        RunCommandRecord(
            run_id=run.id,
            command_type="SET_FL",
            payload={"aircraft_id": "AC200", "flight_level": 300},
            created_at=base_time,
        )
    )
    newer_command = command_repository.create(
        RunCommandRecord(
            run_id=run.id,
            command_type="SET_SPEED",
            payload={"aircraft_id": "AC200", "speed_kt": 430},
            created_at=base_time + timedelta(minutes=2),
        )
    )
    command_repository.create(
        RunCommandRecord(
            run_id=other_run.id,
            command_type="SET_SPEED",
            payload={"aircraft_id": "AC300", "speed_kt": 390},
            created_at=base_time + timedelta(minutes=3),
        )
    )

    items = command_repository.list_for_run(run.id)

    assert [item.id for item in items] == [newer_command.id, older_command.id]
    assert {item.run_id for item in items} == {run.id}
