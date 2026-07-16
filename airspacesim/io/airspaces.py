"""Airspace payload normalization helpers."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any


DEFAULT_REFERENCE = {
    "datum": "WGS84",
    "earth_model": "spherical",
    "nm_to_m": 1852,
}


def _generated_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _metadata_with_defaults(
    payload: dict[str, Any],
    *,
    default_source: str,
    generated_utc: str | None,
) -> dict[str, Any]:
    metadata = (
        copy.deepcopy(payload.get("metadata"))
        if isinstance(payload.get("metadata"), dict)
        else {}
    )
    if not isinstance(metadata.get("source"), str):
        metadata["source"] = metadata.get("id") or default_source
    if not isinstance(metadata.get("generated_utc"), str):
        metadata["generated_utc"] = generated_utc or _generated_utc()
    return metadata


def _point_records_from_package(points: Any) -> dict[str, dict[str, Any]]:
    if isinstance(points, dict):
        return copy.deepcopy(points)
    if not isinstance(points, list):
        return {}

    point_records: dict[str, dict[str, Any]] = {}
    for point in points:
        if not isinstance(point, dict) or not isinstance(point.get("id"), str):
            continue
        point_id = point["id"]
        position = point.get("position") or point.get("coord", {}).get("dd")
        point_records[point_id] = {
            "type": point.get("type", "fix"),
            "name": point.get("name", point_id),
            "coord": {"dd": position},
            **({"ident": point["ident"]} if point.get("ident") else {}),
        }
    return point_records


def normalize_scenario_airspace_payload(
    payload: dict[str, Any],
    *,
    default_source: str = "airspace_package",
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Normalize canonical or package-style airspace JSON for scenarios."""

    if payload.get("schema", {}).get("name") == "airspacesim.scenario_airspace":
        normalized = copy.deepcopy(payload)
        normalized["metadata"] = _metadata_with_defaults(
            normalized,
            default_source=default_source,
            generated_utc=generated_utc,
        )
        return normalized

    points = payload.get("points")
    routes = payload.get("routes")
    airspaces = payload.get("airspaces")
    if points is None and routes is None and airspaces is None:
        raise ValueError("Airspace must contain data.points/routes or package points/routes.")

    return {
        "schema": {"name": "airspacesim.scenario_airspace", "version": "1.0"},
        "metadata": _metadata_with_defaults(
            payload,
            default_source=default_source,
            generated_utc=generated_utc,
        ),
        "data": {
            "reference": copy.deepcopy(payload.get("reference", DEFAULT_REFERENCE)),
            "points": _point_records_from_package(points),
            "routes": copy.deepcopy(routes) if isinstance(routes, list) else [],
            "airspaces": copy.deepcopy(airspaces) if isinstance(airspaces, list) else [],
        },
    }
