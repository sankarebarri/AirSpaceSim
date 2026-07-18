"""`airspacesim init` scaffolds a valid airspace package (Phase 8 CLI)."""

import importlib.util
import json
from pathlib import Path

from airspacesim.cli.commands import scaffold_airspace_package


def load_validator_module():
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "validate_airspace_package.py"
    )
    spec = importlib.util.spec_from_file_location("validate_airspace_package", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scaffolded_package_passes_the_package_validator(tmp_path):
    package_dir = scaffold_airspace_package(
        "my_sector", base_dir=str(tmp_path / "airspaces"), name="My Sector"
    )

    assert (package_dir / "package.v1.json").exists()
    assert (package_dir / "airspace.v1.json").exists()
    assert (package_dir / "scenarios" / "basic_traffic.v1.json").exists()
    assert (package_dir / "README.md").exists()

    validator = load_validator_module()
    result = validator.validate_package(package_dir, require_scenarios=True)
    assert result["errors"] == []
    assert result["airspace_id"] == "my_sector"
    assert result["scenario_count"] == 1


def test_scaffold_is_idempotent_and_respects_force(tmp_path):
    base_dir = str(tmp_path / "airspaces")
    package_dir = scaffold_airspace_package("alpha_two", base_dir=base_dir)

    manifest_path = package_dir / "package.v1.json"
    manifest_path.write_text(
        json.dumps({**json.loads(manifest_path.read_text()), "description": "edited"})
    )

    # Re-running without --force keeps user edits.
    scaffold_airspace_package("alpha_two", base_dir=base_dir)
    assert json.loads(manifest_path.read_text())["description"] == "edited"

    # --force restores the scaffold.
    scaffold_airspace_package("alpha_two", base_dir=base_dir, overwrite=True)
    assert json.loads(manifest_path.read_text())["description"] != "edited"


def test_scaffolded_scenario_is_versioned_and_fictional(tmp_path):
    package_dir = scaffold_airspace_package(
        "training_two", base_dir=str(tmp_path / "airspaces")
    )
    scenario = json.loads(
        (package_dir / "scenarios" / "basic_traffic.v1.json").read_text()
    )
    airspace = json.loads((package_dir / "airspace.v1.json").read_text())

    assert scenario["version"] == "1.0.0"
    assert airspace["metadata"]["version"] == "1.0.0"
    assert airspace["metadata"]["source_type"] == "fictional_training"
    assert "not operationally valid" in airspace["metadata"]["notes"].lower()
