"""Run repository helpers."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..models import RunRecord

_ACTIVE_RUN_STATUSES = ("running", "paused")


class RunRepository:
    """Repository for run persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    def list(self, *, session_id: str) -> list[RunRecord]:
        statement = (
            select(RunRecord)
            .options(selectinload(RunRecord.scenario))
            .where(RunRecord.session_id == session_id)
            .order_by(RunRecord.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def get(self, run_id: str, *, session_id: str) -> RunRecord | None:
        statement = (
            select(RunRecord)
            .options(selectinload(RunRecord.scenario), selectinload(RunRecord.commands))
            .where(RunRecord.id == run_id, RunRecord.session_id == session_id)
        )
        return self.session.scalar(statement)

    def count_active_for_session(self, session_id: str) -> int:
        statement = select(func.count()).where(
            RunRecord.session_id == session_id,
            RunRecord.status.in_(_ACTIVE_RUN_STATUSES),
        )
        return int(self.session.scalar(statement) or 0)

    def create(self, run: RunRecord) -> RunRecord:
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def update(self, run: RunRecord) -> RunRecord:
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run
