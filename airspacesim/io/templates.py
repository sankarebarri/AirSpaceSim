"""Shared scenario-template and environment validation.

Single source of truth for validating airspace geometry, scenario templates,
and aircraft plans against an environment and the aircraft-performance
database. Used by the hosted API (plain-language HTTP 400s), the seeding
script, and `scripts/validate_airspace_package.py`.

All validators return a list of plain-English error strings ("Aircraft NVR231
references unknown route 'X9'."), never raw exceptions — per the brief's
validation contract.
"""

from __future__ import annotations

import re
from typing import Any

from airspacesim.io.contracts import KNOWN_COMMAND_TYPES
from airspacesim.simulation.performance_database import (
    load_aircraft_performance_profiles,
)

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def load_aircraft_performance() -> dict:
    """Aircraft-performance profiles keyed by type (from the engine database)."""
    return load_aircraft_performance_profiles()


def format_validation_errors(errors: list[str]) -> str:
    return "Template validation failed:\n" + "\n".join(f"- {error}" for error in errors)


def is_semver(value: Any) -> bool:
    return isinstance(value, str) and bool(SEMVER_PATTERN.match(value.strip()))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_valid_lat_lon(position: Any) -> bool:
    return (
        isinstance(position, list)
        and len(position) >= 2
        and _is_number(position[0])
        and _is_number(position[1])
        and -90 <= float(position[0]) <= 90
        and -180 <= float(position[1]) <= 180
    )


def _read_point_position(point: Any) -> list[float] | None:
    if not isinstance(point, dict):
        return None
    coord = point.get("coord")
    if isinstance(coord, dict):
        position = coord.get("dd")
    else:
        position = point.get("position")
    if (
        isinstance(position, list)
        and len(position) >= 2
        and _is_number(position[0])
        and _is_number(position[1])
    ):
        return [float(position[0]), float(position[1])]
    return None


def airspace_point_ids(airspace: dict) -> set[str]:
    points = airspace.get("data", {}).get("points", {})
    if isinstance(points, dict):
        return {str(point_id) for point_id in points}
    return set()


def airspace_route_ids(airspace: dict) -> set[str]:
    routes = airspace.get("data", {}).get("routes", [])
    if not isinstance(routes, list):
        return set()
    return {
        str(route.get("id"))
        for route in routes
        if isinstance(route, dict) and route.get("id")
    }


def airspace_id(airspace: dict) -> str | None:
    metadata = airspace.get("metadata", {})
    if isinstance(metadata, dict):
        value = metadata.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def environment_version(airspace: dict) -> str | None:
    metadata = airspace.get("metadata", {})
    if isinstance(metadata, dict):
        value = metadata.get("version")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def merge_template_routes(airspace: dict, template: dict | None) -> dict:
    """Return a copy of the airspace with the template's extra_routes merged."""
    import json as _json

    merged = _json.loads(_json.dumps(airspace))
    routes = merged["data"]["routes"]
    existing_route_ids = {route["id"] for route in routes}
    template_airspace = template.get("airspace", {}) if template else {}
    extra_routes = template_airspace.get("extra_routes") or []
    routes.extend(
        route for route in extra_routes if route.get("id") not in existing_route_ids
    )
    return merged


# ------------------------------------------------------- airspace geometry


def validate_airspace_points(airspace: dict, errors: list[str]) -> None:
    points = airspace.get("data", {}).get("points", {})
    if not isinstance(points, dict) or not points:
        errors.append("airspace.data.points must be a non-empty object.")
        return

    for point_id, point in points.items():
        point_path = f"airspace.points.{point_id}"
        if not isinstance(point_id, str) or not point_id.strip():
            errors.append("airspace point IDs must be non-empty strings.")
            continue
        position = _read_point_position(point)
        if not _is_valid_lat_lon(position):
            errors.append(f"{point_path} must have valid coord.dd [lat, lon].")


