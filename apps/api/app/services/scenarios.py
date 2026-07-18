"""Scenario service helpers."""

import json
import re
from pathlib import Path
from typing import Any

from airspacesim.io.contracts import (
    build_envelope,
    validate_scenario_aircraft,
    validate_scenario_airspace,
)
from airspacesim.settings import settings as library_settings
from sqlalchemy.orm import Session

from ..db.models import ScenarioRecord
from ..db.repositories import ScenarioRepository


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "scenario"


def _next_unique_slug(repository: ScenarioRepository, requested_slug: str) -> str:
    slug = requested_slug
    suffix = 2
    while repository.get_by_slug(slug) is not None:
        slug = f"{requested_slug}-{suffix}"
        suffix += 1
    return slug


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _default_scenario_airspace() -> dict[str, Any]:
    return _load_json(library_settings.DEFAULT_SCENARIO_AIRSPACE_FILE)


def _default_scenario_aircraft() -> dict[str, Any]:
    return _load_json(library_settings.DEFAULT_SCENARIO_AIRCRAFT_FILE)


def _normalize_contract_payload(
    payload: dict[str, Any] | None,
    *,
    schema_name: str,
    source: str,
    default_envelope: dict[str, Any],
) -> dict[str, Any]:
    if not payload:
        return default_envelope

    if payload.get("schema", {}).get("name") == schema_name and "data" in payload:
        return payload

    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return build_envelope(schema_name=schema_name, source=source, data=data)


def resolve_scenario_contracts(
    scenario: ScenarioRecord | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve stored scenario payloads into validated canonical envelopes."""

    default_airspace = _default_scenario_airspace()
    default_aircraft = _default_scenario_aircraft()

    airspace_payload = _normalize_contract_payload(
        scenario.airspace_payload if scenario is not None else None,
        schema_name="airspacesim.scenario_airspace",
        source="airspacesim.api.scenarios",
        default_envelope=default_airspace,
    )
    validate_scenario_airspace(airspace_payload)

    aircraft_payload = _normalize_contract_payload(
        scenario.aircraft_payload if scenario is not None else None,
        schema_name="airspacesim.scenario_aircraft",
        source="airspacesim.api.scenarios",
        default_envelope=default_aircraft,
    )
    route_ids = {route["id"] for route in airspace_payload["data"]["routes"]}
    validate_scenario_aircraft(aircraft_payload, route_ids=route_ids)
    return airspace_payload, aircraft_payload


def create_scenario(
    session: Session,
    *,
    session_id: str,
    user_id: str | None = None,
    name: str,
    description: str | None,
    airspace_payload: dict[str, Any],
    aircraft_payload: dict[str, Any],
    metadata_payload: dict[str, Any],
) -> ScenarioRecord:
    """Create a durable scenario definition with a stable unique slug."""

    repository = ScenarioRepository(session)
    slug = _next_unique_slug(repository, _slugify(name))
    normalized_airspace, normalized_aircraft = resolve_scenario_contracts(
        ScenarioRecord(
            slug=slug,
            name=name,
            description=description,
            airspace_payload=airspace_payload,
            aircraft_payload=aircraft_payload,
            metadata_payload=metadata_payload,
        )
    )
    scenario = ScenarioRecord(
        session_id=session_id,
        user_id=user_id,
        slug=slug,
        name=name,
        description=description,
        airspace_payload=normalized_airspace,
        aircraft_payload=normalized_aircraft,
        metadata_payload=metadata_payload,
    )
    return repository.create(scenario)


def update_scenario(
    session: Session,
    scenario: ScenarioRecord,
    *,
    name: str | None = None,
    description: str | None = None,
    airspace_payload: dict[str, Any] | None = None,
    aircraft_payload: dict[str, Any] | None = None,
    metadata_payload: dict[str, Any] | None = None,
) -> ScenarioRecord:
    """Update mutable scenario fields without changing the stable slug."""

    candidate_airspace_payload = (
        airspace_payload if airspace_payload is not None else scenario.airspace_payload
    )
    candidate_aircraft_payload = (
        aircraft_payload if aircraft_payload is not None else scenario.aircraft_payload
    )
    normalized_airspace, normalized_aircraft = resolve_scenario_contracts(
        ScenarioRecord(
            slug=scenario.slug,
            name=name or scenario.name,
            description=description if description is not None else scenario.description,
            airspace_payload=candidate_airspace_payload,
            aircraft_payload=candidate_aircraft_payload,
            metadata_payload=metadata_payload if metadata_payload is not None else scenario.metadata_payload,
        )
    )
    if name is not None:
        scenario.name = name
    if description is not None:
        scenario.description = description
    scenario.airspace_payload = normalized_airspace
    scenario.aircraft_payload = normalized_aircraft
    if metadata_payload is not None:
        scenario.metadata_payload = metadata_payload
    return ScenarioRepository(session).update(scenario)
