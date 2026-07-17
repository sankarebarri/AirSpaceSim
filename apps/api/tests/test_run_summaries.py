"""Phase 2: server-side separation state, practice outcomes, and run summaries."""

import time

from airspacesim.io import build_envelope

from app.db.models import RunRecord
from app.services.runs import create_run
from app.sessions import SessionRegistry
from app.sessions.practice import PracticeTracker
from app.sessions.runtime import SimulationRuntimeSession

SESSION_ID = "test-session-summaries"


def _crossing_airspace():
    return build_envelope(
        schema_name="airspacesim.scenario_airspace",
        source="tests.run_summaries",
        data={
            "reference": {
                "datum": "WGS84",
                "earth_model": "spherical",
                "nm_to_m": 1852,
            },
            "points": {
                "W1": {"type": "fix", "name": "W1", "coord": {"dd": [10.0, 0.0]}},
                "E1": {"type": "fix", "name": "E1", "coord": {"dd": [11.0, 1.0]}},
                "N1": {"type": "fix", "name": "N1", "coord": {"dd": [11.0, 0.0]}},
                "S1": {"type": "fix", "name": "S1", "coord": {"dd": [10.0, 1.0]}},
            },
            "routes": [
                {"id": "X1", "waypoint_ids": ["W1", "E1"]},
                {"id": "X2", "waypoint_ids": ["N1", "S1"]},
            ],
            "airspaces": [],
        },
    )


def _crossing_aircraft(entry_offsets=(0, 0)):
    return build_envelope(
        schema_name="airspacesim.scenario_aircraft",
        source="tests.run_summaries",
        data={
            "aircraft": [
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
        },
    )


def _build_session(metadata_payload=None, entry_offsets=(0, 0)):
    return SimulationRuntimeSession(
        run_id="summary-test-run",
        scenario_airspace=_crossing_airspace(),
        scenario_aircraft=_crossing_aircraft(entry_offsets),
        sim_rate=1.0,
        update_interval_seconds=0.01,
        metadata_payload=metadata_payload,
    )


def test_state_snapshot_includes_separation_time_and_summary():
    session = _build_session()
    snapshot = session.state_snapshot()

    assert snapshot["time_seconds"] == 0.0
    assert snapshot["separation"]["standard"] == {
        "horizontal_nm": 10.0,
        "vertical_ft": 1000.0,
    }
    assert snapshot["separation"]["active_violations"] == []
    assert snapshot["separation"]["loss_of_separation_count"] == 0
    assert snapshot["summary"]["kind"] == "simulate"
    assert snapshot["summary"]["instructions_issued"] == 0
    assert snapshot["metrics"]["pending_aircraft_count"] == 0


def test_scenario_metadata_overrides_separation_standard():
    session = _build_session(
        metadata_payload={
            "simulate": {
                "required_horizontal_separation_nm": 5,
                "required_vertical_separation_ft": 2000,
            }
        }
    )
    standard = session.state_snapshot()["separation"]["standard"]
    assert standard == {"horizontal_nm": 5.0, "vertical_ft": 2000.0}


def test_deferred_entry_reported_as_pending():
    session = _build_session(entry_offsets=(0, 60))
    metrics = session.state_snapshot()["metrics"]
    assert metrics["aircraft_count"] == 1
    assert metrics["pending_aircraft_count"] == 1


def test_practice_run_summary_kind_and_manual_terminate_outcome():
    session = _build_session(
        metadata_payload={
            "practice": {
                "conflict_pair": ["NVR231", "SKL842"],
                "required_horizontal_separation_nm": 10,
                "required_vertical_separation_ft": 1000,
            }
        }
    )
    session.start()
    time.sleep(0.1)
    session.stop()

    summary = session.run_summary()
    assert summary["kind"] == "practice"
    outcome = summary["practice_outcome"]
    assert outcome is not None
    assert outcome["reason"] == "manual_terminate"
    assert outcome["closest_horizontal_nm"] is not None


def test_practice_tracker_loss_of_separation_matches_frontend_semantics():
    tracker = PracticeTracker.from_metadata(
        {
            "practice": {
                "conflict_pair": ["A", "B"],
                "required_horizontal_separation_nm": 10,
                "required_vertical_separation_ft": 1000,
            }
        }
    )

    def state(ac_id, lat, lon, flight_level, status="active"):
        return {
            "id": ac_id,
            "position_dd": [lat, lon],
            "flight_level": flight_level,
            "status": status,
        }

    # Converging at the same level: ~30 NM apart, then ~3 NM apart.
    tracker.observe([state("A", 10.0, 0.0, 330), state("B", 10.5, 0.0, 330)])
    assert tracker.outcome is None
    tracker.observe([state("A", 10.0, 0.0, 330), state("B", 10.05, 0.0, 330)])

    assert tracker.outcome is not None
    assert tracker.outcome["reason"] == "loss_of_separation"
    assert tracker.outcome["rating"] == "loss_of_separation"
    assert tracker.outcome["separation_maintained"] is False


def test_practice_tracker_vertical_resolution_rates_safe_effective():
    tracker = PracticeTracker.from_metadata(
        {
            "practice": {
                "conflict_pair": ["A", "B"],
                "required_horizontal_separation_nm": 10,
                "required_vertical_separation_ft": 1000,
            }
        }
    )

    def state(ac_id, lat, lon, flight_level, status="active"):
        return {
            "id": ac_id,
            "position_dd": [lat, lon],
            "flight_level": flight_level,
            "status": status,
        }

    # Vertical minimum established before the pair closes horizontally,
    # then both finish: safe and effective.
    tracker.observe([state("A", 10.0, 0.0, 310), state("B", 10.05, 0.0, 330)])
    tracker.observe(
        [
            state("A", 10.0, 0.0, 310, "finished"),
            state("B", 10.05, 0.0, 330, "finished"),
        ]
    )

    assert tracker.outcome is not None
    assert tracker.outcome["reason"] == "scenario_complete"
    assert tracker.outcome["rating"] == "safe_effective"
    assert tracker.outcome["applicable_form"] == "vertical"


def test_registry_persists_summary_on_stop(db_session):
    run = create_run(db_session, session_id=SESSION_ID, name="Summary Persist Run")
    registry = SessionRegistry(
        update_interval_seconds=0.01,
        checkpoint_interval_seconds=60.0,
    )

    try:
        registry.start(run=run, scenario=None)
        time.sleep(0.05)
        registry.stop(run.id)

        db_session.expire_all()
        stored = db_session.get(RunRecord, run.id)
        assert stored.summary_json is not None
        assert stored.summary_json["kind"] == "simulate"
        assert "loss_of_separation_count" in stored.summary_json
        assert "instructions_issued" in stored.summary_json
        assert stored.summary_json["simulated_seconds"] >= 0.0
    finally:
        registry.shutdown()
