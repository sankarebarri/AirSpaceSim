import pytest

from airspacesim.simulation.aircraft import Aircraft
from airspacesim.settings import settings
from airspacesim.utils.conversions import haversine


def test_aircraft_advances_within_segment():
    ac = Aircraft("AC1", "R1", [[0.0, 0.0], [1.0, 0.0]], speed=60)

    # At 60 knots, 60 sec should move ~1 NM; definitely not complete 1-degree segment.
    ac.update_position(60)

    assert ac.current_index == 0
    assert ac.position != [0.0, 0.0]


def test_aircraft_reaches_next_waypoint_on_large_step():
    ac = Aircraft("AC2", "R1", [[0.0, 0.0], [0.05, 0.0]], speed=600)

    # Large enough step to complete this short segment.
    ac.update_position(3600)

    assert ac.current_index == 1
    assert ac.position == [0.05, 0.0]


def test_aircraft_respects_simulation_speed_multiplier():
    original = settings.SIMULATION_SPEED
    try:
        settings.SIMULATION_SPEED = 2.0
        ac_fast = Aircraft("AC3", "R1", [[0.0, 0.0], [1.0, 0.0]], speed=60)
        ac_fast.update_position(60)

        settings.SIMULATION_SPEED = 1.0
        ac_normal = Aircraft("AC4", "R1", [[0.0, 0.0], [1.0, 0.0]], speed=60)
        ac_normal.update_position(60)

        assert ac_fast.position[0] > ac_normal.position[0]
    finally:
        settings.SIMULATION_SPEED = original


def test_aircraft_carries_over_distance_across_multiple_segments():
    # Route with two short segments where one update should traverse both.
    ac = Aircraft(
        "AC5",
        "R2",
        [
            [0.0, 0.0],
            [0.05, 0.0],
            [0.1, 0.0],
        ],
        speed=600,
    )

    # Large enough timestep to cross >1 segment at once.
    ac.update_position(3600)

    assert ac.current_index == 2
    assert ac.position == [0.1, 0.0]


def test_aircraft_skips_zero_length_segment():
    ac = Aircraft(
        "AC6",
        "R3",
        [
            [10.0, 10.0],
            [10.0, 10.0],  # Zero-length segment.
            [10.05, 10.0],
        ],
        speed=300,
    )

    ac.update_position(3600)

    assert ac.current_index >= 1
    assert ac.position != [10.0, 10.0]


def test_aircraft_updates_altitude_with_vertical_rate():
    ac = Aircraft(
        "AC7",
        "R4",
        [[0.0, 0.0], [0.2, 0.0]],
        speed=300,
        altitude_ft=10000,
        vertical_rate_fpm=1200,
    )

    # 30 seconds at +1200 fpm -> +600 ft.
    ac.update_position(30)

    assert round(ac.altitude_ft, 3) == 10600


def test_aircraft_480kt_moves_about_480nm_in_one_sim_hour():
    ac = Aircraft("AC8", "R5", [[0.0, 0.0], [0.0, 20.0]], speed=480)
    ac.update_position(3600)

    travelled_nm = haversine(0.0, 0.0, ac.position[0], ac.position[1])
    assert travelled_nm == pytest.approx(480, abs=1.0)


def test_time_acceleration_changes_wall_clock_only_not_physics():
    original = settings.SIMULATION_SPEED
    try:
        # Baseline: 1x simulation, 3600 real seconds.
        settings.SIMULATION_SPEED = 1.0
        baseline = Aircraft("AC9", "R6", [[0.0, 0.0], [0.0, 20.0]], speed=480)
        baseline.update_position(3600)
        baseline_nm = haversine(0.0, 0.0, baseline.position[0], baseline.position[1])

        # Accelerated: 10x simulation, 360 real seconds -> same 3600 simulated seconds.
        settings.SIMULATION_SPEED = 10.0
        accelerated = Aircraft("AC10", "R6", [[0.0, 0.0], [0.0, 20.0]], speed=480)
        accelerated.update_position(360)
        accelerated_nm = haversine(0.0, 0.0, accelerated.position[0], accelerated.position[1])

        assert accelerated_nm == pytest.approx(baseline_nm, abs=0.1)
    finally:
        settings.SIMULATION_SPEED = original


def test_absurd_speed_rejected_by_default_guardrail():
    with pytest.raises(ValueError):
        Aircraft("AC11", "R7", [[0.0, 0.0], [0.1, 0.0]], speed=2000)


def test_absurd_speed_can_be_clamped_when_enabled():
    original_mode = settings.SPEED_GUARDRAIL_MODE
    try:
        settings.SPEED_GUARDRAIL_MODE = "clamp"
        ac = Aircraft("AC12", "R8", [[0.0, 0.0], [1.0, 0.0]], speed=2000)
        assert ac.speed == settings.MAX_ABSURD_SPEED_KTS
    finally:
        settings.SPEED_GUARDRAIL_MODE = original_mode
