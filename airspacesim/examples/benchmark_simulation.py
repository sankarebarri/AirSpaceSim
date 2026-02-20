"""Benchmark simulation update loop and JSON write path."""

import argparse

from airspacesim.simulation.performance import (
    benchmark_json_write_path,
    benchmark_update_loop,
)


def main():
    parser = argparse.ArgumentParser(description="Benchmark AirSpaceSim simulation internals.")
    parser.add_argument("--aircraft", type=int, default=200, help="Aircraft count.")
    parser.add_argument("--steps", type=int, default=50, help="Update steps for update-loop benchmark.")
    parser.add_argument("--writes", type=int, default=25, help="Write iterations for JSON benchmark.")
    args = parser.parse_args()

    update_metrics = benchmark_update_loop(num_aircraft=args.aircraft, num_steps=args.steps)
    write_metrics = benchmark_json_write_path(num_aircraft=args.aircraft, iterations=args.writes)

    print("Update-loop benchmark:")
    for key, value in update_metrics.items():
        print(f"- {key}: {value}")

    print("\nJSON-write benchmark:")
    for key, value in write_metrics.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