def validate_airspace_boundaries(airspace: dict, errors: list[str]) -> None:
    point_ids = airspace_point_ids(airspace)
    boundaries = airspace.get("data", {}).get("airspaces", [])
    if not isinstance(boundaries, list):
        errors.append("airspace.data.airspaces must be a list.")
        return

    boundary_ids: set[str] = set()
    for index, boundary in enumerate(boundaries, start=1):
        boundary_path = f"airspace.airspaces[{index}]"
        if not isinstance(boundary, dict):
            errors.append(f"{boundary_path} must be an object.")
            continue

        boundary_id = boundary.get("id")
        if not isinstance(boundary_id, str) or not boundary_id.strip():
            errors.append(f"{boundary_path} is missing id.")
        elif boundary_id in boundary_ids:
            errors.append(f"{boundary_path} duplicates airspace id '{boundary_id}'.")
        else:
            boundary_ids.add(boundary_id)

        boundary_type = str(boundary.get("type") or "").strip().lower()
        if boundary_type == "circle":
            center_point_id = boundary.get("center_point_id")
            radius_nm = boundary.get("radius_nm")
            if not isinstance(center_point_id, str) or center_point_id not in point_ids:
                errors.append(
                    f"{boundary_path} circle references unknown center_point_id "
                    f"'{center_point_id}'."
                )
            if not _is_number(radius_nm) or float(radius_nm) <= 0:
                errors.append(f"{boundary_path} circle radius_nm must be > 0.")
        elif boundary_type == "polygon":
            points = boundary.get("points")
            if not isinstance(points, list) or len(points) < 3:
                errors.append(f"{boundary_path} polygon must have at least 3 points.")
                continue
            for point_index, position in enumerate(points, start=1):
                if not _is_valid_lat_lon(position):
                    errors.append(
                        f"{boundary_path} polygon point {point_index} must be [lat, lon]."
                    )
        elif boundary_type == "sector":
            center_point_id = boundary.get("center_point_id")
            inner_radius_nm = boundary.get("inner_radius_nm", 0)
            outer_radius_nm = boundary.get("outer_radius_nm")
            start_radial = boundary.get("start_radial")
            end_radial = boundary.get("end_radial")
            if not isinstance(center_point_id, str) or center_point_id not in point_ids:
                errors.append(
                    f"{boundary_path} sector references unknown center_point_id "
                    f"'{center_point_id}'."
                )
            if not _is_number(inner_radius_nm) or float(inner_radius_nm) < 0:
                errors.append(f"{boundary_path} sector inner_radius_nm must be >= 0.")
            if not _is_number(outer_radius_nm) or float(outer_radius_nm) <= 0:
                errors.append(f"{boundary_path} sector outer_radius_nm must be > 0.")
            if (
                _is_number(inner_radius_nm)
                and _is_number(outer_radius_nm)
                and float(inner_radius_nm) >= float(outer_radius_nm)
            ):
                errors.append(
                    f"{boundary_path} sector outer_radius_nm must exceed inner_radius_nm."
                )
            for radial_name, radial_value in (
                ("start_radial", start_radial),
                ("end_radial", end_radial),
            ):
                if not _is_number(radial_value) or not 0 <= float(radial_value) < 360:
                    errors.append(f"{boundary_path} sector {radial_name} must be 0-359.")
        else:
            errors.append(
                f"{boundary_path} has unsupported type '{boundary.get('type')}'."
            )


