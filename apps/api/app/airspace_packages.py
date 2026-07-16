"""Helpers for reading airspace package manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import AIRSPACES_ROOT, PROJECT_ROOT


def read_json_object(path: Path) -> dict[str, Any] | None:
    """Read a JSON object from disk, returning None for invalid input."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def package_manifest_paths(airspaces_root: Path = AIRSPACES_ROOT) -> list[Path]:
    """Return all package manifest paths under an airspaces root."""

    if not airspaces_root.exists():
        return []
    return sorted(airspaces_root.glob("*/package.v1.json"))


def string_list(value: Any) -> list[str]:
    """Return a clean list of non-empty strings."""

    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def manifest_items(value: Any) -> list[dict[str, Any]]:
    """Return manifest item dictionaries from a list-like value."""

    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def repo_relative(path: Path) -> str:
    """Format a path relative to the repository root when possible."""

    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def resolve_package_file(package_dir: Path, relative_path: str) -> Path:
    """Resolve a package-relative path without allowing path escape."""

    candidate = (package_dir / relative_path).resolve()
    package_root = package_dir.resolve()
    if not candidate.is_relative_to(package_root):
        raise ValueError(f"Package path escapes the airspace package: {relative_path}")
    return candidate


def resolve_airspace_package_dir(airspace_id: str) -> Path:
    """Resolve an airspace id to its package directory without path escape."""

    candidate = (AIRSPACES_ROOT / airspace_id).resolve()
    airspaces_root = AIRSPACES_ROOT.resolve()
    if not candidate.is_relative_to(airspaces_root):
        raise ValueError(f"Airspace id escapes the airspaces root: {airspace_id}")
    return candidate


def normalize_package_manifest(
    manifest: dict[str, Any],
    package_dir: Path,
) -> dict[str, Any] | None:
    """Normalize the manifest fields used by the API and web app."""

    package_id = manifest.get("id")
    name = manifest.get("name")
    description = manifest.get("description")
    package_type = manifest.get("package_type")
    difficulty = manifest.get("difficulty")
    airspace_file = manifest.get("airspace_file")

    required_strings = (package_id, name, description, package_type, difficulty, airspace_file)
    if not all(isinstance(item, str) and item.strip() for item in required_strings):
        return None

    return {
        "id": package_id.strip(),
        "name": name.strip(),
        "description": description.strip(),
        "package_type": package_type.strip(),
        "service_types": string_list(manifest.get("service_types")),
        "difficulty": difficulty.strip(),
        "training_modes": string_list(manifest.get("training_modes")),
        "airspace_file": repo_relative(package_dir.joinpath(airspace_file)),
        "default_scenario": (
            manifest["default_scenario"].strip()
            if isinstance(manifest.get("default_scenario"), str)
            else None
        ),
        "map": manifest.get("map") if isinstance(manifest.get("map"), dict) else {},
        "scenarios": manifest_items(manifest.get("scenarios")),
        "lessons": manifest_items(manifest.get("lessons")),
    }


def find_manifest_item(
    manifest: dict[str, Any],
    *,
    collection: str,
    item_id: str,
) -> dict[str, Any] | None:
    """Find one item by id in a package manifest collection."""

    for item in manifest_items(manifest.get(collection)):
        if item.get("id") == item_id:
            return item
    return None


def default_scenario_id(manifest: dict[str, Any]) -> str | None:
    """Return the package default scenario id, if any."""

    if isinstance(manifest.get("default_scenario"), str):
        return manifest["default_scenario"]
    scenarios = manifest_items(manifest.get("scenarios"))
    first = scenarios[0] if scenarios else None
    if isinstance(first, dict) and isinstance(first.get("id"), str):
        return first["id"]
    return None


def scenario_id_from_lesson(
    manifest: dict[str, Any],
    lesson_id: str,
) -> str | None:
    """Return the scenario id referenced by a lesson manifest entry."""

    lesson = find_manifest_item(manifest, collection="lessons", item_id=lesson_id)
    if lesson and isinstance(lesson.get("scenario_id"), str):
        return lesson["scenario_id"]
    return None
