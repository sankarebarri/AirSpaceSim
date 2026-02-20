#!/usr/bin/env python3
"""Install AirSpaceSim editable in offline-constrained environments.

Strategy:
1) Create venv.
2) Ensure target venv has setuptools (seeded from host interpreter if missing).
3) Run editable install with no index + no build isolation.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys
import sysconfig
import venv
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _target_site_packages(python_exe: Path) -> Path:
    output = subprocess.check_output(
        [str(python_exe), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        text=True,
    ).strip()
    return Path(output)


def _has_setuptools(python_exe: Path) -> bool:
    proc = subprocess.run(
        [str(python_exe), "-c", "import setuptools"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def _copy_tree_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


def _seed_setuptools_into_venv(python_exe: Path) -> None:
    spec = importlib.util.find_spec("setuptools")
    if spec is None or spec.origin is None:
        raise RuntimeError(
            "Host interpreter does not provide setuptools. "
            "Install setuptools in host env or use a wheelhouse."
        )

    host_site = Path(spec.origin).resolve().parent.parent
    host_setuptools = host_site / "setuptools"
    host_pkg_resources = host_site / "pkg_resources"
    host_distutils_hack = host_site / "_distutils_hack"
    dist_name = importlib.metadata.distribution("setuptools").metadata["Name"]
    dist_version = importlib.metadata.version("setuptools")
    host_dist_info = host_site / f"{dist_name}-{dist_version}.dist-info"

    target_site = _target_site_packages(python_exe)
    target_site.mkdir(parents=True, exist_ok=True)

    _copy_tree_if_exists(host_setuptools, target_site / "setuptools")
    _copy_tree_if_exists(host_pkg_resources, target_site / "pkg_resources")
    _copy_tree_if_exists(host_distutils_hack, target_site / "_distutils_hack")
    _copy_tree_if_exists(host_dist_info, target_site / host_dist_info.name)

    if not _has_setuptools(python_exe):
        raise RuntimeError("Failed to seed setuptools into target venv.")


def install_offline_editable(project_root: Path, venv_dir: Path) -> None:
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(str(venv_dir))
    python_exe = _venv_python(venv_dir)

    if not _has_setuptools(python_exe):
        _seed_setuptools_into_venv(python_exe)

    _run(
        [
            str(python_exe),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-build-isolation",
            "--no-deps",
            "-e",
            str(project_root),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline editable installer for AirSpaceSim.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root containing pyproject.toml",
    )
    parser.add_argument(
        "--venv",
        type=Path,
        default=Path(".venv-offline"),
        help="Target virtual environment path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    venv_dir = args.venv.resolve()

    if not (project_root / "pyproject.toml").exists():
        print(f"ERROR: pyproject.toml not found under {project_root}", file=sys.stderr)
        return 2

    install_offline_editable(project_root, venv_dir)
    print(f"Offline editable install completed in {venv_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