def validate_airspace_routes(airspace: dict, errors: list[str]) -> None:
    point_ids = airspace_point_ids(airspace)
    route_ids: set[str] = set()
    routes = airspace.get("data", {}).get("routes", [])
    if not isinstance(routes, list):
        errors.append("airspace.data.routes must be a list.")
        return

    for index, route in enumerate(routes, start=1):
        route_path = f"airspace.routes[{index}]"
        if not isinstance(route, dict):
            errors.append(f"{route_path} must be an object.")
            continue

        route_id = route.get("id")
        if not isinstance(route_id, str) or not route_id.strip():
            errors.append(f"{route_path} is missing id.")
        elif route_id in route_ids:
            errors.append(f"{route_path} duplicates route id '{route_id}'.")
        else:
            route_ids.add(route_id)

        waypoint_ids = route.get("waypoint_ids")
        if not isinstance(waypoint_ids, list) or len(waypoint_ids) < 2:
            errors.append(f"{route_path} must have at least two waypoint_ids.")
            continue

        for waypoint_id in waypoint_ids:
            if not isinstance(waypoint_id, str) or not waypoint_id.strip():
                errors.append(f"{route_path} has an invalid waypoint id.")
            elif waypoint_id not in point_ids:
                errors.append(
                    f"{route_path} references unknown waypoint '{waypoint_id}'."
                )


def validate_airspace_geometry(airspace: dict) -> list[str]:
    errors: list[str] = []
    validate_airspace_points(airspace, errors)
    validate_airspace_boundaries(airspace, errors)
    validate_airspace_routes(airspace, errors)
    return errors


# ------------------------------------------------------------ aircraft plan


def default_speed_for_type(aircraft_type: str, performance_db: dict) -> int:
    return int(performance_db[aircraft_type]["speed"]["default_cruise_kt"])


def speed_limits_for_type(
    aircraft_type: str, performance_db: dict
) -> tuple[float, float]:
    speed = performance_db[aircraft_type]["speed"]
    minimum = float(speed["min_clean_kt"])
    maximum = max(
        float(speed["max_operating_kt"]),
        float(speed["default_cruise_kt"]) * 1.5,
    )
    return minimum, maximum


def max_flight_level_for_type(aircraft_type: str, performance_db: dict) -> int:
    return int(round(float(performance_db[aircraft_type]["limits"]["max_fl"])))


def validate_aircraft_plan(
    aircraft_items: list[dict],
    route_ids: set[str],
    performance_db: dict,
    errors: list[str],
    *,
    path_prefix: str,
) -> None:
    seen_ids: set[str] = set()
    seen_callsigns: set[str] = set()

    for index, item in enumerate(aircraft_items, start=1):
        item_path = f"{path_prefix}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object.")
            continue

        aircraft_id = item.get("aircraft_id") or item.get("id")
        if not isinstance(aircraft_id, str) or not aircraft_id.strip():
            errors.append(f"{item_path} is missing id.")
            aircraft_id_label = item_path
        else:
            aircraft_id_label = aircraft_id
            if aircraft_id in seen_ids:
                errors.append(f"{item_path} duplicates aircraft id '{aircraft_id}'.")
            seen_ids.add(aircraft_id)

        callsign = item.get("callsign") or aircraft_id
        if not isinstance(callsign, str) or not callsign.strip():
            errors.append(f"{aircraft_id_label} has an invalid callsign.")
        else:
            normalized_callsign = callsign.strip().upper()
            if normalized_callsign in seen_callsigns:
                errors.append(f"{aircraft_id_label} duplicates callsign '{callsign}'.")
            seen_callsigns.add(normalized_callsign)

        aircraft_type = str(item.get("aircraft_type") or "B737").strip().upper()
        if aircraft_type not in performance_db:
            known_types = ", ".join(sorted(performance_db))
            errors.append(
                f"{aircraft_id_label} has unknown aircraft_type '{aircraft_type}'. "
                f"Known types: {known_types}."
            )
            continue

        route_id = item.get("route_id")
        if not isinstance(route_id, str) or not route_id.strip():
            errors.append(f"{aircraft_id_label} is missing route_id.")
        elif route_id not in route_ids:
            errors.append(f"{aircraft_id_label} references unknown route '{route_id}'.")

        speed_kt = item.get(
            "speed_kt",
            default_speed_for_type(aircraft_type, performance_db),
        )
        if not _is_number(speed_kt):
            errors.append(f"{aircraft_id_label} speed_kt must be a number.")
        else:
            minimum_speed, maximum_speed = speed_limits_for_type(
                aircraft_type,
                performance_db,
            )
            if float(speed_kt) < minimum_speed or float(speed_kt) > maximum_speed:
                errors.append(
                    f"{aircraft_id_label} speed_kt {float(speed_kt):.1f} outside "
                    f"{aircraft_type} range {minimum_speed:.1f}-{maximum_speed:.1f} kt."
                )

        flight_level = item.get("flight_level", 350)
        if not _is_number(flight_level):
            errors.append(f"{aircraft_id_label} flight_level must be a number.")
        else:
            max_flight_level = max_flight_level_for_type(
                aircraft_type,
                performance_db,
            )
            rounded_flight_level = int(round(float(flight_level)))
            if rounded_flight_level < 0:
                errors.append(f"{aircraft_id_label} flight_level must be >= 0.")
            elif rounded_flight_level > max_flight_level:
                errors.append(
                    f"{aircraft_id_label} flight_level FL{rounded_flight_level} "
                    f"exceeds {aircraft_type} max FL{max_flight_level}."
                )

        appear_after_seconds = item.get("appear_after_seconds", 0)
        if not _is_number(appear_after_seconds):
            errors.append(f"{aircraft_id_label} appear_after_seconds must be a number.")
        elif float(appear_after_seconds) < 0:
            errors.append(f"{aircraft_id_label} appear_after_seconds must be >= 0.")

        metadata = item.get("metadata", {})
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{aircraft_id_label} metadata must be an object.")


