"""Phase 2 core tests: Simulation façade, clock, engine events, separation monitor.

The separation semantics table mirrors the behaviour previously implemented in
apps/web/src/lib/{conflict,simulateSummary}.ts so the server-side monitor is a
faithful port (docs/repository-audit/03 §5, 07 Phase 2 parity requirement).
"""

import pytest

from airspacesim.core import (
    SeparationMonitor,
    SeparationStandard,
    Simulation,
    SimulationClock,
)
from airspacesim.io.contracts import build_envelope


def _airspace(points, routes):
    return build_envelope(
        schema_name="airspacesim.scenario_airspace",
        source="tests.simulation_core",
        data={
            "reference": {"datum": "WGS84", "earth_model": "spherical", "nm_to_m": 1852},
            "points": points,
            "routes": routes,
            "airspaces": [],
        },
    )


def _aircraft(items):
    return build_envelope(
        schema_name="airspacesim.scenario_aircraft",
        source="tests.simulation_core",
        data={"aircraft": items},
    )


# Two straight crossing routes meeting near (10.5, 0.5), plus one short hop.
CROSSING_AIRSPACE = _airspace(
    points={
        "W1": {"type": "fix", "name": "W1", "coord": {"dd": [10.0, 0.0]}},
        "E1": {"type": "fix", "name": "E1", "coord": {"dd": [11.0, 1.0]}},
        "N1": {"type": "fix", "name": "N1", "coord": {"dd": [11.0, 0.0]}},
        "S1": {"type": "fix", "name": "S1", "coord": {"dd": [10.0, 1.0]}},
        "H1": {"type": "fix", "name": "H1", "coord": {"dd": [10.0, 0.0]}},
        "H2": {"type": "fix", "name": "H2", "coord": {"dd": [10.02, 0.0]}},
    },
    routes=[
        {"id": "X1", "waypoint_ids": ["W1", "E1"]},
        {"id": "X2", "waypoint_ids": ["N1", "S1"]},
        {"id": "HOP", "waypoint_ids": ["H1", "H2"]},
    ],
)


# ---------------------------------------------------------------- clock


def test_clock_advances_and_rejects_negative_steps():
    clock = SimulationClock()
    assert clock.now_seconds == 0.0
    assert clock.advance(1.5) == 1.5
    assert clock.advance(0) == 1.5
    with pytest.raises(ValueError):
        clock.advance(-1)


# --------------------------------------------------- separation semantics


def _state(ac_id, lat, lon, flight_level, status="active"):
    return {
        "id": ac_id,
        "position_dd": [lat, lon],
        "flight_level": flight_level,
        "status": status,
    }


@pytest.mark.parametrize(
    ("horizontal_deg", "fl_a", "fl_b", "separated"),
    [
        # Same level, far apart horizontally -> separated (horizontal OK).
        (0.5, 330, 330, True),  # 0.5 deg lat ~= 30 NM
        # Same level, close horizontally -> violation.
        (0.05, 330, 330, False),  # ~3 NM
        # Close horizontally but vertical minimum satisfied -> separated.
        (0.05, 330, 340, True),  # 1000 ft
        # Close horizontally, vertical below minimum -> violation.
        (0.05, 330, 335, False),  # 500 ft
    ],
)
def test_is_separated_or_rule_matches_frontend_semantics(
    horizontal_deg, fl_a, fl_b, separated
):
    monitor = SeparationMonitor(SeparationStandard(10.0, 1000.0))
    events = monitor.update(
        [
            _state("A", 10.0, 0.0, fl_a),
            _state("B", 10.0 + horizontal_deg, 0.0, fl_b),
        ],
        time_seconds=1.0,
    )
    if separated:
        assert events == []
        assert monitor.loss_event_count == 0
    else:
        assert [event.type for event in events] == ["separation_loss_started"]
        assert monitor.loss_event_count == 1


def test_continuous_violation_counts_once_until_restored_then_recounts():
    monitor = SeparationMonitor(SeparationStandard(10.0, 1000.0))
    close = [_state("A", 10.0, 0.0, 330), _state("B", 10.01, 0.0, 330)]
    apart = [_state("A", 10.0, 0.0, 330), _state("B", 11.0, 0.0, 330)]

    monitor.update(close, 1.0)
    for tick in range(2, 30):
        monitor.update(close, float(tick))
    assert monitor.loss_event_count == 1  # not once per tick

    ended = monitor.update(apart, 30.0)
    assert [event.type for event in ended] == ["separation_loss_ended"]
    assert ended[0].payload["started_at_seconds"] == 1.0

    restarted = monitor.update(close, 31.0)
    assert [event.type for event in restarted] == ["separation_loss_started"]
    assert monitor.loss_event_count == 2  # re-entry is a new event


def test_finished_aircraft_cannot_violate_and_ends_open_violation():
    monitor = SeparationMonitor(SeparationStandard(10.0, 1000.0))
    monitor.update(
        [_state("A", 10.0, 0.0, 330), _state("B", 10.01, 0.0, 330)], 1.0
    )
    assert monitor.loss_event_count == 1

    events = monitor.update(
        [_state("A", 10.0, 0.0, 330), _state("B", 10.01, 0.0, 330, "finished")],
        2.0,
    )
    assert [event.type for event in events] == ["separation_loss_ended"]
    assert monitor.active_violations() == []


