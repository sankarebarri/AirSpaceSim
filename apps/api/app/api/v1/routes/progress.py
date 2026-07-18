"""Learning-progress routes (protected persistence for signed-in users).

Guests keep progress in browser storage (decision Q10); these routes reject
unauthenticated writes, which is exactly what authentication adds.
"""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from ....db.models import LearningProgressRecord
from ....dependencies import CurrentUserDependency, DbSessionDependency

router = APIRouter(prefix="/progress", tags=["progress"])


class ProgressEntryRequest(BaseModel):
    concept_id: str = Field(min_length=1, max_length=80)
    stage_key: str = Field(min_length=1, max_length=120)
    status: str = Field(default="completed", max_length=32)


class ProgressEntryResponse(BaseModel):
    concept_id: str
    stage_key: str
    status: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgressListResponse(BaseModel):
    items: list[ProgressEntryResponse]


@router.get("", response_model=ProgressListResponse)
def list_progress(
    user: CurrentUserDependency,
    db: DbSessionDependency,
) -> ProgressListResponse:
    """List the signed-in user's lesson progress."""

    entries = db.scalars(
        select(LearningProgressRecord)
        .where(LearningProgressRecord.user_id == user.id)
        .order_by(LearningProgressRecord.updated_at.desc())
    )
    return ProgressListResponse(
        items=[ProgressEntryResponse.model_validate(entry) for entry in entries]
    )


@router.put("", response_model=ProgressEntryResponse)
def upsert_progress(
    payload: ProgressEntryRequest,
    user: CurrentUserDependency,
    db: DbSessionDependency,
) -> ProgressEntryResponse:
    """Record (or update) one lesson/stage completion for the user."""

    entry = db.scalar(
        select(LearningProgressRecord).where(
            LearningProgressRecord.user_id == user.id,
            LearningProgressRecord.concept_id == payload.concept_id,
            LearningProgressRecord.stage_key == payload.stage_key,
        )
    )
    if entry is None:
        entry = LearningProgressRecord(
            user_id=user.id,
            concept_id=payload.concept_id,
            stage_key=payload.stage_key,
            status=payload.status,
        )
    else:
        entry.status = payload.status
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return ProgressEntryResponse.model_validate(entry)
