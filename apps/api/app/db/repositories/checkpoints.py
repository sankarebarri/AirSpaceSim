"""Checkpoint repository helpers."""

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from ..models import RunCheckpointRecord


class RunCheckpointRepository:
    """Repository for durable run checkpoint snapshots."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, checkpoint: RunCheckpointRecord) -> RunCheckpointRecord:
        self.session.add(checkpoint)
        self.session.commit()
        self.session.refresh(checkpoint)
        return checkpoint

    def list_for_run(
        self,
        run_id: str,
        *,
        newest_first: bool = True,
    ) -> list[RunCheckpointRecord]:
        ordering = (
            desc(RunCheckpointRecord.created_at),
            desc(RunCheckpointRecord.id),
        )
        if not newest_first:
            ordering = (
                asc(RunCheckpointRecord.created_at),
                asc(RunCheckpointRecord.id),
            )
        statement = (
            select(RunCheckpointRecord)
            .where(RunCheckpointRecord.run_id == run_id)
            .order_by(*ordering)
        )
        return list(self.session.scalars(statement))

    def count_for_run(self, run_id: str) -> int:
        return len(self.list_for_run(run_id))

    def latest_for_run(self, run_id: str) -> RunCheckpointRecord | None:
        statement = (
            select(RunCheckpointRecord)
            .where(RunCheckpointRecord.run_id == run_id)
            .order_by(
                desc(RunCheckpointRecord.created_at),
                desc(RunCheckpointRecord.id),
            )
            .limit(1)
        )
        return self.session.scalar(statement)

    def prune_for_run(self, run_id: str, *, keep_latest: int) -> int:
        if keep_latest <= 0:
            keep_latest = 1

        checkpoints = self.list_for_run(run_id)
        obsolete = checkpoints[keep_latest:]
        if not obsolete:
            return 0

        for checkpoint in obsolete:
            self.session.delete(checkpoint)
        self.session.commit()
        return len(obsolete)
