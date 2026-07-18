"""Scenario management routes."""

from fastapi import APIRouter, HTTPException, status

from ....db.repositories import ScenarioRepository
from ....dependencies import (
    DbSessionDependency,
    OptionalUserDependency,
    SessionIdDependency,
)
from ....schemas.scenarios import (
    ScenarioCreateRequest,
    ScenarioListResponse,
    ScenarioResponse,
    ScenarioUpdateRequest,
)
from ....services import create_scenario, update_scenario

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=ScenarioListResponse)
def list_scenarios(
    db: DbSessionDependency,
    session_id: SessionIdDependency,
    user: OptionalUserDependency = None,
) -> ScenarioListResponse:
    """List scenarios for the browser session and, when signed in, the account."""

    items = ScenarioRepository(db).list(
        session_id=session_id, user_id=user.id if user else None
    )
    return ScenarioListResponse(items=[ScenarioResponse.model_validate(item) for item in items])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ScenarioResponse)
def create_scenario_route(
    payload: ScenarioCreateRequest,
    db: DbSessionDependency,
    session_id: SessionIdDependency,
    user: OptionalUserDependency = None,
) -> ScenarioResponse:
    """Create and persist a scenario shell."""

    scenario = create_scenario(
        db,
        session_id=session_id,
        user_id=user.id if user else None,
        name=payload.name,
        description=payload.description,
        airspace_payload=payload.airspace_payload,
        aircraft_payload=payload.aircraft_payload,
        metadata_payload=payload.metadata_payload,
    )
    return ScenarioResponse.model_validate(scenario)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: str,
    db: DbSessionDependency,
    session_id: SessionIdDependency,
    user: OptionalUserDependency = None,
) -> ScenarioResponse:
    """Fetch a persisted scenario by id."""

    scenario = ScenarioRepository(db).get(
        scenario_id, session_id=session_id, user_id=user.id if user else None
    )
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario not found: {scenario_id}",
        )
    return ScenarioResponse.model_validate(scenario)


@router.patch("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario_route(
    scenario_id: str,
    payload: ScenarioUpdateRequest,
    db: DbSessionDependency,
    session_id: SessionIdDependency,
) -> ScenarioResponse:
    """Update a persisted scenario."""

    repository = ScenarioRepository(db)
    scenario = repository.get(scenario_id, session_id=session_id)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario not found: {scenario_id}",
        )
    updated = update_scenario(
        db,
        scenario,
        name=payload.name,
        description=payload.description,
        airspace_payload=payload.airspace_payload,
        aircraft_payload=payload.aircraft_payload,
        metadata_payload=payload.metadata_payload,
    )
    return ScenarioResponse.model_validate(updated)
