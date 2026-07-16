#!/usr/bin/env python3
"""Seed a hosted AirSpaceSim demo run with live aircraft."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from airspacesim.io import normalize_scenario_airspace_payload

DEFAULT_AIRSPACE_PATH = PROJECT_ROOT / "airspaces" / "gao_demo" / "airspace.v1.json"
LEGACY_DEFAULT_AIRSPACE_PATH = (
    PROJECT_ROOT / "airspacesim" / "data" / "scenario_airspace.v1.json"
)

# The API scopes every run/scenario to a client-generated session id (see
# apps/api/app/session_identity.py). Stable by default (not a fresh UUID per
# run) so a one-time `localStorage.setItem(...)` in the browser keeps working
# across repeated seeding instead of going stale on every reseed. Override
# with --session-id if you need to simulate a different client.
DEFAULT_SESSION_ID = "airspacesim-local-dev-demo"
SESSION_ID = DEFAULT_SESSION_ID
DEMO_RUN_NAME_PREFIX = "Hosted Demo Run "
ACTIVE_RUN_STATUSES = {"running", "paused"}


def _request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json", "X-Airspacesim-Session": SESSION_ID}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(
            f"HTTP {exc.code} while calling {method} {url}\n{body}"
        ) from exc
    except URLError as exc:
        raise SystemExit(
            f"Could not reach {url}. Is the API running?"
        ) from exc


def _stop_existing_demo_runs(api_base: str) -> int:
    response = _request_json("GET", f"{api_base}/api/v1/runs")
    stopped_count = 0
    for run in response.get("items", []):
        if not isinstance(run, dict):
            continue
        if run.get("status") not in ACTIVE_RUN_STATUSES:
            continue
        if not str(run.get("name", "")).startswith(DEMO_RUN_NAME_PREFIX):
            continue
        run_id = run.get("id")
        if not isinstance(run_id, str):
            continue
        _request_json("POST", f"{api_base}/api/v1/runs/{run_id}/stop")
        stopped_count += 1
    return stopped_count


def _timestamp_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _resolve_project_path(path: str | None, default_path: Path) -> Path:
    if path is None:
        return default_path
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


def _load_airspace(path: str | None = None) -> tuple[dict, Path]:
    airspace_path = _resolve_project_path(path, DEFAULT_AIRSPACE_PATH)
    if path is None and not airspace_path.exists():
        airspace_path = LEGACY_DEFAULT_AIRSPACE_PATH
    if not airspace_path.exists():
        raise SystemExit(f"Airspace file not found: {airspace_path}")

    payload = json.loads(airspace_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Airspace root must be a JSON object.")
    try:
        return normalize_scenario_airspace_payload(payload), airspace_path
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def _load_template(path: str | None) -> dict | None:
    if path is None:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Template root must be a JSON object.")
    return payload


def _load_aircraft_performance() -> dict:
    payload = json.loads(
        (PROJECT_ROOT / "airspacesim" / "data" / "aircraft_performance.v1.json")
        .read_text(encoding="utf-8")
    )
    return payload["data"]["aircraft_types"]


def _normalize_aircraft_type(value: object, performance_db: dict) -> str:
    aircraft_type = str(value or "B737").strip().upper()
    if aircraft_type not in performance_db:
        known_types = ", ".join(sorted(performance_db))
        raise SystemExit(
            f"Unknown aircraft_type '{aircraft_type}'. Known types: {known_types}"
        )
    return aircraft_type


def _default_speed_for_type(aircraft_type: str, performance_db: dict) -> int:
    return int(performance_db[aircraft_type]["speed"]["default_cruise_kt"])


def _speed_limits_for_type(aircraft_type: str, performance_db: dict) -> tuple[float, float]:
    speed = performance_db[aircraft_type]["speed"]
    minimum = float(speed["min_clean_kt"])
    maximum = max(
        float(speed["max_operating_kt"]),
        float(speed["default_cruise_kt"]) * 1.5,
    )
    return minimum, maximum


def _max_flight_level_for_type(aircraft_type: str, performance_db: dict) -> int:
    return int(round(float(performance_db[aircraft_type]["limits"]["max_fl"])))


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _format_validation_errors(errors: list[str]) -> str:
    return "Template validation failed:\n" + "\n".join(
        f"- {error}" for error in errors
    )


def _airspace_point_ids(airspace: dict) -> set[str]:
    points = airspace.get("data", {}).get("points", {})
    if isinstance(points, dict):
        return {str(point_id) for point_id in points}
    return set()


def _airspace_id(airspace: dict) -> str | None:
    metadata = airspace.get("metadata", {})
    if isinstance(metadata, dict):
        value = metadata.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _read_point_position(point: object) -> list[float] | None:
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


def _is_valid_lat_lon(position: object) -> bool:
    return (
        isinstance(position, list)
        and len(position) >= 2
        and _is_number(position[0])
        and _is_number(position[1])
        and -90 <= float(position[0]) <= 90
        and -180 <= float(position[1]) <= 180
    )


def _airspace_route_ids(airspace: dict) -> set[str]:
    routes = airspace.get("data", {}).get("routes", [])
    if not isinstance(routes, list):
        return set()
    return {
        str(route.get("id"))
        for route in routes
        if isinstance(route, dict) and route.get("id")
    }


def _validate_airspace_points(airspace: dict, errors: list[str]) -> None:
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


def _validate_airspace_boundaries(airspace: dict, errors: list[str]) -> None:
    point_ids = _airspace_point_ids(airspace)
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
                    errors.append(
                        f"{boundary_path} sector {radial_name} must be 0-359."
                    )
        else:
            errors.append(
                f"{boundary_path} has unsupported type '{boundary.get('type')}'."
            )


def _validate_airspace_routes(airspace: dict, errors: list[str]) -> None:
    point_ids = _airspace_point_ids(airspace)
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


def _validate_aircraft_plan(
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
            _default_speed_for_type(aircraft_type, performance_db),
        )
        if not _is_number(speed_kt):
            errors.append(f"{aircraft_id_label} speed_kt must be a number.")
        else:
            minimum_speed, maximum_speed = _speed_limits_for_type(
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
            max_flight_level = _max_flight_level_for_type(
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


def _validate_template_or_exit(
    template: dict | None,
    airspace: dict,
    aircraft: object,
    performance_db: dict,
) -> None:
    errors: list[str] = []
    if template:
        expected_airspace_id = template.get("airspace_id")
        selected_airspace_id = _airspace_id(airspace)
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
    _validate_airspace_points(airspace, errors)
    _validate_airspace_boundaries(airspace, errors)
    _validate_airspace_routes(airspace, errors)
    if not isinstance(aircraft, list) or not aircraft:
        errors.append(
            "Template must contain a non-empty aircraft list."
            if template
            else "Built-in demo plan must contain a non-empty aircraft list."
        )
    else:
        _validate_aircraft_plan(
            aircraft,
            _airspace_route_ids(airspace),
            performance_db,
            errors,
            path_prefix="aircraft" if template else "demo_aircraft",
        )
    if errors:
        raise SystemExit(_format_validation_errors(errors))


def _build_demo_airspace(base_airspace: dict, template: dict | None = None) -> dict:
    airspace = json.loads(json.dumps(base_airspace))
    routes = airspace["data"]["routes"]
    existing_route_ids = {route["id"] for route in routes}
    template_airspace = template.get("airspace", {}) if template else {}
    if template:
        overflight_routes = template_airspace.get("extra_routes") or []
    else:
        overflight_routes = [
            {
                "id": "OVF_NW_SE",
                "name": "Overflight NW-SE",
                "waypoint_ids": ["TAVIL", "GAO_VOR", "PILTI"],
            },
            {
                "id": "OVF_NE_SW",
                "name": "Overflight NE-SW",
                "waypoint_ids": ["TESTI", "GAO_VOR", "OPUGO"],
            },
            {
                "id": "OVF_N_S",
                "name": "Overflight N-S",
                "waypoint_ids": ["BIDUX", "GAO_VOR", "ARGAM"],
            },
        ]
    routes.extend(
        route for route in overflight_routes if route["id"] not in existing_route_ids
    )
    return airspace


def _scenario_aircraft_payload(aircraft: list[dict]) -> dict:
    scenario_aircraft = [
        {
            "id": item["aircraft_id"],
            "callsign": item["callsign"],
            "aircraft_type": item["aircraft_type"],
            "route_id": item["route_id"],
            "speed_kt": item["speed_kt"],
            "flight_level": item["flight_level"],
        }
        for item in aircraft
    ]
    return {
        "schema": {"name": "airspacesim.scenario_aircraft", "version": "1.0"},
        "metadata": {
            "source": "scripts.seed_hosted_demo",
            "generated_utc": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        },
        "data": {"aircraft": scenario_aircraft},
    }


def _build_demo_aircraft(performance_db: dict) -> list[dict]:
    route_plan = [
        ("UA612", "departure"),
        ("UG859", "arrival"),
        ("OVF_NW_SE", "overflight"),
        ("UR971", "departure"),
        ("UM629", "departure"),
        ("OVF_NE_SW", "overflight"),
        ("UA603", "departure"),
        ("UG859_ALT", "departure"),
        ("UT365", "departure"),
        ("OVF_N_S", "overflight"),
        ("UR981", "departure"),
        ("UM629_ALT", "departure"),
        ("UG859", "arrival"),
        ("UA612", "departure"),
        ("OVF_NW_SE", "overflight"),
        ("UR971", "departure"),
        ("UM629", "departure"),
        ("OVF_NE_SW", "overflight"),
        ("UA603", "departure"),
        ("UG859_ALT", "departure"),
        ("UT365", "departure"),
        ("OVF_N_S", "overflight"),
        ("UR981", "departure"),
        ("UM629_ALT", "departure"),
        ("UG859", "arrival"),
    ]
    aircraft_types = [
        "B737",
        "A320",
        "B738",
        "E190",
        "CRJ9",
        "A332",
        "B772",
        "AT72",
        "DH8D",
        "C208",
    ]
    flight_levels = [290, 310, 330, 350, 370, 390]
    aircraft = []
    for index, (route_id, flow_group) in enumerate(route_plan, start=1):
        prefix = {
            "arrival": "ARR",
            "departure": "DEP",
            "overflight": "OVF",
        }[flow_group]
        aircraft_type = aircraft_types[(index - 1) % len(aircraft_types)]
        requested_flight_level = flight_levels[(index - 1) % len(flight_levels)]
        flight_level = min(
            requested_flight_level,
            _max_flight_level_for_type(aircraft_type, performance_db),
        )
        aircraft.append(
            {
                "aircraft_id": f"AC{900 + index}",
                "callsign": f"{prefix}{index:02d}",
                "aircraft_type": aircraft_type,
                "route_id": route_id,
                "speed_kt": _default_speed_for_type(aircraft_type, performance_db),
                "flight_level": flight_level,
            }
        )
    return aircraft


def _build_template_aircraft(template: dict, performance_db: dict) -> list[dict]:
    aircraft_items = template.get("aircraft")
    if not isinstance(aircraft_items, list) or not aircraft_items:
        raise SystemExit("Template must contain a non-empty aircraft list.")

    aircraft = []
    seen_ids = set()
    for index, item in enumerate(aircraft_items, start=1):
        aircraft_id = item.get("aircraft_id") or item.get("id")
        if not aircraft_id:
            raise SystemExit(f"Template aircraft[{index}] is missing id.")
        if aircraft_id in seen_ids:
            raise SystemExit(f"Template aircraft id is duplicated: {aircraft_id}")
        seen_ids.add(aircraft_id)

        appear_after_seconds = float(item.get("appear_after_seconds", 0))
        if appear_after_seconds < 0:
            raise SystemExit(
                f"Template aircraft {aircraft_id} has negative appear_after_seconds."
            )

        aircraft_type = _normalize_aircraft_type(
            item.get("aircraft_type"),
            performance_db,
        )
        aircraft.append(
            {
                "aircraft_id": aircraft_id.strip(),
                "callsign": (item.get("callsign") or aircraft_id).strip(),
                "aircraft_type": aircraft_type,
                "route_id": item["route_id"].strip(),
                "speed_kt": float(
                    item.get(
                        "speed_kt",
                        _default_speed_for_type(aircraft_type, performance_db),
                    )
                ),
                "flight_level": int(round(float(item.get("flight_level", 350)))),
                "appear_after_seconds": appear_after_seconds,
                "metadata": item.get("metadata", {}),
            }
        )
    return sorted(aircraft, key=lambda item: item["appear_after_seconds"])


def _add_aircraft(api_base: str, run_id: str, aircraft: dict) -> dict:
    return _request_json(
        "POST",
        f"{api_base}/api/v1/runs/{run_id}/commands",
        {
            "command_type": "ADD_AIRCRAFT",
            "payload": aircraft,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a hosted demo scenario, run, and aircraft set."
    )
    parser.add_argument(
        "--api-base-url",
        default="http://127.0.0.1:8000",
        help="Base URL for the FastAPI backend.",
    )
    parser.add_argument(
        "--web-base-url",
        default="http://127.0.0.1:5174",
        help="Base URL for the React frontend.",
    )
    parser.add_argument(
        "--initial-aircraft",
        type=int,
        default=7,
        help="Number of aircraft to add immediately after the run starts.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Number of later aircraft to add per staggered batch.",
    )
    parser.add_argument(
        "--stagger-seconds",
        type=float,
        default=8.0,
        help="Seconds to wait between later aircraft batches. Use 0 to add all immediately.",
    )
    parser.add_argument(
        "--template",
        help="Optional JSON template describing routes, aircraft, and appearance timing.",
    )
    parser.add_argument(
        "--airspace",
        help=(
            "Optional airspace package JSON. Defaults to "
            "airspaces/gao_demo/airspace.v1.json."
        ),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the selected template/demo inputs and exit without calling the API.",
    )
    parser.add_argument(
        "--session-id",
        default=DEFAULT_SESSION_ID,
        help=(
            "Client session id to scope the created scenario/run under. "
            f"Defaults to a stable id ('{DEFAULT_SESSION_ID}') so repeated "
            "seeding stays visible in a browser that adopted it once."
        ),
    )
    parser.add_argument(
        "--keep-existing-runs",
        action="store_true",
        help=(
            "Do not stop existing active Hosted Demo runs for this session before "
            "creating a new one."
        ),
    )
    args = parser.parse_args()

    global SESSION_ID
    SESSION_ID = args.session_id

    api_base = args.api_base_url.rstrip("/")
    web_base = args.web_base_url.rstrip("/")
    stamp = _timestamp_label()
    template = _load_template(args.template)
    performance_db = _load_aircraft_performance()
    template_metadata = template.get("metadata", {}) if template else {}
    base_airspace, airspace_path = _load_airspace(args.airspace)
    demo_airspace = _build_demo_airspace(base_airspace, template)
    if template:
        _validate_template_or_exit(
            template,
            demo_airspace,
            template.get("aircraft"),
            performance_db,
        )
        demo_aircraft = _build_template_aircraft(template, performance_db)
    else:
        demo_aircraft = _build_demo_aircraft(performance_db)
        _validate_template_or_exit(None, demo_airspace, demo_aircraft, performance_db)

    if args.validate_only:
        source = args.template or "built-in demo plan"
        print(f"Template validation passed: {source}")
        print(f"Airspace: {_airspace_id(demo_airspace) or airspace_path}")
        print(f"Aircraft: {len(demo_aircraft)}")
        print(f"Routes: {len(_airspace_route_ids(demo_airspace))}")
        return 0

    stopped_existing_runs = (
        0 if args.keep_existing_runs else _stop_existing_demo_runs(api_base)
    )

    initial_count = (
        len([item for item in demo_aircraft if item.get("appear_after_seconds", 0) <= 0])
        if template
        else max(1, min(args.initial_aircraft, len(demo_aircraft)))
    )
    batch_size = max(1, args.batch_size)
    initial_aircraft = demo_aircraft[:initial_count]

    scenario = _request_json(
        "POST",
        f"{api_base}/api/v1/scenarios",
        {
            "name": template_metadata.get("name", f"Hosted Demo Scenario {stamp}"),
            "description": (
                template_metadata.get("description")
                or "Scenario created by scripts/seed_hosted_demo.py with "
                "departure, arrival, and overflight tracks."
            ),
            "airspace_payload": demo_airspace,
            "aircraft_payload": _scenario_aircraft_payload(initial_aircraft),
        },
    )

    run = _request_json(
        "POST",
        f"{api_base}/api/v1/runs",
        {
            "name": f"Hosted Demo Run {stamp}",
            "scenario_id": scenario["id"],
        },
    )

    _request_json("POST", f"{api_base}/api/v1/runs/{run['id']}/start")

    remaining_aircraft = demo_aircraft[initial_count:]
    applied_later_aircraft = 0
    if template:
        elapsed_seconds = 0.0
        for aircraft in remaining_aircraft:
            appear_after_seconds = float(aircraft.get("appear_after_seconds", 0))
            wait_seconds = max(appear_after_seconds - elapsed_seconds, 0)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
                elapsed_seconds = appear_after_seconds
            response = _add_aircraft(api_base, run["id"], aircraft)
            if response.get("result", {}).get("applied"):
                applied_later_aircraft += 1
    else:
        for batch_start in range(0, len(remaining_aircraft), batch_size):
            if args.stagger_seconds > 0:
                time.sleep(args.stagger_seconds)
            for aircraft in remaining_aircraft[batch_start : batch_start + batch_size]:
                response = _add_aircraft(api_base, run["id"], aircraft)
                if response.get("result", {}).get("applied"):
                    applied_later_aircraft += 1

    state = _request_json("GET", f"{api_base}/api/v1/runs/{run['id']}/state")

    print("Hosted AirSpaceSim demo created.")
    print(f"Scenario: {scenario['name']} ({scenario['id']})")
    print(f"Run: {run['name']} ({run['id']})")
    print(f"Airspace: {_airspace_id(demo_airspace) or airspace_path}")
    if stopped_existing_runs:
        print(f"Stopped previous active demo runs: {stopped_existing_runs}")
    print(f"Aircraft loaded: {state['metrics']['aircraft_count']} / {len(demo_aircraft)}")
    print(
        "Traffic mix: departures, arrivals, and overflights. "
        f"Initial tracks: {initial_count}; later tracks added: {applied_later_aircraft}; "
        f"later batch size: {batch_size}."
    )
    print()
    print("Open these URLs:")
    session_query = f"sid={quote(SESSION_ID)}"
    print(f"- Web run workspace: {web_base}/runs/{run['id']}?{session_query}")
    print(f"- Runs page: {web_base}/runs?{session_query}")
    print(f"- API docs: {api_base}/docs")
    print()
    print(
        "Runs are scoped to a client session id. This script uses a stable id "
        f"('{SESSION_ID}') by default, so you only need to do this once — it "
        "keeps working for every future reseed unless you pass --session-id."
    )
    print(
        "If the browser doesn't already have this id, open devtools console on "
        "the web app and run this once, then reload the page:"
    )
    print(f"  localStorage.setItem('airspacesim.session-id', '{SESSION_ID}')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
