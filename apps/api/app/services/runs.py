"""Run lifecycle service helpers."""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..db.models import RunCommandRecord, RunRecord, ScenarioRecord
from ..db.repositories import RunCommandRepository, RunRepository, ScenarioRepository


RUN_STATUS_DRAFT = "draft"
RUN_STATUS_RUNNING = "running"
RUN_STATUS_PAUSED = "paused"
RUN_STATUS_STOPPED = "stopped"
RUN_STATUSES_REQUIRING_LIVE_RUNTIME = {
    RUN_STATUS_RUNNING,
    RUN_STATUS_PAUSED,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_run(
    session: Session,
    *,
    session_id: str,
    scenario_id: str | None = None,
    name: str | None = None,
) -> RunRecord:
    """Create a durable run shell, optionally attached to a stored scenario."""

    scenario: ScenarioRecord | None = None
    if scenario_id is not None:
        scenario = ScenarioRepository(session).get(scenario_id, session_id=session_id)
        if scenario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario not found: {scenario_id}",
            )

    run = RunRecord(
        session_id=session_id,
        scenario_id=scenario.id if scenario is not None else None,
        name=name or (f"{scenario.name} Run" if scenario is not None else None),
    )
    return RunRepository(session).create(run)


def transition_run_status(session: Session, run: RunRecord, target_status: str) -> RunRecord:
    """Apply a guarded lifecycle transition to a run."""

    return _transition_run_status(
        session,
        run,
        target_status=target_status,
        allowed_sources={
            RUN_STATUS_RUNNING: {RUN_STATUS_DRAFT, RUN_STATUS_PAUSED},
            RUN_STATUS_PAUSED: {RUN_STATUS_RUNNING},
            RUN_STATUS_STOPPED: {RUN_STATUS_DRAFT, RUN_STATUS_RUNNING, RUN_STATUS_PAUSED},
        }[target_status],
    )


def _transition_run_status(
    session: Session,
    run: RunRecord,
    *,
    target_status: str,
    allowed_sources: set[str],
) -> RunRecord:
    if run.status not in allowed_sources:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition run {run.id} from {run.status} to {target_status}.",
        )

    now = _utcnow()
    run.status = target_status
    if target_status == RUN_STATUS_RUNNING and run.started_at is None:
        run.started_at = now
    if target_status == RUN_STATUS_STOPPED:
        run.ended_at = now
    return RunRepository(session).update(run)


def start_run(session: Session, run: RunRecord) -> RunRecord:
    """Start a draft run."""

    return _transition_run_status(
        session,
        run,
        target_status=RUN_STATUS_RUNNING,
        allowed_sources={RUN_STATUS_DRAFT},
    )


def pause_run(session: Session, run: RunRecord) -> RunRecord:
    """Pause a running run."""

    return _transition_run_status(
        session,
        run,
        target_status=RUN_STATUS_PAUSED,
        allowed_sources={RUN_STATUS_RUNNING},
    )


def resume_run(session: Session, run: RunRecord) -> RunRecord:
    """Resume a paused run."""

    return _transition_run_status(
        session,
        run,
        target_status=RUN_STATUS_RUNNING,
        allowed_sources={RUN_STATUS_PAUSED},
    )


def stop_run(session: Session, run: RunRecord) -> RunRecord:
    """Stop a draft, running, or paused run."""

    return _transition_run_status(
        session,
        run,
        target_status=RUN_STATUS_STOPPED,
        allowed_sources={RUN_STATUS_DRAFT, RUN_STATUS_RUNNING, RUN_STATUS_PAUSED},
    )


def record_run_command(
    session: Session,
    *,
    run: RunRecord,
    command_type: str,
    payload: dict[str, Any],
) -> RunCommandRecord:
    """Persist an operator command against a run."""

    command = RunCommandRecord(
        run_id=run.id,
        command_type=command_type,
        payload=payload,
    )
    return RunCommandRepository(session).create(command)


def missing_runtime_detail(
    run: RunRecord,
    *,
    has_checkpoint: bool = False,
) -> str:
    """Describe why a live runtime operation cannot continue."""

    if run.status in RUN_STATUSES_REQUIRING_LIVE_RUNTIME and has_checkpoint:
        return (
            f"Run {run.id} has persisted checkpoint state, but live recovery is not "
            "implemented yet."
        )
    if run.status == RUN_STATUS_STOPPED:
        return f"Run {run.id} is stopped and cannot accept live runtime operations."
    return f"Runtime session not active for run: {run.id}"
