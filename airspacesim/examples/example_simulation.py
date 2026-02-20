"""Scenario-first AirSpaceSim simulation bootstrap."""

from airspacesim.simulation.scenario_runner import (
    apply_inbox_events_once,
    initialize_manager_from_scenarios,
    load_scenarios,
)


def main():
    scenario_airspace, scenario_aircraft = load_scenarios()
    manager = initialize_manager_from_scenarios(scenario_airspace, scenario_aircraft)
    apply_inbox_events_once(manager)
    manager.terminate_simulations()


if __name__ == "__main__":
    main()
