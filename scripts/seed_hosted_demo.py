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

from airspacesim.io import normalize_scenario_airspace_payload  # noqa: E402 (after sys.path setup)

from airspacesim.io.templates import (  # noqa: E402 (after sys.path setup)
    airspace_id as _airspace_id,
    airspace_route_ids as _airspace_route_ids,
    default_speed_for_type as _default_speed_for_type,
    format_validation_errors as _format_validation_errors,
    load_aircraft_performance,
    max_flight_level_for_type as _max_flight_level_for_type,
    merge_template_routes,
    validate_scenario_template,
)


def _load_aircraft_performance() -> dict:
    """Aircraft-performance profiles (shared engine database)."""
    return load_aircraft_performance()


def _build_demo_airspace(base_airspace: dict, template: dict | None = None) -> dict:
    """Merge template extra_routes, or the built-in demo overflight routes."""
    if template:
        return merge_template_routes(base_airspace, template)
    builtin_overflights = {
        "airspace": {
            "extra_routes": [
                {
                    "id": "UN866",
                    "name": "Overflight NW-SE",
                    "waypoint_ids": ["ORNAK", "NRV_VOR", "TIRGO"],
                },
                {
                    "id": "UT204",
                    "name": "Overflight NE-SW",
                    "waypoint_ids": ["LUMEK", "NRV_VOR", "KOLVA"],
                },
                {
                    "id": "UM551",
                    "name": "Overflight N-S",
                    "waypoint_ids": ["NARVO", "NRV_VOR", "TULBA"],
                },
            ]
        }
    }
    return merge_template_routes(base_airspace, builtin_overflights)


def _validate_template_or_exit(
    template: dict | None,
    airspace: dict,
    aircraft: object,
    performance_db: dict,
) -> None:
    errors = validate_scenario_template(template, airspace, aircraft, performance_db)
    if errors:
        raise SystemExit(_format_validation_errors(errors))


DEFAULT_AIRSPACE_PATH = PROJECT_ROOT / "airspaces" / "nerava_fir" / "airspace.v1.json"
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


def _normalize_aircraft_type(value: object, performance_db: dict) -> str:
    aircraft_type = str(value or "B737").strip().upper()
    if aircraft_type not in performance_db:
        known_types = ", ".join(sorted(performance_db))
        raise SystemExit(
            f"Unknown aircraft_type '{aircraft_type}'. Known types: {known_types}"
        )
    return aircraft_type


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
        ("UL602", "departure"),
        ("UM731", "arrival"),
        ("UN866", "overflight"),
        ("T45", "departure"),
        ("B12", "departure"),
        ("UT204", "overflight"),
        ("UM214", "departure"),
        ("A1", "departure"),
        ("UN480", "departure"),
        ("UM551", "overflight"),
        ("UT88", "departure"),
        ("UL335", "departure"),
        ("UM731", "arrival"),
        ("UL602", "departure"),
        ("UN866", "overflight"),
        ("T45", "departure"),
        ("B12", "departure"),
        ("UT204", "overflight"),
        ("UM214", "departure"),
        ("A1", "departure"),
        ("UN480", "departure"),
        ("UM551", "overflight"),
        ("UT88", "departure"),
        ("UL335", "departure"),
        ("UM731", "arrival"),
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
            "airspaces/nerava_fir/airspace.v1.json."
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
