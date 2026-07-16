"""Phase 1 engine-boundary guarantees: pure, deterministic, IO-free stepping."""

import pytest

from airspacesim.simulation.aircraft_manager import AircraftManager

ROUTES = {
    "R1": [{"id": "A", "dec_coords": [10.0, 1.0]}, {"id": "B", "dec_coords": [11.0, 2.0]}],
    "R2": [{"id": "C", "dec_coords": [12.0, 1.0]}, {"id": "D", "dec_coords": [11.0, 2.0]}],
}


def _build_manager(sim_rate=1.0):
    manager = AircraftManager(
        ROUTES,
        execution_mode="batched",
        sim_rate=sim_rate,
        enable_file_output=False,
    )
    manager.add_aircraft("AC1", "R1", callsign="AC1", speed=420, flight_level=330)
    manager.add_aircraft("AC2", "R2", callsign="AC2", speed=440, flight_level=350)
    return manager


def _positions(manager):
    return [(ac.id, tuple(ac.position), ac.altitude_ft) for ac in manager.aircraft_list]


def test_identical_step_sequences_produce_identical_states():
    first = _build_manager()
    second = _build_manager()

    for _ in range(50):
        first._step_all_aircraft(1.0)
    for _ in range(50):
        second._step_all_aircraft(1.0)

    assert _positions(first) == _positions(second)


def test_manager_sim_rate_scales_simulated_time():
    realtime = _build_manager(sim_rate=1.0)
    accelerated = _build_manager(sim_rate=4.0)

    for _ in range(20):
        realtime._step_all_aircraft(4.0)
    for _ in range(20):
        accelerated._step_all_aircraft(1.0)

    for (_, realtime_pos, _), (_, accelerated_pos, _) in zip(
        _positions(realtime), _positions(accelerated)
    ):
        assert realtime_pos[0] == pytest.approx(accelerated_pos[0], abs=1e-9)
        assert realtime_pos[1] == pytest.approx(accelerated_pos[1], abs=1e-9)


def test_set_simulation_speed_is_scoped_to_one_manager():
    first = _build_manager()
    second = _build_manager()

    first.set_simulation_speed(3.0)

    assert first.sim_rate == 3.0
    assert second.sim_rate == 1.0


def test_disabled_file_output_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    manager = _build_manager()

    manager._step_all_aircraft(1.0)
    manager.save_aircraft_data()

    assert list(tmp_path.rglob("*.json")) == []


def test_enabled_file_output_still_writes_contracts(tmp_path):
    from airspacesim.settings import settings

    manager = AircraftManager(ROUTES, execution_mode="batched")
    manager.add_aircraft("AC1", "R1", callsign="AC1", speed=420, flight_level=330)

    original = (
        settings.AIRCRAFT_FILE,
        settings.AIRCRAFT_STATE_FILE,
        settings.TRAJECTORY_FILE,
    )
    settings.AIRCRAFT_FILE = str(tmp_path / "aircraft_data.json")
    settings.AIRCRAFT_STATE_FILE = str(tmp_path / "aircraft_state.v1.json")
    settings.TRAJECTORY_FILE = str(tmp_path / "trajectory.v0.1.json")
    try:
        manager.save_aircraft_data()
        assert (tmp_path / "aircraft_data.json").exists()
        assert (tmp_path / "aircraft_state.v1.json").exists()
        assert (tmp_path / "trajectory.v0.1.json").exists()
    finally:
        (
            settings.AIRCRAFT_FILE,
            settings.AIRCRAFT_STATE_FILE,
            settings.TRAJECTORY_FILE,
        ) = original
