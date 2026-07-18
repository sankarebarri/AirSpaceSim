"""Retention sweep for anonymous run data (decision Q10).

Anonymous (guest) runs that ended more than `anonymous_run_retention_days`
ago are deleted, together with their commands/checkpoints (FK cascade) and
any practice scenarios left orphaned by the sweep. Runs owned by signed-in
users are never touched — authenticated history is persistent.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import RunRecord, ScenarioRecord

logger = logging.getLogger(__name__)

_TERMINAL_RUN_STATUSES = ("stopped",)


def sweep_expired_anonymous_runs(
    session: Session, *, retention_days: int, now: datetime | None = None
) -> dict[str, int]:
    """Delete expired anonymous completed runs; returns deletion counts."""

    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=retention_days)

    expired_runs = list(
        session.scalars(
            select(RunRecord).where(
                RunRecord.user_id.is_(None),
                RunRecord.status.in_(_TERMINAL_RUN_STATUSES),
                RunRecord.ended_at.is_not(None),
                RunRecord.ended_at < cutoff,
            )
        )
    )
    candidate_scenario_ids = {
        run.scenario_id for run in expired_runs if run.scenario_id is not None
    }
    for run in expired_runs:
        session.delete(run)
    session.flush()

    orphaned_scenarios = 0
    for scenario_id in candidate_scenario_ids:
        still_referenced = session.scalar(
            select(RunRecord.id).where(RunRecord.scenario_id == scenario_id).limit(1)
        )
        if still_referenced is not None:
            continue
        scenario = session.get(ScenarioRecord, scenario_id)
        if scenario is not None and scenario.user_id is None:
            session.delete(scenario)
            orphaned_scenarios += 1

    session.commit()
    if expired_runs or orphaned_scenarios:
        logger.info(
            "Retention sweep removed %d anonymous runs and %d orphaned scenarios "
            "older than %d days.",
            len(expired_runs),
            orphaned_scenarios,
            retention_days,
        )
    return {"runs": len(expired_runs), "scenarios": orphaned_scenarios}


class RetentionSweeper:
    """Background thread running the retention sweep on an interval."""

    def __init__(
        self,
        session_factory,
        *,
        retention_days: int,
        interval_seconds: float,
    ) -> None:
        self._session_factory = session_factory
        self._retention_days = retention_days
        self._interval_seconds = max(float(interval_seconds), 60.0)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._run, name="airspacesim-retention", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def sweep_once(self) -> dict[str, int]:
        session = self._session_factory()
        try:
            return sweep_expired_anonymous_runs(
                session, retention_days=self._retention_days
            )
        finally:
            session.close()

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval_seconds):
            try:
                self.sweep_once()
            except Exception:
                logger.exception("Retention sweep failed; will retry next interval.")
