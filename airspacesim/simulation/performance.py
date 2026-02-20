"""Performance utilities for simulation stress and benchmark runs."""

import time
from types import SimpleNamespace

from airspacesim.settings import settings
from airspacesim.simulation.aircraft import Aircraft
from airspacesim.simulation.aircraft_manager import AircraftManager


def benchmark_update_loop(num_aircraft=200, num_steps=50, speed_kt=420, time_step=1.0):
    """Benchmark pure aircraft position updates (no threads, no file writes)."""
    aircraft_list = [
        Aircraft(
            id=f"BENCH_{idx:04d}",
            route="BENCH_ROUTE",
            waypoints=[[16.25, -0.03], [16.35, 0.02], [16.45, 0.08]],
            speed=speed_kt,
            callsign=f"B{idx:04d}",
        )
        for idx in range(num_aircraft)
    ]

    start = time.perf_counter()
    for _ in range(num_steps):
        for aircraft in aircraft_list:
            aircraft.update_position(time_step)
    elapsed = time.perf_counter() - start
    total_updates = num_aircraft * num_steps

    return {
        "num_aircraft": num_aircraft,
        "num_steps": num_steps,
        "total_updates": total_updates,
        "elapsed_seconds": elapsed,
        "updates_per_second": (total_updates / elapsed) if elapsed > 0 else 0.0,
    }


def benchmark_json_write_path(num_aircraft=200, iterations=25):
    """Benchmark manager JSON write path (legacy + canonical state files)."""
    manager = AircraftManager(routes={})
    manager.aircraft_list = [
        SimpleNamespace(
            id=f"BENCH_{idx:04d}",
            position=[16.25 + (idx * 0.0001), -0.03 + (idx * 0.0001)],
            callsign=f"B{idx:04d}",
            speed=420,
            altitude_ft=10000.0,
            vertical_rate_fpm=0.0,
            route="BENCH_ROUTE",
        )
        for idx in range(num_aircraft)
    ]

    start = time.perf_counter()
    for _ in range(iterations):
        manager.save_aircraft_data()
    elapsed = time.perf_counter() - start

    return {
        "num_aircraft": num_aircraft,
        "iterations": iterations,
        "elapsed_seconds": elapsed,
        "writes_per_second": (iterations / elapsed) if elapsed > 0 else 0.0,
        "aircraft_file": settings.AIRCRAFT_FILE,
        "aircraft_state_file": settings.AIRCRAFT_STATE_FILE,
    }
