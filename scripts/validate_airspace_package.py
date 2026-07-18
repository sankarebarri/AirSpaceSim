#!/usr/bin/env python3
"""Validate an AirSpaceSim airspace package folder."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# File loading helpers stay in the seed script; validation logic is shared
# in airspacesim.io.templates (single source of truth).
from seed_hosted_demo import (  # noqa: E402 (after sys.path setup)
    PROJECT_ROOT,
    _load_airspace,
    _load_template,
)
from airspacesim.io.templates import (  # noqa: E402 (after sys.path setup)
    airspace_id as _airspace_id,
    environment_version,
    format_validation_errors as _format_validation_errors,
    is_semver,
    load_aircraft_performance as _load_aircraft_performance,
    merge_template_routes,
    validate_scenario_template,
)

VALID_PACKAGE_TYPES = {
    "real_world",
    "adapted_real_world",
    "fictional",
    "classroom",
}
VALID_SERVICE_TYPES = {
    "enroute",
    "approach",
    "aerodrome",
    "radar",
    "apron",
}
VALID_DIFFICULTIES = {
    "beginner",
    "intermediate",
    "advanced",
}
VALID_TRAINING_MODES = {
    "solo_guided",
    "solo_free_practice",
    "instructor_led",
    "two_person",
}


def _repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _load_json_object(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"{_repo_relative(path)} could not be read: {exc}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"{_repo_relative(path)} is not valid JSON: {exc}")
        return None

    if not isinstance(payload, dict):
        errors.append(f"{_repo_relative(path)} root must be a JSON object.")
        return None
    return payload


def _scenario_template_paths(package_dir: Path) -> list[Path]:
    scenarios_dir = package_dir / "scenarios"
    if not scenarios_dir.exists():
        return []
    return sorted(scenarios_dir.glob("*.json"))


def _lesson_paths(package_dir: Path) -> list[Path]:
    lessons_dir = package_dir / "lessons"
    if not lessons_dir.exists():
        return []
    return sorted(lessons_dir.glob("*.json"))


def _is_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _validate_string_list(
    payload: dict[str, Any],
    field: str,
    allowed_values: set[str],
    label: str,
    errors: list[str],
) -> set[str]:
    values = payload.get(field)
    if not isinstance(values, list) or not values:
        errors.append(f"{label} {field} must be a non-empty list.")
        return set()

    normalized: set[str] = set()
    for index, value in enumerate(values, start=1):
        if not _is_string(value):
            errors.append(f"{label} {field}[{index}] must be a non-empty string.")
            continue
        normalized_value = value.strip()
        if normalized_value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            errors.append(
                f"{label} {field}[{index}] has unsupported value "
                f"'{normalized_value}'. Allowed: {allowed}."
            )
        normalized.add(normalized_value)
    return normalized


def _resolve_package_path(package_dir: Path, value: Any) -> Path | None:
    if not _is_string(value):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.resolve()
    return (package_dir / candidate).resolve()


def _validate_manifest_items(
    *,
    manifest: dict[str, Any],
    field: str,
    package_dir: Path,
    existing_paths: set[Path],
    allowed_service_types: set[str],
    allowed_training_modes: set[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    items = manifest.get(field, [])
    manifest_label = _repo_relative(package_dir / "package.v1.json")
    if not isinstance(items, list):
        errors.append(f"{manifest_label} {field} must be a list.")
        return {}

    seen_ids: set[str] = set()
    output: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items, start=1):
        item_path = f"{manifest_label} {field}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object.")
            continue

        item_id = item.get("id")
        if not _is_string(item_id):
            errors.append(f"{item_path} is missing id.")
        elif item_id in seen_ids:
            errors.append(f"{item_path} duplicates id '{item_id}'.")
        else:
            seen_ids.add(item_id)
            output[item_id] = item

        for required_field in ("title", "path"):
            if not _is_string(item.get(required_field)):
                errors.append(f"{item_path} is missing required string field '{required_field}'.")

        resolved_path = _resolve_package_path(package_dir, item.get("path"))
        if resolved_path is None or resolved_path not in existing_paths:
            errors.append(f"{item_path} references missing path '{item.get('path')}'.")

        service_type = item.get("service_type")
        if _is_string(service_type):
            if service_type not in allowed_service_types:
                errors.append(
                    f"{item_path} service_type '{service_type}' is not declared "
                    "in package service_types."
                )

        training_mode = item.get("training_mode")
        if _is_string(training_mode):
            if training_mode not in allowed_training_modes:
                errors.append(
                    f"{item_path} training_mode '{training_mode}' is not declared "
                    "in package training_modes."
                )

        difficulty = item.get("difficulty") or item.get("level")
        if _is_string(difficulty) and difficulty not in VALID_DIFFICULTIES:
            allowed = ", ".join(sorted(VALID_DIFFICULTIES))
            errors.append(f"{item_path} difficulty/level must be one of: {allowed}.")

        duration = item.get("duration_minutes")
        if duration is not None and not _is_positive_number(duration):
            errors.append(f"{item_path} duration_minutes must be a positive number.")

    return output


def _validate_package_manifest(
    package_dir: Path,
    airspace_path: Path,
    selected_airspace_id: str | None,
    scenario_paths: list[Path],
    lesson_paths: list[Path],
    errors: list[str],
) -> dict[str, Any] | None:
    manifest_path = package_dir / "package.v1.json"
    manifest_label = _repo_relative(manifest_path)
    if not manifest_path.exists():
        errors.append(f"Missing package manifest: {manifest_label}")
        return None

    manifest = _load_json_object(manifest_path, errors)
    if manifest is None:
        return None

    schema = manifest.get("schema")
    if not isinstance(schema, dict):
        errors.append(f"{manifest_label} schema must be an object.")
    else:
        if schema.get("name") != "airspacesim.airspace_package_manifest":
            errors.append(
                f"{manifest_label} schema.name must be "
                "'airspacesim.airspace_package_manifest'."
            )
        if schema.get("version") != "1.0":
            errors.append(f"{manifest_label} schema.version must be '1.0'.")

    for field in ("id", "name", "description", "package_type", "airspace_file"):
        if not _is_string(manifest.get(field)):
            errors.append(f"{manifest_label} is missing required string field '{field}'.")

    if not is_semver(manifest.get("version")):
        errors.append(
            f"{manifest_label} version must be a semantic version string "
            "(for example 1.0.0)."
        )

    manifest_id = manifest.get("id")
    if _is_string(manifest_id):
        if manifest_id != package_dir.name:
            errors.append(
                f"{manifest_label} id '{manifest_id}' must match package directory "
                f"'{package_dir.name}'."
            )
        if selected_airspace_id and manifest_id != selected_airspace_id:
            errors.append(
                f"{manifest_label} id '{manifest_id}' does not match airspace metadata "
                f"id '{selected_airspace_id}'."
            )

    package_type = manifest.get("package_type")
    if _is_string(package_type) and package_type not in VALID_PACKAGE_TYPES:
        allowed = ", ".join(sorted(VALID_PACKAGE_TYPES))
        errors.append(f"{manifest_label} package_type must be one of: {allowed}.")

    airspace_file_path = _resolve_package_path(package_dir, manifest.get("airspace_file"))
    if airspace_file_path != airspace_path.resolve():
        errors.append(
            f"{manifest_label} airspace_file must point to "
            f"{_repo_relative(airspace_path)}."
        )

    service_types = _validate_string_list(
        manifest,
        "service_types",
        VALID_SERVICE_TYPES,
        manifest_label,
        errors,
    )
    training_modes = _validate_string_list(
        manifest,
        "training_modes",
        VALID_TRAINING_MODES,
        manifest_label,
        errors,
    )

    difficulty = manifest.get("difficulty")
    if _is_string(difficulty) and difficulty not in VALID_DIFFICULTIES:
        allowed = ", ".join(sorted(VALID_DIFFICULTIES))
        errors.append(f"{manifest_label} difficulty must be one of: {allowed}.")

    scenario_path_set = {path.resolve() for path in scenario_paths}
    lesson_path_set = {path.resolve() for path in lesson_paths}
    scenario_items = _validate_manifest_items(
        manifest=manifest,
        field="scenarios",
        package_dir=package_dir,
        existing_paths=scenario_path_set,
        allowed_service_types=service_types,
        allowed_training_modes=training_modes,
        errors=errors,
    )
    lesson_items = _validate_manifest_items(
        manifest=manifest,
        field="lessons",
        package_dir=package_dir,
        existing_paths=lesson_path_set,
        allowed_service_types=service_types,
        allowed_training_modes=training_modes,
        errors=errors,
    )

    default_scenario = manifest.get("default_scenario")
    if scenario_items:
        if not _is_string(default_scenario):
            errors.append(f"{manifest_label} is missing default_scenario.")
        elif default_scenario not in scenario_items:
            errors.append(
                f"{manifest_label} default_scenario '{default_scenario}' is not "
                "listed in scenarios."
            )

    for lesson_id, lesson in lesson_items.items():
        scenario_id = lesson.get("scenario_id")
        if _is_string(scenario_id) and scenario_id not in scenario_items:
            errors.append(
                f"{manifest_label} lesson '{lesson_id}' references unknown "
                f"scenario_id '{scenario_id}'."
            )

    return manifest


def _resolve_lesson_scenario_reference(package_dir: Path, lesson_path: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate

    candidates = [
        package_dir / "scenarios" / value,
        package_dir / value,
        lesson_path.parent / value,
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def _scenario_references_from_lesson(lesson: dict[str, Any]) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    for index, step in enumerate(lesson.get("lesson_steps", []), start=1):
        if isinstance(step, dict) and isinstance(step.get("scenario_template"), str):
            references.append(
                (f"lesson_steps[{index}].scenario_template", step["scenario_template"])
            )

    exercise = lesson.get("exercise")
    if isinstance(exercise, dict) and isinstance(exercise.get("scenario_template"), str):
        references.append(("exercise.scenario_template", exercise["scenario_template"]))
    return references


def _validate_lesson(
    lesson_path: Path,
    package_dir: Path,
    scenario_paths: set[Path],
    errors: list[str],
) -> None:
    lesson = _load_json_object(lesson_path, errors)
    if lesson is None:
        return

    lesson_label = _repo_relative(lesson_path)
    required_string_fields = (
        "id",
        "title",
        "service_type",
        "training_mode",
        "level",
    )
    for field in required_string_fields:
        if not isinstance(lesson.get(field), str) or not lesson[field].strip():
            errors.append(f"{lesson_label} is missing required string field '{field}'.")

    duration = lesson.get("duration_minutes")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
        errors.append(f"{lesson_label} duration_minutes must be a positive number.")

    lesson_steps = lesson.get("lesson_steps")
    if not isinstance(lesson_steps, list) or not lesson_steps:
        errors.append(f"{lesson_label} lesson_steps must be a non-empty list.")

    references = _scenario_references_from_lesson(lesson)
    for field_path, reference in references:
        resolved = _resolve_lesson_scenario_reference(package_dir, lesson_path, reference)
        if resolved not in scenario_paths:
            errors.append(
                f"{lesson_label} {field_path} references missing scenario template "
                f"'{reference}'."
            )


def validate_package(package_dir: Path, *, require_scenarios: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    package_dir = package_dir.resolve()
    airspace_path = package_dir / "airspace.v1.json"

    if not package_dir.exists() or not package_dir.is_dir():
        errors.append(f"Airspace package directory not found: {_repo_relative(package_dir)}")
        return {"errors": errors, "scenario_count": 0, "lesson_count": 0}

    if not airspace_path.exists():
        errors.append(f"Missing package airspace file: {_repo_relative(airspace_path)}")
        return {"errors": errors, "scenario_count": 0, "lesson_count": 0}

    performance_db = _load_aircraft_performance()
    scenario_paths = _scenario_template_paths(package_dir)
    lesson_paths = _lesson_paths(package_dir)

    try:
        airspace, _ = _load_airspace(str(airspace_path))
    except SystemExit as exc:
        errors.append(str(exc))
        return {
            "errors": errors,
            "scenario_count": len(scenario_paths),
            "lesson_count": len(lesson_paths),
        }

    package_id = package_dir.name
    selected_airspace_id = _airspace_id(airspace)
    if selected_airspace_id and selected_airspace_id != package_id:
        errors.append(
            f"Package directory '{package_id}' does not match airspace metadata id "
            f"'{selected_airspace_id}'."
        )

    if not is_semver(environment_version(airspace)):
        errors.append(
            f"{_repo_relative(airspace_path)} metadata.version must be a semantic "
            "version string (for example 1.0.0)."
        )

    manifest = _validate_package_manifest(
        package_dir,
        airspace_path,
        selected_airspace_id,
        scenario_paths,
        lesson_paths,
        errors,
    )

    if require_scenarios and not scenario_paths:
        errors.append(f"{_repo_relative(package_dir)} must contain at least one scenario.")

    for scenario_path in scenario_paths:
        try:
            template = _load_template(str(scenario_path))
            assert template is not None
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{_repo_relative(scenario_path)} could not be loaded: {exc}")
            continue
        if not is_semver(template.get("version")):
            errors.append(
                f"{_repo_relative(scenario_path)} version must be a semantic "
                "version string (for example 1.0.0)."
            )
        scenario_airspace = merge_template_routes(airspace, template)
        for error in validate_scenario_template(
            template,
            scenario_airspace,
            template.get("aircraft"),
            performance_db,
        ):
            errors.append(f"{_repo_relative(scenario_path)}: {error}")

    scenario_path_set = {path.resolve() for path in scenario_paths}
    for lesson_path in lesson_paths:
        _validate_lesson(lesson_path.resolve(), package_dir, scenario_path_set, errors)

    return {
        "errors": errors,
        "airspace_id": selected_airspace_id or package_id,
        "package_name": manifest.get("name") if isinstance(manifest, dict) else package_id,
        "package_type": (
            manifest.get("package_type") if isinstance(manifest, dict) else "unknown"
        ),
        "scenario_count": len(scenario_paths),
        "lesson_count": len(lesson_paths),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an AirSpaceSim airspace package.")
    parser.add_argument(
        "package_dir",
        help="Airspace package directory, for example airspaces/training_alpha.",
    )
    parser.add_argument(
        "--require-scenarios",
        action="store_true",
        help="Fail when the package has no scenarios/*.json templates.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_package(
        Path(args.package_dir),
        require_scenarios=args.require_scenarios,
    )
    errors = result["errors"]
    if errors:
        print(_format_validation_errors(errors))
        return 1

    print(f"Airspace package validation passed: {args.package_dir}")
    print(f"Airspace: {result['airspace_id']}")
    print(f"Package: {result['package_name']} ({result['package_type']})")
    print(f"Scenarios: {result['scenario_count']}")
    print(f"Lessons: {result['lesson_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
