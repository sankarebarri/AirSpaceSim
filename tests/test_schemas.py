import json
from pathlib import Path


def test_versioned_schema_files_exist_and_are_valid_json():
    schema_dir = Path(__file__).resolve().parents[1] / "airspacesim" / "schemas"
    required = [
        "airspacesim.scenario.v0.1.schema.json",
        "airspacesim.trajectory.v0.1.schema.json",
    ]
    for name in required:
        schema_path = schema_dir / name
        assert schema_path.exists(), f"Missing schema file: {name}"
        payload = json.loads(schema_path.read_text(encoding="utf-8"))
        assert payload.get("$schema"), f"Missing $schema in {name}"
        assert payload.get("type") == "object", f"Schema root must be object in {name}"
