"""Phase 4: shared scenario-template/environment validation (airspacesim.io.templates)."""

from airspacesim.io.contracts import build_envelope
from airspacesim.io.templates import (
    is_semver,
    load_aircraft_performance,
    merge_template_routes,
    validate_airspace_geometry,
    validate_scenario_template,
)

PERFORMANCE = load_aircraft_performance()


def _airspace():
    payload = build_envelope(
        schema_name="airspacesim.scenario_airspace",
        source="tests.template_validation",
        data={
            "reference": {"datum": "WGS84", "earth_model": "spherical", "nm_to_m": 1852},
            "points": {
                "NRV_VOR": {
                    "type": "navaid",
                    "name": "Nerava VOR",
                    "coord": {"dd": [33.5, -41.0]},
                },
                "NARVO": {"type": "fix", "name": "NARVO", "coord": {"dd": [34.89, -41.3]}},
                "TIRGO": {"type": "fix", "name": "TIRGO", "coord": {"dd": [32.47, -40.35]}},
            },
            "routes": [
                {"id": "UL602", "waypoint_ids": ["NRV_VOR", "NARVO"]},
                {"id": "B12", "waypoint_ids": ["NRV_VOR", "TIRGO"]},
            ],
            "airspaces": [],
        },
    )
    payload["metadata"]["id"] = "test_env"
    return payload


def _aircraft(**overrides):
    item = {
        "id": "NVR231",
        "callsign": "NVR231",
        "aircraft_type": "A320",
        "route_id": "UL602",
        "speed_kt": 440,
        "flight_level": 330,
    }
    item.update(overrides)
    return item


def test_valid_template_produces_no_errors():
    template = {"version": "1.0.0", "airspace_id": "test_env"}
    errors = validate_scenario_template(
        template, _airspace(), [_aircraft()], PERFORMANCE
    )
    assert errors == []


def test_unknown_route_and_duplicates_read_as_plain_english():
    aircraft = [
        _aircraft(route_id="X9"),
        _aircraft(),  # duplicate id + callsign
    ]
    errors = validate_scenario_template({}, _airspace(), aircraft, PERFORMANCE)
    joined = " ".join(errors)
    assert "NVR231 references unknown route 'X9'." in joined
    assert "duplicates aircraft id 'NVR231'" in joined
    assert "duplicates callsign 'NVR231'" in joined


def test_speed_level_and_entry_bounds_are_validated():
    aircraft = [
        _aircraft(speed_kt=9999, flight_level=999, appear_after_seconds=-3),
    ]
    errors = validate_scenario_template({}, _airspace(), aircraft, PERFORMANCE)
    joined = " ".join(errors)
    assert "speed_kt 9999.0 outside A320 range" in joined
    assert "flight_level FL999 exceeds A320 max" in joined
    assert "appear_after_seconds must be >= 0" in joined


def test_unknown_aircraft_type_lists_known_types():
    errors = validate_scenario_template(
        {}, _airspace(), [_aircraft(aircraft_type="X999")], PERFORMANCE
    )
    assert any("unknown aircraft_type 'X999'" in error for error in errors)
    assert any("Known types:" in error for error in errors)


def test_airspace_id_mismatch_is_reported():
    template = {"airspace_id": "somewhere_else"}
    errors = validate_scenario_template(template, _airspace(), [_aircraft()], PERFORMANCE)
    assert any(
        "Template expects airspace_id 'somewhere_else'" in error for error in errors
    )


def test_unsupported_active_command_is_rejected():
    template = {
        "metadata": {
            "practice": {"active_commands": ["SET_FL", "LAUNCH_MISSILE"]},
        }
    }
    errors = validate_scenario_template(template, _airspace(), [_aircraft()], PERFORMANCE)
    assert any(
        "unsupported command 'LAUNCH_MISSILE'" in error for error in errors
    )
    # Only the unknown command is flagged; the valid SET_FL is accepted.
    assert sum("unsupported command" in error for error in errors) == 1


def test_bad_semver_is_rejected_and_good_semver_accepted():
    assert is_semver("1.0.0") and is_semver("10.2.33")
    assert not is_semver("1.0") and not is_semver("v1.0.0") and not is_semver(None)
    errors = validate_scenario_template(
        {"version": "one-point-oh"}, _airspace(), [_aircraft()], PERFORMANCE
    )
    assert any("must be semantic" in error for error in errors)


def test_merge_template_routes_adds_extra_routes_without_duplicates():
    airspace = _airspace()
    template = {
        "airspace": {
            "extra_routes": [
                {"id": "UN866", "waypoint_ids": ["NARVO", "TIRGO"]},
                {"id": "UL602", "waypoint_ids": ["NRV_VOR", "NARVO"]},  # duplicate id
            ]
        }
    }
    merged = merge_template_routes(airspace, template)
    route_ids = [route["id"] for route in merged["data"]["routes"]]
    assert route_ids == ["UL602", "B12", "UN866"]
    # Original untouched
    assert [r["id"] for r in airspace["data"]["routes"]] == ["UL602", "B12"]


def test_airspace_geometry_reports_unknown_waypoint():
    airspace = _airspace()
    airspace["data"]["routes"].append({"id": "BAD", "waypoint_ids": ["NRV_VOR", "GHOST"]})
    errors = validate_airspace_geometry(airspace)
    assert any("references unknown waypoint 'GHOST'" in error for error in errors)
