"""Practice-run creation from airspace package manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from airspacesim.io import build_envelope, normalize_scenario_airspace_payload
from airspacesim.io.templates import (
    environment_version,
    load_aircraft_performance,
    validate_scenario_template,
)

from ..airspace_packages import (
    default_scenario_id,
    find_manifest_item,
    read_json_object,
    repo_relative,
    resolve_airspace_package_dir,
    resolve_package_file,
    scenario_id_from_lesson,
)
from .runs import create_run
from .scenarios import create_scenario


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = read_json_object(path)
    if payload is None and not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"JSON file not found: {repo_relative(path)}",
        )
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read JSON object: {repo_relative(path)}",
        )
    return payload


def _resolve_package_file(package_dir: Path, relative_path: str) -> Path:
    try:
        candidate = resolve_package_file(package_dir, relative_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if not candidate.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package file not found: {relative_path}",
        )
    return candidate


def _get_package_manifest(airspace_id: str) -> tuple[dict[str, Any], Path]:
    try:
        package_dir = resolve_airspace_package_dir(airspace_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    manifest_path = package_dir / "package.v1.json"
    if not manifest_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Airspace package not found: {airspace_id}",
        )
    manifest = _load_json_object(manifest_path)
    if manifest.get("id") != airspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Airspace package id mismatch: {airspace_id}",
        )
    return manifest, package_dir


def _find_manifest_item(
    manifest: dict[str, Any],
    *,
    collection: str,
    item_id: str,
) -> dict[str, Any]:
    item = find_manifest_item(manifest, collection=collection, item_id=item_id)
    if item is not None:
        return item
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{collection[:-1].title()} not found in package: {item_id}",
    )


def _default_scenario_id(manifest: dict[str, Any]) -> str:
    scenario_id = default_scenario_id(manifest)
    if scenario_id is not None:
        return scenario_id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Airspace package does not define a default scenario.",
    )


def _scenario_id_from_lesson(manifest: dict[str, Any], lesson_id: str) -> str:
    scenario_id = scenario_id_from_lesson(manifest, lesson_id)
    if scenario_id is not None:
        return scenario_id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Lesson does not reference a scenario: {lesson_id}",
    )


def _normalize_airspace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return normalize_scenario_airspace_payload(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def _build_airspace_payload(
    manifest: dict[str, Any],
    package_dir: Path,
    template: dict[str, Any],
) -> dict[str, Any]:
    airspace_file = manifest.get("airspace_file")
    if not isinstance(airspace_file, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Airspace package is missing airspace_file.",
        )
    airspace = _normalize_airspace_payload(
        _load_json_object(_resolve_package_file(package_dir, airspace_file))
    )
    extra_routes = template.get("airspace", {}).get("extra_routes")
    if isinstance(extra_routes, list):
        existing_route_ids = {
            route.get("id")
            for route in airspace["data"]["routes"]
            if isinstance(route, dict)
        }
        airspace["data"]["routes"].extend(
            route
            for route in extra_routes
            if isinstance(route, dict) and route.get("id") not in existing_route_ids
        )
    return airspace


def _build_aircraft_payload(template: dict[str, Any]) -> dict[str, Any]:
    aircraft_items = template.get("aircraft")
    if not isinstance(aircraft_items, list) or not aircraft_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scenario template must contain aircraft.",
        )
    aircraft = []
    for item in aircraft_items:
        if not isinstance(item, dict):
            continue
        aircraft_id = item.get("aircraft_id") or item.get("id")
        if not isinstance(aircraft_id, str) or not aircraft_id.strip():
            continue
        entry_seconds = item.get(
            "entry_time_seconds", item.get("appear_after_seconds", 0)
        )
        aircraft.append(
            {
                "id": aircraft_id.strip(),
                "callsign": str(item.get("callsign") or aircraft_id).strip(),
                "aircraft_type": str(item.get("aircraft_type") or "B737").strip().upper(),
                "route_id": str(item.get("route_id") or "").strip(),
                "speed_kt": float(item.get("speed_kt", 420)),
                "flight_level": int(round(float(item.get("flight_level", 350)))),
                "appear_after_seconds": (
                    float(entry_seconds)
                    if isinstance(entry_seconds, (int, float)) and entry_seconds > 0
                    else 0
                ),
            }
        )
    return build_envelope(
        schema_name="airspacesim.scenario_aircraft",
        source="airspacesim.api.practice_runs",
        data={"aircraft": aircraft},
    )


def create_practice_run(
    session: Session,
    *,
    session_id: str,
    airspace_id: str,
    scenario_id: str | None = None,
    lesson_id: str | None = None,
    name: str | None = None,
):
    """Create a scenario/run from package data for live lesson practice."""

    manifest, package_dir = _get_package_manifest(airspace_id)
    resolved_scenario_id = (
        scenario_id
        or (_scenario_id_from_lesson(manifest, lesson_id) if lesson_id else None)
        or _default_scenario_id(manifest)
    )
    scenario_item = _find_manifest_item(
        manifest,
        collection="scenarios",
        item_id=resolved_scenario_id,
    )
    scenario_path = scenario_item.get("path")
    if not isinstance(scenario_path, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scenario is missing a path: {resolved_scenario_id}",
        )
    template = _load_json_object(_resolve_package_file(package_dir, scenario_path))
    if template.get("airspace_id") not in (None, airspace_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Scenario template expects airspace_id '{template.get('airspace_id')}' "
                f"but '{airspace_id}' was requested."
            ),
        )

    airspace_payload = _build_airspace_payload(manifest, package_dir, template)
    validation_errors = validate_scenario_template(
        template,
        airspace_payload,
        template.get("aircraft"),
        load_aircraft_performance(),
    )
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Scenario template '{resolved_scenario_id}' failed validation: "
                + " ".join(validation_errors)
            ),
        )

    template_metadata = (
        template.get("metadata") if isinstance(template.get("metadata"), dict) else {}
    )
    scenario_name = (
        name
        or template_metadata.get("name")
        or scenario_item.get("title")
        or f"{airspace_id} Practice"
    )
    scenario = create_scenario(
        session,
        session_id=session_id,
        name=str(scenario_name),
        description=str(
            template_metadata.get("description")
            or scenario_item.get("description")
            or "Practice scenario created from an airspace package."
        ),
        airspace_payload=airspace_payload,
        aircraft_payload=_build_aircraft_payload(template),
        metadata_payload={
            "source": "airspacesim.api.practice_runs",
            "airspace_id": airspace_id,
            "scenario_template_id": resolved_scenario_id,
            "lesson_id": lesson_id,
            # Exact content versions used by this run, for reproducibility
            # (brief: run records must identify scenario/environment versions).
            "content_versions": {
                "airspace_id": airspace_id,
                "environment_version": environment_version(airspace_payload),
                "scenario_template_id": resolved_scenario_id,
                "scenario_template_version": (
                    template.get("version")
                    if isinstance(template.get("version"), str)
                    else None
                ),
            },
            **(
                {"practice": template_metadata["practice"]}
                if isinstance(template_metadata.get("practice"), dict)
                else {}
            ),
            **(
                {"simulate": template_metadata["simulate"]}
                if isinstance(template_metadata.get("simulate"), dict)
                else {}
            ),
            **(
                {"learn": template_metadata["learn"]}
                if isinstance(template_metadata.get("learn"), dict)
                else {}
            ),
            **(
                {"traffic_relationship": template_metadata["traffic_relationship"]}
                if isinstance(template_metadata.get("traffic_relationship"), dict)
                else {}
            ),
        },
    )
    return create_run(
        session,
        session_id=session_id,
        scenario_id=scenario.id,
        name=name or f"{scenario.name} Practice Run",
    )
