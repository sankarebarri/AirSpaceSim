import json
from io import StringIO
from types import SimpleNamespace

from airspacesim.io.adapters import FileEventAdapter, FileSnapshotAdapter, StdinEventAdapter
from airspacesim.io.contracts import (
    build_envelope,
    contract_domain,
    ValidationError,
    validate_aircraft_data,
    validate_aircraft_state,
    validate_inbox_events,
    validate_map_config,
    validate_render_profile,
    validate_scenario_v01,
    validate_scenario_aircraft,
    validate_scenario_airspace,
    validate_trajectory_v01,
)
from airspacesim.settings import settings
from airspacesim.simulation.aircraft_manager import AircraftManager
from airspacesim.simulation.events import apply_events_idempotent
from airspacesim.simulation.scenario_runner import load_scenarios


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_scenario_contracts_validate_and_load(tmp_path):
    scenario_airspace = {
        "schema": {"name": "airspacesim.scenario_airspace", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {
            "points": {
                "P1": {"type": "fix", "name": "P1", "coord": {"dd": [10.0, 1.0]}},
                "P2": {"type": "fix", "name": "P2", "coord": {"dd": [11.0, 1.5]}},
            },
            "airspaces": [{"id": "A1", "center_point_id": "P1", "radius_nm": 30}],
            "routes": [{"id": "R1", "name": "R1", "waypoint_ids": ["P1", "P2"]}],
        },
    }
    scenario_aircraft = {
        "schema": {"name": "airspacesim.scenario_aircraft", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {"aircraft": [{"id": "AC1", "route_id": "R1", "speed_kt": 400}]},
    }

    airspace_path = tmp_path / "scenario_airspace.v1.json"
    aircraft_path = tmp_path / "scenario_aircraft.v1.json"
    _write_json(airspace_path, scenario_airspace)
    _write_json(aircraft_path, scenario_aircraft)

    validate_scenario_airspace(scenario_airspace)
    validate_scenario_aircraft(scenario_aircraft, route_ids={"R1"})
    loaded_airspace, loaded_aircraft = load_scenarios(
        airspace_path=str(airspace_path),
        aircraft_path=str(aircraft_path),
    )
    assert loaded_airspace["data"]["routes"][0]["id"] == "R1"
    assert loaded_aircraft["data"]["aircraft"][0]["id"] == "AC1"


def test_combined_scenario_v01_contract_validates_and_loads(tmp_path):
    payload = {
        "schema": {"name": "airspacesim.scenario", "version": "0.1"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {
            "airspace": {
                "points": {
                    "P1": {"type": "fix", "name": "P1", "coord": {"dd": [10.0, 1.0]}},
                    "P2": {"type": "fix", "name": "P2", "coord": {"dd": [11.0, 1.5]}},
                },
                "airspaces": [{"id": "A1", "center_point_id": "P1", "radius_nm": 30}],
                "routes": [{"id": "R1", "name": "R1", "waypoint_ids": ["P1", "P2"]}],
            },
            "aircraft": {"aircraft": [{"id": "AC1", "route_id": "R1", "speed_kt": 400}]},
        },
    }
    scenario_path = tmp_path / "scenario.v0.1.json"
    _write_json(scenario_path, payload)
    validate_scenario_v01(payload)
    loaded_airspace, loaded_aircraft = load_scenarios(scenario_path=str(scenario_path))
    assert loaded_airspace["schema"]["name"] == "airspacesim.scenario_airspace"
    assert loaded_aircraft["schema"]["name"] == "airspacesim.scenario_aircraft"
    assert loaded_aircraft["data"]["aircraft"][0]["id"] == "AC1"


def test_contract_validators_reject_invalid_payloads():
    with_exception = {
        "schema": {"name": "airspacesim.aircraft_state", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {"aircraft": [{"id": "A", "position_dd": [91.0, 0.0], "status": "active", "updated_utc": "bad"}]},
    }
    try:
        validate_aircraft_state(with_exception)
        assert False, "Expected ValidationError for invalid aircraft_state payload"
    except ValidationError:
        pass


def test_file_event_adapter_is_idempotent_and_ordered(tmp_path):
    payload = {
        "schema": {"name": "airspacesim.inbox_events", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {
            "events": [
                {"event_id": "e2", "type": "SET_SPEED", "created_utc": "2026-02-20T00:00:02Z", "sequence": 2, "payload": {"aircraft_id": "AC1", "speed_kt": 500}},
                {"event_id": "e1", "type": "SET_SPEED", "created_utc": "2026-02-20T00:00:01Z", "sequence": 1, "payload": {"aircraft_id": "AC1", "speed_kt": 450}},
            ]
        },
    }
    path = tmp_path / "inbox_events.v1.json"
    _write_json(path, payload)
    adapter = FileEventAdapter(str(path))
    first = adapter.poll()
    second = adapter.poll()
    assert [evt["event_id"] for evt in first] == ["e1", "e2"]
    assert second == []


def test_apply_events_idempotent_mutates_manager_state(tmp_path):
    routes = {
        "R1": [{"dec_coords": [10.0, 1.0]}, {"dec_coords": [11.0, 1.5]}],
        "R2": [{"dec_coords": [10.0, 1.0]}, {"dec_coords": [12.0, 2.0]}],
    }
    manager = AircraftManager(routes)
    manager.aircraft_list = [
        SimpleNamespace(
            id="AC1",
            route="R1",
            speed=400,
            callsign="AC1",
            altitude_ft=9000,
            vertical_rate_fpm=0,
            position=[10.0, 1.0],
            waypoints=[[10.0, 1.0], [11.0, 1.5]],
            current_index=0,
            segment_progress=0,
        )
    ]

    original_aircraft_file = settings.AIRCRAFT_FILE
    original_aircraft_state_file = settings.AIRCRAFT_STATE_FILE
    settings.AIRCRAFT_FILE = str((tmp_path / "aircraft_data.json"))
    settings.AIRCRAFT_STATE_FILE = str((tmp_path / "aircraft_state.v1.json"))
    try:
        events = [
            {"event_id": "e1", "type": "SET_SPEED", "created_utc": "2026-02-20T00:00:01Z", "payload": {"aircraft_id": "AC1", "speed_kt": 420}},
            {"event_id": "e2", "type": "REROUTE", "created_utc": "2026-02-20T00:00:02Z", "payload": {"aircraft_id": "AC1", "route_id": "R2"}},
            {"event_id": "e3", "type": "SET_VERTICAL_RATE", "created_utc": "2026-02-20T00:00:03Z", "payload": {"aircraft_id": "AC1", "vertical_rate_fpm": 600}},
        ]
        result = apply_events_idempotent(manager, events)
        assert result["applied"] == ["e1", "e2", "e3"]
        assert manager.aircraft_list[0].speed == 420
        assert manager.aircraft_list[0].route == "R2"
        assert manager.aircraft_list[0].vertical_rate_fpm == 600
    finally:
        settings.AIRCRAFT_FILE = original_aircraft_file
        settings.AIRCRAFT_STATE_FILE = original_aircraft_state_file


def test_render_profile_validator_accepts_minimum_shape():
    payload = {
        "schema": {"name": "airspacesim.render_profile", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {"map": {"zoom": 8}, "layers": []},
    }
    validate_render_profile(payload)


def test_map_config_validator_accepts_legacy_and_versioned_shapes():
    legacy = {
        "center": [16.25, -0.03],
        "zoom": 8,
        "tile_layer": {"url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "attribution": "OSM"},
        "elements": [],
    }
    validate_map_config(legacy)

    versioned = {
        "schema": {"name": "airspacesim.map_config", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": legacy,
    }
    validate_map_config(versioned)


def test_aircraft_data_validator_accepts_legacy_and_versioned_shapes():
    legacy = {
        "aircraft_data": [
            {
                "id": "AC1",
                "position": [16.25, -0.03],
                "callsign": "TEST01",
                "speed": 420,
            }
        ]
    }
    validate_aircraft_data(legacy)

    versioned = {
        "schema": {"name": "airspacesim.aircraft_data", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": legacy,
    }
    validate_aircraft_data(versioned)


def test_snapshot_adapter_runs_validator(tmp_path):
    payload = {
        "schema": {"name": "airspacesim.inbox_events", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {"events": []},
    }
    path = tmp_path / "events.json"
    adapter = FileSnapshotAdapter(str(path), validator=validate_inbox_events)
    adapter.save(payload)
    loaded = adapter.load()
    assert loaded["schema"]["name"] == "airspacesim.inbox_events"


def test_contract_envelope_builder_and_domain_mapping():
    payload = build_envelope(
        schema_name="airspacesim.inbox_events",
        source="test",
        data={"events": []},
        generated_utc="2026-02-20T00:00:00Z",
    )
    assert payload["schema"]["version"] == "1.0"
    assert payload["metadata"]["source"] == "test"
    assert contract_domain("airspacesim.inbox_events") == "aircraft_events"
    assert contract_domain("airspacesim.unknown") is None


def test_trajectory_v01_validator_accepts_minimum_shape():
    payload = {
        "schema": {"name": "airspacesim.trajectory", "version": "0.1"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {
            "tracks": [
                {
                    "id": "AC1",
                    "route_id": "R1",
                    "position_dd": [10.0, 1.0],
                    "status": "active",
                    "updated_utc": "2026-02-20T00:00:00Z",
                }
            ]
        },
    }
    validate_trajectory_v01(payload)


def _assert_ingestion_conformance(adapter):
    first = adapter.poll()
    assert [evt["event_id"] for evt in first] == ["e1", "e2"]
    adapter.ack([evt["event_id"] for evt in first])
    second = adapter.poll()
    assert second == []


def test_ingestion_conformance_file_event_adapter(tmp_path):
    payload = {
        "schema": {"name": "airspacesim.inbox_events", "version": "1.0"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {
            "events": [
                {"event_id": "e2", "type": "SET_SPEED", "created_utc": "2026-02-20T00:00:02Z", "sequence": 2, "payload": {"aircraft_id": "AC1", "speed_kt": 500}},
                {"event_id": "e1", "type": "SET_SPEED", "created_utc": "2026-02-20T00:00:01Z", "sequence": 1, "payload": {"aircraft_id": "AC1", "speed_kt": 450}},
            ]
        },
    }
    path = tmp_path / "events.v1.json"
    _write_json(path, payload)
    adapter = FileEventAdapter(str(path), auto_ack=False)
    _assert_ingestion_conformance(adapter)


def test_ingestion_conformance_stdin_event_adapter():
    stream = StringIO(
        "\n".join(
            [
                json.dumps({"event_id": "e2", "type": "SET_SPEED", "created_utc": "2026-02-20T00:00:02Z", "sequence": 2, "payload": {"aircraft_id": "AC1", "speed_kt": 500}}),
                json.dumps({"event_id": "e1", "type": "SET_SPEED", "created_utc": "2026-02-20T00:00:01Z", "sequence": 1, "payload": {"aircraft_id": "AC1", "speed_kt": 450}}),
                "",
            ]
        )
    )
    adapter = StdinEventAdapter(stream=stream)
    _assert_ingestion_conformance(adapter)
