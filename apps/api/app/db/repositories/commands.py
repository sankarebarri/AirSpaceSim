"""Run command repository helpers."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import RunCommandRecord


class RunCommandRepository:
    """Repository for durable operator commands."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, command: RunCommandRecord) -> RunCommandRecord:
        self.session.add(command)
        self.session.commit()
        self.session.refresh(command)
        return command

    def update(self, command: RunCommandRecord) -> RunCommandRecord:
        self.session.add(command)
        self.session.commit()
        self.session.refresh(command)
        return command

    def list_for_run(self, run_id: str) -> list[RunCommandRecord]:
        statement = (
            select(RunCommandRecord)
            .where(RunCommandRecord.run_id == run_id)
            .order_by(RunCommandRecord.created_at.desc())
        )
        return list(self.session.scalars(statement))
