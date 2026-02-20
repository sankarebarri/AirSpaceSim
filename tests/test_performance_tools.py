from airspacesim.simulation.performance import (
    benchmark_json_write_path,
    benchmark_update_loop,
)
from airspacesim.settings import settings


def test_benchmark_update_loop_returns_metrics():
    metrics = benchmark_update_loop(num_aircraft=5, num_steps=3, speed_kt=300, time_step=0.5)
    assert metrics["num_aircraft"] == 5
    assert metrics["num_steps"] == 3
    assert metrics["total_updates"] == 15
    assert metrics["elapsed_seconds"] >= 0
    assert metrics["updates_per_second"] >= 0


def test_benchmark_json_write_path_returns_metrics(tmp_path):
    original_aircraft_file = settings.AIRCRAFT_FILE
    original_aircraft_state_file = settings.AIRCRAFT_STATE_FILE
    settings.AIRCRAFT_FILE = str(tmp_path / "aircraft_data.json")
    settings.AIRCRAFT_STATE_FILE = str(tmp_path / "aircraft_state.v1.json")
    try:
        metrics = benchmark_json_write_path(num_aircraft=5, iterations=3)
        assert metrics["num_aircraft"] == 5
        assert metrics["iterations"] == 3
        assert metrics["elapsed_seconds"] >= 0
        assert metrics["writes_per_second"] >= 0
    finally:
        settings.AIRCRAFT_FILE = original_aircraft_file
        settings.AIRCRAFT_STATE_FILE = original_aircraft_state_file
