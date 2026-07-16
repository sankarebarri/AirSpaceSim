"""Airspace package discovery routes."""

from fastapi import APIRouter

from ....schemas.airspaces import AirspacePackageListResponse, AirspacePackageSummary
from ....services.airspaces import list_airspace_packages

router = APIRouter(prefix="/airspaces", tags=["airspaces"])


@router.get("", response_model=AirspacePackageListResponse)
def list_airspaces() -> AirspacePackageListResponse:
    """List discoverable airspace package manifests."""

    return AirspacePackageListResponse(
        items=[
            AirspacePackageSummary.model_validate(item)
            for item in list_airspace_packages()
        ]
    )
