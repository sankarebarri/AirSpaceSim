"""Health and readiness routes."""

from fastapi import APIRouter
from sqlalchemy import text

from ....dependencies import DbSessionDependency, SettingsDependency
from ....schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck(
    settings: SettingsDependency,
    db: DbSessionDependency,
) -> HealthResponse:
    """Return a service heartbeat plus a minimal database readiness probe."""

    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", service=settings.app_name, database="ok")
