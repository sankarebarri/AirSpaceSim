"""Scenario-first AirSpaceSim simulation bootstrap."""

import argparse
import threading

from airspacesim.simulation.scenario_runner import (
    initialize_manager_from_scenarios,
    load_scenarios,
    run_inbox_events_loop,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run scenario simulation with continuous inbox event ingestion."
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        default=None,
        help="Optional timeout in seconds; omit for no timeout.",
    )
    parser.add_argument(
        "--event-poll-interval",
        type=float,
        default=1.0,
        help="Inbox event polling interval in seconds.",
    )
    args = parser.parse_args()

    scenario_airspace, scenario_aircraft = load_scenarios()
    manager = initialize_manager_from_scenarios(scenario_airspace, scenario_aircraft)
    event_thread = threading.Thread(
        target=run_inbox_events_loop,
        args=(manager,),
        kwargs={"poll_interval_seconds": args.event_poll_interval},
        daemon=True,
    )
    event_thread.start()
    try:
        manager.wait_for_completion(timeout_seconds=args.max_wait)
    finally:
        manager.request_shutdown()
        event_thread.join(timeout=2.0)
        manager.terminate_simulations()


if __name__ == "__main__":
    main()
