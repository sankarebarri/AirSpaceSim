import os
import subprocess
import sys
from pathlib import Path


def test_offline_editable_install_script(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "offline_editable_install.py"
    venv_dir = tmp_path / "offline-venv"

    env = dict(os.environ)
    # Ensure script imports from repository source tree.
    env["PYTHONPATH"] = str(repo_root)

    subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--project-root",
            str(repo_root),
            "--venv",
            str(venv_dir),
        ],
        check=True,
        env=env,
        timeout=120,
    )

    venv_python = (
        venv_dir
        / ("Scripts" if sys.platform == "win32" else "bin")
        / ("python.exe" if sys.platform == "win32" else "python")
    )
    proc = subprocess.run(
        [str(venv_python), "-c", "import airspacesim, setuptools; print('ok')"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "ok" in proc.stdout
