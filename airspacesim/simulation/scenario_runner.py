"""Scenario-first simulation bootstrap using canonical v1 contracts."""

import os

from airspacesim.core.models import AircraftDefinition, ScenarioBundle, Waypoint
from airspacesim.io.adapters import FileEventAdapter, FileSnapshotAdapter
from airspacesim.io.contracts import (
    build_envelope,
    validate_scenario_aircraft,
    validate_scenario_airspace,
    validate_scenario_v01,
)
from airspacesim.settings import settings
from airspacesim.simulation.aircraft_manager import AircraftManager
from airspacesim.simulation.events import apply_events_idempotent


def _build_routes_from_scenario_airspace(scenario_airspace):
    points = scenario_airspace["data"]["points"]
    routes = {}
    for route in scenario_airspace["data"]["routes"]:
        route_id = route["id"]
        route_points = []
        for point_id in route["waypoint_ids"]:
            point = points[point_id]
            route_points.append({"dec_coords": point["coord"]["dd"]})
        routes[route_id] = route_points
    return routes


def load_scenarios(airspace_path=None, aircraft_path=None, scenario_path=None):
    if scenario_path:
        scenario_contract_path = scenario_path
    else:
        cwd = os.getcwd()
        scenario_candidates = [
            os.path.join(cwd, "data", "scenario.v0.1.json"),
            os.path.join(cwd, "scenario.v0.1.json"),
        ]
        scenario_contract_path = next(
            (path for path in scenario_candidates if os.path.exists(path)), None
        )

    if scenario_contract_path:
        scenario_adapter = FileSnapshotAdapter(
            scenario_contract_path,
            validator=validate_scenario_v01,
        )
        scenario_payload = scenario_adapter.load()
        metadata = scenario_payload["metadata"]
        scenario_airspace = build_envelope(
            schema_name="airspacesim.scenario_airspace",
            source=metadata.get("source", "airspacesim.scenario_runner"),
            generated_utc=metadata.get("generated_utc"),
            data=scenario_payload["data"]["airspace"],
        )
        scenario_aircraft = build_envelope(
            schema_name="airspacesim.scenario_aircraft",
            source=metadata.get("source", "airspacesim.scenario_runner"),
            generated_utc=metadata.get("generated_utc"),
            data=scenario_payload["data"]["aircraft"],
        )
        return scenario_airspace, scenario_aircraft

    airspace_adapter = FileSnapshotAdapter(
        airspace_path or settings.SCENARIO_AIRSPACE_FILE,
        validator=validate_scenario_airspace,
    )
    scenario_airspace = airspace_adapter.load()
    route_ids = {route["id"] for route in scenario_airspace["data"]["routes"]}
    aircraft_adapter = FileSnapshotAdapter(
        aircraft_path or settings.SCENARIO_AIRCRAFT_FILE,
        validator=lambda payload: validate_scenario_aircraft(
            payload, route_ids=route_ids
        ),
    )
    scenario_aircraft = aircraft_adapter.load()
    return scenario_airspace, scenario_aircraft


def load_scenario_bundle(airspace_path=None, aircraft_path=None, scenario_path=None):
    """Load scenario contracts and normalize to typed core models."""
    scenario_airspace, scenario_aircraft = load_scenarios(
        airspace_path=airspace_path,
        aircraft_path=aircraft_path,
        scenario_path=scenario_path,
    )
    points = {
        point_id: Waypoint(
            id=point_id,
            position_dd=(
                float(point["coord"]["dd"][0]),
                float(point["coord"]["dd"][1]),
            ),
        )
        for point_id, point in scenario_airspace["data"]["points"].items()
    }
    routes = {
        route["id"]: tuple(route["waypoint_ids"])
        for route in scenario_airspace["data"]["routes"]
    }
    aircraft = tuple(
        AircraftDefinition(
            id=item["id"],
            route_id=item["route_id"],
            speed_kt=float(item["speed_kt"]),
            callsign=item.get("callsign"),
            altitude_ft=float(item.get("altitude_ft", 0.0)),
            vertical_rate_fpm=float(item.get("vertical_rate_fpm", 0.0)),
        )
        for item in scenario_aircraft["data"]["aircraft"]
    )
    return ScenarioBundle(
        points=points,
        routes=routes,
        aircraft=aircraft,
    )


def initialize_manager_from_scenarios(
    scenario_airspace, scenario_aircraft, execution_mode="thread_per_aircraft"
):
    routes = _build_routes_from_scenario_airspace(scenario_airspace)
    manager = AircraftManager(routes, execution_mode=execution_mode)
    for item in scenario_aircraft["data"]["aircraft"]:
        manager.add_aircraft(
            id=item["id"],
            route_name=item["route_id"],
            callsign=item.get("callsign", item["id"]),
            speed=item["speed_kt"],
            altitude_ft=item.get("altitude_ft", 0.0),
            vertical_rate_fpm=item.get("vertical_rate_fpm", 0.0),
        )
    return manager


def apply_inbox_events_once(manager, events_path=None):
    event_adapter = FileEventAdapter(events_path or settings.INBOX_EVENTS_FILE)
    events = event_adapter.poll()
    return apply_events_idempotent(manager, events)
