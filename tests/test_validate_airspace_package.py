import importlib.util
import json
import shutil
from pathlib import Path


def load_validator_module():
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "validate_airspace_package.py"
    )
    spec = importlib.util.spec_from_file_location("validate_airspace_package", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_airspace_package_accepts_existing_packages():
    validator = load_validator_module()
    root = Path(__file__).resolve().parents[1]

    nerava_result = validator.validate_package(root / "airspaces" / "nerava_fir")
    training_result = validator.validate_package(root / "airspaces" / "training_alpha")

    assert nerava_result["errors"] == []
    assert nerava_result["scenario_count"] == 2
    assert training_result["errors"] == []
    assert training_result["scenario_count"] == 10
    assert training_result["lesson_count"] == 12
    assert training_result["package_name"] == "Training Alpha"


def test_validate_airspace_package_rejects_missing_lesson_scenario(tmp_path):
    validator = load_validator_module()
    root = Path(__file__).resolve().parents[1]
    package_dir = tmp_path / "training_alpha"
    shutil.copytree(root / "airspaces" / "training_alpha", package_dir)
    (package_dir / "scenarios" / "beginner_mix.v1.json").unlink()

    result = validator.validate_package(package_dir)

    assert any(
        "references missing scenario template 'beginner_mix.v1.json'" in error
        for error in result["errors"]
    )


def test_validate_airspace_package_rejects_bad_manifest(tmp_path):
    validator = load_validator_module()
    root = Path(__file__).resolve().parents[1]
    package_dir = tmp_path / "training_alpha"
    shutil.copytree(root / "airspaces" / "training_alpha", package_dir)
    manifest_path = package_dir / "package.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["id"] = "wrong_id"
    manifest["default_scenario"] = "missing_scenario"
    manifest["lessons"][0]["scenario_id"] = "missing_scenario"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validator.validate_package(package_dir)

    assert any("must match package directory 'training_alpha'" in error for error in result["errors"])
    assert any("default_scenario 'missing_scenario'" in error for error in result["errors"])
    assert any("references unknown scenario_id 'missing_scenario'" in error for error in result["errors"])
