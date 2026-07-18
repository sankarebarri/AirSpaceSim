"""Phase 4: practice-run template validation and content-version stamping."""

import json

import pytest
from fastapi import HTTPException

from app import airspace_packages
from app.services import practice_runs
from app.services.practice_runs import create_practice_run

SESSION_ID = "test-session-validation"


def _write_package(root, *, aircraft_overrides=None):
    package_dir = root / "bad_pack"
    (package_dir / "scenarios").mkdir(parents=True)
    airspace = {
        "schema": {"name": "airspacesim.scenario_airspace", "version": "1.0"},
        "metadata": {"id": "bad_pack", "name": "Bad Pack", "version": "1.0.0"},
        "data": {
            "reference": {"datum": "WGS84", "earth_model": "spherical", "nm_to_m": 1852},
            "points": {
                "CTR": {"type": "navaid", "name": "Centre", "coord": {"dd": [10.0, 10.0]}},
                "EDGE": {"type": "fix", "name": "EDGE", "coord": {"dd": [11.0, 10.0]}},
            },
            "routes": [{"id": "R1", "waypoint_ids": ["CTR", "EDGE"]}],
            "airspaces": [],
        },
    }
    aircraft = {
        "id": "AC1",
        "callsign": "AC1",
        "aircraft_type": "B737",
        "route_id": "R1",
        "speed_kt": 420,
        "flight_level": 330,
    }
    aircraft.update(aircraft_overrides or {})
    template = {
        "schema": {"name": "airspacesim.demo_template", "version": "1.0"},
        "version": "1.0.0",
        "metadata": {"name": "Bad Scenario"},
        "airspace_id": "bad_pack",
        "aircraft": [aircraft],
    }
    manifest = {
        "schema": {"name": "airspacesim.airspace_package_manifest", "version": "1.0"},
        "id": "bad_pack",
        "version": "1.0.0",
        "name": "Bad Pack",
        "description": "Synthetic package for validation tests.",
        "package_type": "fictional",
        "service_types": ["enroute"],
        "difficulty": "beginner",
        "training_modes": ["solo_guided"],
        "airspace_file": "airspace.v1.json",
        "default_scenario": "only",
        "scenarios": [
            {"id": "only", "title": "Only Scenario", "path": "scenarios/only.v1.json"}
        ],
        "lessons": [],
    }
    (package_dir / "airspace.v1.json").write_text(json.dumps(airspace))
    (package_dir / "scenarios" / "only.v1.json").write_text(json.dumps(template))
    (package_dir / "package.v1.json").write_text(json.dumps(manifest))
    return package_dir


@pytest.fixture
def synthetic_airspaces_root(tmp_path, monkeypatch):
    def point_at(root):
        monkeypatch.setattr(airspace_packages, "AIRSPACES_ROOT", root)
        monkeypatch.setattr(practice_runs, "resolve_airspace_package_dir",
                            lambda airspace_id: root / airspace_id)
        return root

    return point_at


def test_invalid_template_returns_plain_language_400(
    db_session, tmp_path, synthetic_airspaces_root
):
    root = synthetic_airspaces_root(tmp_path)
    _write_package(root, aircraft_overrides={"route_id": "NO_SUCH_ROUTE"})

    with pytest.raises(HTTPException) as exc_info:
        create_practice_run(
            db_session,
            session_id=SESSION_ID,
            airspace_id="bad_pack",
            scenario_id="only",
        )

    assert exc_info.value.status_code == 400
    detail = exc_info.value.detail
    assert "failed validation" in detail
    assert "AC1 references unknown route 'NO_SUCH_ROUTE'." in detail
    assert "Traceback" not in detail


def test_valid_practice_run_stamps_content_versions(db_session):
    run = create_practice_run(
        db_session,
        session_id=SESSION_ID,
        airspace_id="training_alpha",
        lesson_id="enroute_crossing_traffic_intro",
    )

    metadata = run.scenario.metadata_payload
    versions = metadata["content_versions"]
    assert versions["airspace_id"] == "training_alpha"
    assert versions["environment_version"] == "1.0.0"
    assert versions["scenario_template_id"] == "crossing_traffic"
    assert versions["scenario_template_version"] == "1.0.0"
