"""Scenario repository helpers."""

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from ..models import ScenarioRecord


class ScenarioRepository:
    """Repository for scenario persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _scope(session_id: str, user_id: str | None):
        if user_id is None:
            return ScenarioRecord.session_id == session_id
        return or_(
            ScenarioRecord.user_id == user_id,
            and_(
                ScenarioRecord.session_id == session_id,
                ScenarioRecord.user_id.is_(None),
            ),
        )

    def list(
        self, *, session_id: str, user_id: str | None = None
    ) -> list[ScenarioRecord]:
        statement = (
            select(ScenarioRecord)
            .where(self._scope(session_id, user_id))
            .order_by(ScenarioRecord.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def get(
        self, scenario_id: str, *, session_id: str, user_id: str | None = None
    ) -> ScenarioRecord | None:
        statement = select(ScenarioRecord).where(
            ScenarioRecord.id == scenario_id,
            self._scope(session_id, user_id),
        )
        return self.session.scalar(statement)

    def get_by_slug(self, slug: str) -> ScenarioRecord | None:
        statement = select(ScenarioRecord).where(ScenarioRecord.slug == slug)
        return self.session.scalar(statement)

    def create(self, scenario: ScenarioRecord) -> ScenarioRecord:
        self.session.add(scenario)
        self.session.commit()
        self.session.refresh(scenario)
        return scenario

    def update(self, scenario: ScenarioRecord) -> ScenarioRecord:
        self.session.add(scenario)
        self.session.commit()
        self.session.refresh(scenario)
        return scenario
