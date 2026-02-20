"""Run a deterministic stress scenario with many aircraft."""

import argparse

from airspacesim.simulation.aircraft_manager import AircraftManager


def _build_routes():
    return {
        "STRESS_MAIN": [
            {"dec_coords": [16.25, -0.03]},
            {"dec_coords": [16.35, 0.02]},
            {"dec_coords": [16.45, 0.08]},
        ]
    }


def run_stress(num_aircraft, duration_seconds, speed_kt):
    manager = AircraftManager(_build_routes(), execution_mode="batched")
    for idx in range(num_aircraft):
        manager.add_aircraft(
            id=f"STRESS_{idx:04d}",
            route_name="STRESS_MAIN",
            callsign=f"S{idx:04d}",
            speed=speed_kt,
        )

    manager.run_batched_for(duration_seconds=duration_seconds, update_interval=0.1)
    manager.terminate_simulations(timeout_seconds=3.0)

    finished = sum(1 for ac in manager.aircraft_list if hasattr(ac, "finished_time"))
    active = len(manager.aircraft_list) - finished
    return {
        "num_aircraft": num_aircraft,
        "duration_seconds": duration_seconds,
        "speed_kt": speed_kt,
        "finished": finished,
        "active": active,
    }


def main():
    parser = argparse.ArgumentParser(description="Run a stress simulation scenario.")
    parser.add_argument("--aircraft", type=int, default=100, help="Number of aircraft to spawn.")
    parser.add_argument("--duration", type=float, default=5.0, help="Run duration in seconds.")
    parser.add_argument("--speed", type=float, default=420.0, help="Aircraft speed in knots.")
    args = parser.parse_args()

    metrics = run_stress(args.aircraft, args.duration, args.speed)
    print("Stress simulation summary:")
    for key, value in metrics.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
