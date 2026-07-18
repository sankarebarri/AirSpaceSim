"""README quickstart: a headless engine run writes valid contract files.

The legacy `airspacesim init` static-UI workspace flow was retired in
Phase 8; the library quickstart is now: run the example simulation from any
working directory — scenario inputs fall back to the packaged fictional
seeds and contract outputs land in `<cwd>/data/`.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_docs_quickstart_headless_engine_run_writes_contracts(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    example = repo_root / "airspacesim" / "examples" / "example_simulation.py"
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(repo_root)
        if not existing_pythonpath
        else f"{repo_root}:{existing_pythonpath}"
    )

    subprocess.run(
        [sys.executable, str(example), "--max-wait", "5"],
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
    assert len(state_payload["data"]["aircraft"]) >= 1
    assert len(trajectory_payload["data"]["tracks"]) >= 1
    # The packaged seeds are the fictional Nerava environment.
    assert state_payload["data"]["aircraft"][0]["route_id"] == "UL602"
