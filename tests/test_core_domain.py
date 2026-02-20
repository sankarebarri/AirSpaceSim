from types import SimpleNamespace

from airspacesim.core.models import TrajectoryTrack
from airspacesim.core.stepper import ManagerStepper
from airspacesim.simulation.scenario_runner import load_scenario_bundle


def test_load_scenario_bundle_from_combined_contract(tmp_path):
    scenario = {
        "schema": {"name": "airspacesim.scenario", "version": "0.1"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {
            "airspace": {
                "points": {
                    "P1": {"type": "fix", "coord": {"dd": [10.0, 1.0]}},
                    "P2": {"type": "fix", "coord": {"dd": [11.0, 1.5]}},
                },
                "airspaces": [{"id": "A1", "center_point_id": "P1", "radius_nm": 30}],
                "routes": [{"id": "R1", "name": "R1", "waypoint_ids": ["P1", "P2"]}],
            },
            "aircraft": {
                "aircraft": [{"id": "AC1", "route_id": "R1", "speed_kt": 420}],
            },
        },
    }
    path = tmp_path / "scenario.v0.1.json"
    path.write_text(__import__("json").dumps(scenario), encoding="utf-8")

    bundle = load_scenario_bundle(scenario_path=str(path))
    assert "P1" in bundle.points
    assert bundle.routes["R1"] == ("P1", "P2")
    assert bundle.aircraft[0].id == "AC1"


def test_trajectory_track_contract_conversion():
    track = TrajectoryTrack(
        id="AC1",
        route_id="R1",
        position_dd=(16.25, -0.03),
        status="active",
        updated_utc="2026-02-20T00:00:00Z",
        speed_kt=420,
    )
    payload = track.as_contract_dict()
    assert payload["id"] == "AC1"
    assert payload["position_dd"] == [16.25, -0.03]
    assert payload["speed_kt"] == 420


def test_manager_stepper_returns_tracks():
    manager = SimpleNamespace()
    manager.aircraft_list = [
        SimpleNamespace(
            id="AC1",
            route="R1",
            position=[10.0, 1.0],
            callsign="A1",
            speed=410,
            altitude_ft=9000,
            vertical_rate_fpm=0,
        )
    ]
    manager._step_all_aircraft = lambda dt: None
    stepper = ManagerStepper(manager)
    tracks = stepper.step(1.0)
    assert len(tracks) == 1
    assert tracks[0].id == "AC1"
