from pathlib import Path

from airspacesim.settings import Settings


def test_runtime_paths_default_to_workspace_data_dir(tmp_path):
    resolved = Settings(workspace_root=tmp_path)

    assert resolved.AIRCRAFT_FILE == str(tmp_path / "data" / "aircraft_data.json")
    assert resolved.AIRCRAFT_STATE_FILE == str(
        tmp_path / "data" / "aircraft_state.v1.json"
    )
    assert resolved.TRAJECTORY_FILE == str(tmp_path / "data" / "trajectory.v0.1.json")
    assert resolved.INBOX_EVENTS_FILE == str(
        tmp_path / "data" / "inbox_events.v1.json"
    )
    assert resolved.NEW_AIRCRAFT_FILE == str(
        tmp_path / "data" / "aircraft_ingest.json"
    )


def test_seed_inputs_fall_back_to_packaged_defaults_without_workspace_files(tmp_path):
    resolved = Settings(workspace_root=tmp_path)

    assert resolved.AIRSPACE_FILE == resolved.DEFAULT_AIRSPACE_FILE
    assert resolved.SCENARIO_AIRSPACE_FILE == resolved.DEFAULT_SCENARIO_AIRSPACE_FILE
    assert resolved.SCENARIO_AIRCRAFT_FILE == resolved.DEFAULT_SCENARIO_AIRCRAFT_FILE
    assert resolved.SCENARIO_FILE == resolved.DEFAULT_SCENARIO_FILE
    assert resolved.RENDER_PROFILE_FILE == resolved.DEFAULT_RENDER_PROFILE_FILE
    assert Path(resolved.AIRSPACE_FILE).exists()


def test_workspace_files_override_packaged_defaults_and_runtime_aliases(tmp_path):
    workspace_data_dir = tmp_path / "data"
    workspace_data_dir.mkdir()
    scenario_path = workspace_data_dir / "scenario_airspace.v1.json"
    legacy_ingest_path = tmp_path / "new_aircraft.json"
    scenario_path.write_text("{}", encoding="utf-8")
    legacy_ingest_path.write_text("{}", encoding="utf-8")

    resolved = Settings(workspace_root=tmp_path)

    assert resolved.SCENARIO_AIRSPACE_FILE == str(scenario_path)
    assert resolved.NEW_AIRCRAFT_FILE == str(legacy_ingest_path)
