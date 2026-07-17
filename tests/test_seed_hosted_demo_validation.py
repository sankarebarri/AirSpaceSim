import importlib.util
from pathlib import Path

import pytest

from airspacesim.io import normalize_scenario_airspace_payload


def load_seed_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "seed_hosted_demo.py"
    spec = importlib.util.spec_from_file_location("seed_hosted_demo", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_seed_demo_validation_accepts_builtin_plan():
    seed = load_seed_module()
    performance_db = seed._load_aircraft_performance()
    base_airspace, _ = seed._load_airspace(None)
    airspace = seed._build_demo_airspace(base_airspace, None)
    aircraft = seed._build_demo_aircraft(performance_db)

    seed._validate_template_or_exit(None, airspace, aircraft, performance_db)


def test_seed_demo_stops_existing_active_demo_runs(monkeypatch):
    seed = load_seed_module()
    calls = []

    def fake_request_json(method, url, payload=None):
        calls.append((method, url, payload))
        if method == "GET" and url.endswith("/api/v1/runs"):
            return {
                "items": [
                    {
                        "id": "run-active-demo",
                        "name": "Hosted Demo Run 20260710-010101",
                        "status": "running",
                    },
                    {
                        "id": "run-paused-demo",
                        "name": "Hosted Demo Run 20260710-020202",
                        "status": "paused",
                    },
                    {
                        "id": "run-stopped-demo",
                        "name": "Hosted Demo Run 20260710-030303",
                        "status": "stopped",
                    },
                    {
                        "id": "run-active-other",
                        "name": "Manual Training Run",
                        "status": "running",
                    },
                ],
            }
        return {}

    monkeypatch.setattr(seed, "_request_json", fake_request_json)

    stopped_count = seed._stop_existing_demo_runs("http://127.0.0.1:8000")

    assert stopped_count == 2
    assert calls == [
        ("GET", "http://127.0.0.1:8000/api/v1/runs", None),
        (
            "POST",
            "http://127.0.0.1:8000/api/v1/runs/run-active-demo/stop",
            None,
        ),
        (
            "POST",
            "http://127.0.0.1:8000/api/v1/runs/run-paused-demo/stop",
            None,
        ),
    ]


def test_seed_demo_validation_reports_template_errors():
    seed = load_seed_module()
    performance_db = seed._load_aircraft_performance()
    base_airspace, _ = seed._load_airspace(None)
    airspace = seed._build_demo_airspace(base_airspace, None)
    template = {
        "aircraft": [
            {
                "id": "AC1",
                "callsign": "DUP",
                "aircraft_type": "B737",
                "route_id": "UNKNOWN_ROUTE",
                "speed_kt": 9999,
                "flight_level": 999,
                "appear_after_seconds": -1,
            },
            {
                "id": "AC1",
                "callsign": "DUP",
                "aircraft_type": "B737",
                "route_id": "UL602",
                "speed_kt": 410,
                "flight_level": 290,
            },
        ]
    }

    with pytest.raises(SystemExit) as exc_info:
        seed._validate_template_or_exit(
            template,
            airspace,
            template["aircraft"],
            performance_db,
        )

    message = str(exc_info.value)
    assert "Template validation failed" in message
    assert "duplicates aircraft id 'AC1'" in message
    assert "duplicates callsign 'DUP'" in message
    assert "unknown route 'UNKNOWN_ROUTE'" in message
    assert "speed_kt 9999.0 outside B737 range" in message
    assert "flight_level FL999 exceeds B737 max FL410" in message
    assert "appear_after_seconds must be >= 0" in message


def test_seed_demo_validation_rejects_mismatched_airspace_id():
    seed = load_seed_module()
    performance_db = seed._load_aircraft_performance()
    base_airspace, _ = seed._load_airspace(None)
    airspace = seed._build_demo_airspace(base_airspace, None)
    template = {
        "airspace_id": "training_alpha",
        "aircraft": [
            {
                "id": "AC1",
                "callsign": "DEP01",
                "aircraft_type": "B737",
                "route_id": "UL602",
                "speed_kt": 410,
                "flight_level": 290,
            }
        ],
    }

    with pytest.raises(SystemExit) as exc_info:
        seed._validate_template_or_exit(
            template,
            airspace,
            template["aircraft"],
            performance_db,
        )

    assert "Template expects airspace_id 'training_alpha'" in str(exc_info.value)


def test_seed_demo_validation_accepts_package_style_polygon_airspace():
    seed = load_seed_module()
    performance_db = seed._load_aircraft_performance()
    package_airspace = normalize_scenario_airspace_payload(
        {
            "metadata": {"id": "training_alpha", "name": "Training Alpha"},
            "points": [
                {
                    "id": "ALP_VOR",
                    "name": "Alpha VOR",
                    "type": "navaid",
                    "position": [16.25, -0.03],
                },
                {
                    "id": "FIX01",
                    "name": "FIX01",
                    "type": "fix",
                    "position": [16.8, 0.4],
                },
                {
                    "id": "FIX02",
                    "name": "FIX02",
                    "type": "fix",
                    "position": [15.9, -0.7],
                },
            ],
            "routes": [
                {
                    "id": "A1",
                    "name": "Alpha One",
                    "waypoint_ids": ["ALP_VOR", "FIX01", "FIX02"],
                }
            ],
            "airspaces": [
                {
                    "id": "ALPHA_TMA",
                    "name": "Alpha TMA",
                    "type": "polygon",
                    "points": [
                        [16.8, -1.2],
                        [17.4, 0.1],
                        [16.6, 1.0],
                    ],
                }
            ],
        }
    )
    template = {
        "airspace_id": "training_alpha",
        "aircraft": [
            {
                "id": "AC1",
                "callsign": "DEP01",
                "aircraft_type": "B737",
                "route_id": "A1",
                "speed_kt": 410,
                "flight_level": 290,
            }
        ],
    }

    seed._validate_template_or_exit(
        template,
        package_airspace,
        template["aircraft"],
        performance_db,
    )
