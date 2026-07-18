"""Phase 6: anonymous-run retention sweep (decision Q10, default 14 days)."""

from datetime import datetime, timedelta, timezone

from app.db.models import RunRecord, ScenarioRecord, UserRecord
from app.security import hash_password
from app.services.retention import sweep_expired_anonymous_runs

NOW = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)


def _run(session, *, name, user_id=None, status="stopped", ended_days_ago=None,
         scenario_id=None):
    run = RunRecord(
        session_id="retention-session",
        user_id=user_id,
        scenario_id=scenario_id,
        name=name,
        status=status,
        ended_at=(NOW - timedelta(days=ended_days_ago)) if ended_days_ago else None,
    )
    session.add(run)
    session.commit()
    return run


def test_sweep_deletes_only_expired_anonymous_completed_runs(db_session):
    user = UserRecord(
        email="keeper@example.test", password_hash=hash_password("training-pass-1")
    )
    db_session.add(user)
    scenario = ScenarioRecord(
        session_id="retention-session",
        slug="retention-scenario",
        name="Retention Scenario",
        airspace_payload={},
        aircraft_payload={},
        metadata_payload={},
    )
    db_session.add(scenario)
    db_session.commit()

    expired_anonymous = _run(
        db_session, name="old guest", ended_days_ago=20, scenario_id=scenario.id
    )
    recent_anonymous = _run(db_session, name="recent guest", ended_days_ago=3)
    active_anonymous = _run(db_session, name="active guest", status="running")
    user_run = _run(
        db_session, name="user history", user_id=user.id, ended_days_ago=200
    )

    counts = sweep_expired_anonymous_runs(db_session, retention_days=14, now=NOW)

    assert counts == {"runs": 1, "scenarios": 1}
    assert db_session.get(RunRecord, expired_anonymous.id) is None
    assert db_session.get(ScenarioRecord, scenario.id) is None  # orphaned
    assert db_session.get(RunRecord, recent_anonymous.id) is not None
    assert db_session.get(RunRecord, active_anonymous.id) is not None
    # Signed-in history is persistent regardless of age.
    assert db_session.get(RunRecord, user_run.id) is not None


def test_sweep_keeps_scenarios_still_referenced_by_other_runs(db_session):
    scenario = ScenarioRecord(
        session_id="retention-session",
        slug="shared-scenario",
        name="Shared Scenario",
        airspace_payload={},
        aircraft_payload={},
        metadata_payload={},
    )
    db_session.add(scenario)
    db_session.commit()

    _run(db_session, name="old", ended_days_ago=30, scenario_id=scenario.id)
    keeper = _run(db_session, name="fresh", ended_days_ago=1, scenario_id=scenario.id)

    counts = sweep_expired_anonymous_runs(db_session, retention_days=14, now=NOW)

    assert counts["runs"] == 1
    assert db_session.get(ScenarioRecord, scenario.id) is not None
    assert db_session.get(RunRecord, keeper.id) is not None
