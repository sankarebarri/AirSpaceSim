import json
import os
import subprocess
import sys
from pathlib import Path


def test_phase1_clean_init_and_sample_run_via_cli(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(repo_root)
        if not existing_pythonpath
        else f"{str(repo_root)}:{existing_pythonpath}"
    )

    subprocess.run(
        [sys.executable, "-m", "airspacesim.cli.commands", "init", "--force"],
        cwd=tmp_path,
        env=env,
        check=True,
        timeout=30,
    )

    subprocess.run(
        [sys.executable, "examples/example_simulation.py", "--max-wait", "5"],
        cwd=tmp_path,
        env=env,
        check=True,
        timeout=30,
    )

    state_payload = json.loads(
        (tmp_path / "data" / "aircraft_state.v1.json").read_text(encoding="utf-8")
    )
    trajectory_payload = json.loads(
        (tmp_path / "data" / "trajectory.v0.1.json").read_text(encoding="utf-8")
    )

    assert state_payload["schema"]["name"] == "airspacesim.aircraft_state"
    assert trajectory_payload["schema"]["name"] == "airspacesim.trajectory"
