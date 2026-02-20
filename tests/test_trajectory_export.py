import csv
import json

from airspacesim.io.exporters import export_trajectory_json_to_csv, export_trajectory_payload_to_csv


def _sample_payload():
    return {
        "schema": {"name": "airspacesim.trajectory", "version": "0.1"},
        "metadata": {"source": "test", "generated_utc": "2026-02-20T00:00:00Z"},
        "data": {
            "tracks": [
                {
                    "id": "AC1",
                    "callsign": "TEST01",
                    "route_id": "R1",
                    "position_dd": [16.25, -0.03],
                    "status": "active",
                    "speed_kt": 420,
                    "altitude_ft": 9000,
                    "vertical_rate_fpm": 0,
                    "updated_utc": "2026-02-20T00:00:00Z",
                }
            ]
        },
    }


def test_export_trajectory_payload_to_csv(tmp_path):
    csv_path = tmp_path / "trajectory.csv"
    export_trajectory_payload_to_csv(_sample_payload(), str(csv_path))

    with open(csv_path, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["id"] == "AC1"
    assert rows[0]["position_lat"] == "16.25"
    assert rows[0]["position_lon"] == "-0.03"


def test_export_trajectory_json_to_csv(tmp_path):
    json_path = tmp_path / "trajectory.v0.1.json"
    csv_path = tmp_path / "trajectory_export.csv"
    json_path.write_text(json.dumps(_sample_payload(), indent=2), encoding="utf-8")

    export_trajectory_json_to_csv(str(json_path), str(csv_path))
    assert csv_path.exists()