def test_monitor_tracks_multiple_pairs_independently():
    monitor = SeparationMonitor(SeparationStandard(10.0, 1000.0))
    states = [
        _state("A", 10.0, 0.0, 330),
        _state("B", 10.01, 0.0, 330),
        _state("C", 20.0, 0.0, 330),
        _state("D", 20.01, 0.0, 330),
    ]
    events = monitor.update(states, 1.0)
    assert monitor.loss_event_count == 2
    pairs = sorted(tuple(event.payload["pair"]) for event in events)
    assert pairs == [("A", "B"), ("C", "D")]


# ------------------------------------------------------------- simulation


def _crossing_simulation(entry_offsets=(0, 0), standard=None):
    aircraft = _aircraft(
        [
            {
                "id": "NVR231",
                "callsign": "NVR231",
                "aircraft_type": "A320",
                "route_id": "X1",
                "speed_kt": 460,
                "flight_level": 330,
                "appear_after_seconds": entry_offsets[0],
            },
            {
                "id": "SKL842",
                "callsign": "SKL842",
                "aircraft_type": "B738",
                "route_id": "X2",
                "speed_kt": 430,
                "flight_level": 330,
                "appear_after_seconds": entry_offsets[1],
            },
        ]
    )
    return Simulation.from_contracts(CROSSING_AIRSPACE, aircraft, standard=standard)


def test_simulation_step_owns_deterministic_time_and_snapshots():
    first = _crossing_simulation()
    second = _crossing_simulation()
    for _ in range(40):
        first.step(5.0)
        second.step(5.0)

    assert first.clock.now_seconds == 200.0
    first_snapshot = first.snapshot(updated_utc="T")
    second_snapshot = second.snapshot(updated_utc="T")
    assert first_snapshot == second_snapshot
    assert first_snapshot["time_seconds"] == 200.0


def test_scheduled_entry_joins_at_simulated_time_and_emits_events():
    simulation = _crossing_simulation(entry_offsets=(0, 30))

    initial = [
        event for event in simulation.drain_events() if event.type == "aircraft_entered"
    ]
    assert [event.payload["aircraft_id"] for event in initial] == ["NVR231"]
    assert simulation.snapshot()["pending_aircraft_count"] == 1

    simulation.step(20.0)
    assert {item["id"] for item in simulation.snapshot()["aircraft"]} == {"NVR231"}

    simulation.step(20.0)  # crosses t=30
    snapshot = simulation.snapshot()
    assert {item["id"] for item in snapshot["aircraft"]} == {"NVR231", "SKL842"}
    assert snapshot["pending_aircraft_count"] == 0
    entered = [
        event for event in simulation.drain_events() if event.type == "aircraft_entered"
    ]
    assert [event.payload["aircraft_id"] for event in entered] == ["SKL842"]
    assert entered[0].time_seconds == 40.0


def test_crossing_traffic_produces_one_loss_event_and_commands_are_counted():
    simulation = _crossing_simulation()

    result = simulation.issue_command(
        {
            "event_id": "c1",
            "type": "SET_SPEED",
            "payload": {"aircraft_id": "NVR231", "speed_kt": 440},
        }
    )
    assert result["applied"] == ["c1"]

    for _ in range(240):  # 2 simulated hours in 30s steps: full crossing
        simulation.step(30.0)

    summary = simulation.summary()
    assert summary["instructions_issued"] == 1
    assert summary["loss_of_separation_count"] == 1  # one continuous encounter
    assert summary["aircraft_total"] == 2

    events = simulation.drain_events()
    types = [event.type for event in events]
    assert types.count("separation_loss_started") == 1
    assert types.count("separation_loss_ended") == 1
    assert types.count("aircraft_exited") == 2
    assert types[-1] == "simulation_completed"
    assert simulation.status == "completed"


def test_vertical_resolution_prevents_loss_event():
    simulation = _crossing_simulation()
    simulation.issue_command(
        {
            "event_id": "c1",
            "type": "SET_FL",
            "payload": {"aircraft_id": "NVR231", "flight_level": 310},
        }
    )
    for _ in range(240):
        simulation.step(30.0)

    assert simulation.summary()["loss_of_separation_count"] == 0


def test_snapshot_reports_active_violation_measurements():
    simulation = _crossing_simulation()
    while True:
        simulation.step(30.0)
        separation = simulation.snapshot()["separation"]
        if separation["active_violations"]:
            violation = separation["active_violations"][0]
            assert sorted(violation["pair"]) == ["NVR231", "SKL842"]
            assert violation["horizontal_nm"] < 10.0
            assert violation["vertical_ft"] == 0.0
            assert separation["standard"] == {
                "horizontal_nm": 10.0,
                "vertical_ft": 1000.0,
            }
            break
        assert simulation.status != "completed", "never came into violation"


def test_simulation_requires_batched_manager():
    from airspacesim.simulation.aircraft_manager import AircraftManager

    with pytest.raises(ValueError, match="batched"):
        Simulation(AircraftManager({}, execution_mode="thread_per_aircraft"))