# ------------------------------------------------------- scenario template


def _validate_template_metadata(template: dict, errors: list[str]) -> None:
    version = template.get("version")
    if version is not None and not is_semver(version):
        errors.append(
            f"Template version '{version}' must be semantic (for example 1.0.0)."
        )

    metadata = template.get("metadata")
    if metadata is None or not isinstance(metadata, dict):
        return
    for section_name in ("practice", "simulate"):
        section = metadata.get(section_name)
        if not isinstance(section, dict):
            continue
        active_commands = section.get("active_commands")
        if active_commands is None:
            continue
        if not isinstance(active_commands, list):
            errors.append(f"metadata.{section_name}.active_commands must be a list.")
            continue
        for command in active_commands:
            if command not in KNOWN_COMMAND_TYPES:
                known = ", ".join(sorted(KNOWN_COMMAND_TYPES))
                errors.append(
                    f"metadata.{section_name}.active_commands contains unsupported "
                    f"command '{command}'. Supported commands: {known}."
                )


def validate_scenario_template(
    template: dict | None,
    airspace: dict,
    aircraft: Any,
    performance_db: dict | None = None,
) -> list[str]:
    """Validate a scenario template (or a bare aircraft plan) against an airspace.

    `airspace` should already include any template extra_routes (see
    `merge_template_routes`). Returns plain-English errors; empty means valid.
    """
    if performance_db is None:
        performance_db = load_aircraft_performance()

    errors: list[str] = []
    if template:
        expected_airspace_id = template.get("airspace_id")
        selected_airspace_id = airspace_id(airspace)
        if (
            isinstance(expected_airspace_id, str)
            and expected_airspace_id.strip()
            and selected_airspace_id
            and expected_airspace_id.strip() != selected_airspace_id
        ):
            errors.append(
                f"Template expects airspace_id '{expected_airspace_id.strip()}' "
                f"but selected airspace is '{selected_airspace_id}'."
            )
        _validate_template_metadata(template, errors)

    errors.extend(validate_airspace_geometry(airspace))

    if not isinstance(aircraft, list) or not aircraft:
        errors.append(
            "Template must contain a non-empty aircraft list."
            if template
            else "Built-in demo plan must contain a non-empty aircraft list."
        )
    else:
        validate_aircraft_plan(
            aircraft,
            airspace_route_ids(airspace),
            performance_db,
            errors,
            path_prefix="aircraft" if template else "demo_aircraft",
        )
    return errors
