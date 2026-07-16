import pytest

from airspacesim.simulation.aircraft import Aircraft
from airspacesim.simulation.performance_database import speed_limits_kt
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


def test_aircraft_updates_flight_level_during_vertical_profile():
    ac = Aircraft(
        "AC7B",
        "R4",
        [[0.0, 0.0], [0.2, 0.0]],
        speed=300,
        flight_level=100,
        vertical_rate_fpm=1200,
    )
    ac.target_flight_level = 110

    ac.update_position(30)

    assert ac.altitude_ft == 10600
    assert ac.flight_level == 106


def test_aircraft_turns_toward_assigned_heading_before_tracking_it():
    ac = Aircraft(
        "AC7C",
        "R5",
        [[0.0, 0.0], [1.0, 0.0]],
        speed=430,
        aircraft_type="B737",
    )

    ac.assign_heading(90)
    ac.update_position(10)

    assert ac.lateral_mode == "heading"
    assert ac.assigned_heading_deg == 90
    assert ac.heading_deg == pytest.approx(24.442, abs=0.001)
    assert ac.position[1] > 0


def test_aircraft_tracks_assigned_radial_separately_from_route():
    ac = Aircraft(
        "AC7D",
        "R5",
        [[0.0, 0.0], [1.0, 0.0]],
        speed=430,
        aircraft_type="B737",
    )

    ac.assign_radial(265)
    ac.update_position(10)

    assert ac.lateral_mode == "radial"
    assert ac.assigned_radial_deg == 265
    assert ac.assigned_heading_deg == 265
    assert ac.radial_deviation_deg == -95
    assert ac.heading_deg == pytest.approx(335.558, abs=0.001)


def test_aircraft_rejects_speed_outside_type_performance_limits():
    with pytest.raises(ValueError, match="outside C208 performance range"):
        Aircraft(
            "AC7C1",
            "R5",
            [[0.0, 0.0], [1.0, 0.0]],
            speed=300,
            aircraft_type="C208",
        )


def test_aircraft_rejects_flight_level_above_type_limit():
    with pytest.raises(ValueError, match="exceeds C208 max FL250"):
        Aircraft(
            "AC7C2",
            "R5",
            [[0.0, 0.0], [1.0, 0.0]],
            speed=165,
            flight_level=300,
            aircraft_type="C208",
        )


def test_aircraft_radial_assignment_intercepts_before_tracking_line():
    ac = Aircraft(
        "AC7D2",
        "R5",
        [[0.0, 0.0], [1.0, 0.0]],
        speed=430,
        aircraft_type="B737",
    )
    ac.position = [0.5, 0.0]

    ac.assign_radial(15)
    ac.update_position(1)

    assert ac.lateral_mode == "radial_intercept"
    assert ac.radial_cross_track_nm is not None
    assert abs(ac.radial_cross_track_nm) > ac.radial_capture_tolerance_nm
    assert ac.assigned_heading_deg != ac.assigned_radial_deg


def test_aircraft_resume_route_clears_last_radial_and_intercepts_route():
    ac = Aircraft(
        "AC7E",
        "R5",
        [[0.0, 0.0], [1.0, 0.0]],
        speed=430,
        aircraft_type="B737",
    )

    ac.assign_radial(265)
    ac.resume_route()
    ac.update_position(10)

    assert ac.lateral_mode == "route_intercept"
    assert ac.assigned_radial_deg is None
    assert ac.radial_deviation_deg is None
    assert ac.assigned_heading_deg != 265


def test_aircraft_direct_to_named_fix_then_resumes_route_sequence():
    ac = Aircraft(
        "AC7F",
        "R5",
        [[0.0, 0.0], [0.0, 0.02], [0.0, 0.04]],
        speed=600,
        aircraft_type="B737",
        waypoint_ids=["A", "B", "C"],
    )

    ac.direct_to("B")
    ac.update_position(20)

    assert ac.lateral_mode == "route"
    assert ac.current_index == 1
    assert ac.direct_to_fix_id is None
    assert ac.position == [0.0, 0.02]


def test_aircraft_hold_at_fix_slows_and_turns_until_exit():
    ac = Aircraft(
        "AC7G",
        "R5",
        [[0.0, 0.0], [0.0, 0.02], [0.0, 0.04]],
        speed=430,
        aircraft_type="B737",
        waypoint_ids=["A", "B", "C"],
    )

    ac.hold_at_fix("A")
    ac.update_position(1)

    assert ac.lateral_mode == "hold"
    assert ac.hold_fix_id == "A"
    assert ac.speed == 220

    heading_in_hold = ac.heading_deg
    ac.exit_hold()

    assert ac.lateral_mode == "route_intercept"
    assert ac.hold_fix_id is None
    assert ac.speed == 430
    assert ac.heading_deg == heading_in_hold


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
        accelerated_nm = haversine(
            0.0, 0.0, accelerated.position[0], accelerated.position[1]
        )

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
        assert ac.speed == speed_limits_kt("UNKNOWN")[1]
    finally:
        settings.SPEED_GUARDRAIL_MODE = original_mode
