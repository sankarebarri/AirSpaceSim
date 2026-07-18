"""Run repository helpers."""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import RunRecord

_ACTIVE_RUN_STATUSES = ("running", "paused")


class RunRepository:
    """Repository for run persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _scope(session_id: str, user_id: str | None):
        """Visible to the browser session or, when signed in, to the account."""
        if user_id is None:
            return RunRecord.session_id == session_id
        return or_(
            RunRecord.user_id == user_id,
            and_(RunRecord.session_id == session_id, RunRecord.user_id.is_(None)),
        )

    def list(
        self, *, session_id: str, user_id: str | None = None
    ) -> list[RunRecord]:
        statement = (
            select(RunRecord)
            .options(selectinload(RunRecord.scenario))
            .where(self._scope(session_id, user_id))
            .order_by(RunRecord.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def get(
        self, run_id: str, *, session_id: str, user_id: str | None = None
    ) -> RunRecord | None:
        statement = (
            select(RunRecord)
            .options(selectinload(RunRecord.scenario), selectinload(RunRecord.commands))
            .where(RunRecord.id == run_id, self._scope(session_id, user_id))
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
