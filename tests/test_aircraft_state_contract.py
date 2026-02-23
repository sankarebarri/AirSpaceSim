import json
from types import SimpleNamespace

from airspacesim.settings import settings
from airspacesim.simulation.aircraft_manager import AircraftManager


def test_save_aircraft_data_writes_canonical_aircraft_state(tmp_path):
    aircraft_file = tmp_path / "aircraft_data.json"
    aircraft_state_file = tmp_path / "aircraft_state.v1.json"
    trajectory_file = tmp_path / "trajectory.v0.1.json"

    original_aircraft_file = settings.AIRCRAFT_FILE
    original_aircraft_state_file = settings.AIRCRAFT_STATE_FILE
    original_trajectory_file = settings.TRAJECTORY_FILE

    try:
        settings.AIRCRAFT_FILE = str(aircraft_file)
        settings.AIRCRAFT_STATE_FILE = str(aircraft_state_file)
        settings.TRAJECTORY_FILE = str(trajectory_file)

        manager = AircraftManager({})
        manager.stop_event.clear()
        manager.aircraft_list = [
            SimpleNamespace(
                id="AC_TEST_01",
                position=[16.25, -0.03],
                callsign="TEST01",
                speed=420,
                flight_level=210,
                altitude_ft=9000,
                vertical_rate_fpm=0,
                route="UA612",
            )
        ]
        manager.save_aircraft_data()

        legacy_payload = json.loads(aircraft_file.read_text(encoding="utf-8"))
        assert legacy_payload["aircraft_data"][0]["id"] == "AC_TEST_01"

        canonical_payload = json.loads(aircraft_state_file.read_text(encoding="utf-8"))
        assert canonical_payload["schema"]["name"] == "airspacesim.aircraft_state"
        assert canonical_payload["schema"]["version"] == "1.0"
        assert len(canonical_payload["data"]["aircraft"]) == 1
        item = canonical_payload["data"]["aircraft"][0]
        assert item["id"] == "AC_TEST_01"
        assert item["position_dd"] == [16.25, -0.03]
        assert item["status"] == "active"
        assert item["speed_kt"] == 420
        assert item["flight_level"] == 210
        assert item["altitude_ft"] == 9000
        assert item["vertical_rate_fpm"] == 0
        assert item["traffic_flow"] == "unknown"
        assert item["route_id"] == "UA612"

        trajectory_payload = json.loads(trajectory_file.read_text(encoding="utf-8"))
        assert trajectory_payload["schema"]["name"] == "airspacesim.trajectory"
        assert trajectory_payload["schema"]["version"] == "0.1"
        assert trajectory_payload["data"]["tracks"][0]["id"] == "AC_TEST_01"
    finally:
        settings.AIRCRAFT_FILE = original_aircraft_file
        settings.AIRCRAFT_STATE_FILE = original_aircraft_state_file
        settings.TRAJECTORY_FILE = original_trajectory_file


def test_add_aircraft_sets_traffic_flow_from_route():
    center_lat, center_lon = settings.AIRSPACE_CENTER
    routes = {
        "OUTBOUND": [
            {"dec_coords": [center_lat, center_lon]},
            {"dec_coords": [center_lat + 0.6, center_lon + 0.6]},
        ],
        "INBOUND": [
            {"dec_coords": [center_lat + 0.6, center_lon + 0.6]},
            {"dec_coords": [center_lat, center_lon]},
        ],
    }
    manager = AircraftManager(routes, execution_mode="batched")

    manager.add_aircraft(id="AC_OUT_1", route_name="OUTBOUND", callsign="OUT1", speed=420)
    manager.add_aircraft(id="AC_IN_1", route_name="INBOUND", callsign="IN1", speed=420)

    by_id = {ac.id: ac for ac in manager.aircraft_list}
    assert by_id["AC_OUT_1"].traffic_flow == "outbound"
    assert by_id["AC_IN_1"].traffic_flow == "inbound"
