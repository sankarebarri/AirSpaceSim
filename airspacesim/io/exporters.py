"""Export helpers for downstream interoperability workflows."""

import csv
import json

from airspacesim.io.contracts import validate_trajectory_v01


CSV_FIELDS = [
    "id",
    "callsign",
    "route_id",
    "status",
    "speed_kt",
    "flight_level",
    "altitude_ft",
    "vertical_rate_fpm",
    "position_lat",
    "position_lon",
    "updated_utc",
]


def _track_to_row(track):
    position = track.get("position_dd") or [None, None]
    return {
        "id": track.get("id"),
        "callsign": track.get("callsign"),
        "route_id": track.get("route_id"),
        "status": track.get("status"),
        "speed_kt": track.get("speed_kt"),
        "flight_level": track.get("flight_level"),
        "altitude_ft": track.get("altitude_ft"),
        "vertical_rate_fpm": track.get("vertical_rate_fpm"),
        "position_lat": position[0] if len(position) > 0 else None,
        "position_lon": position[1] if len(position) > 1 else None,
        "updated_utc": track.get("updated_utc"),
    }


def export_trajectory_payload_to_csv(payload, output_path):
    """Export validated airspacesim.trajectory.v0.1 payload to CSV."""
    validate_trajectory_v01(payload)
    rows = [_track_to_row(track) for track in payload["data"]["tracks"]]

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def export_trajectory_json_to_csv(input_json_path, output_csv_path):
    """Read trajectory JSON contract and export rows to CSV."""
    with open(input_json_path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    return export_trajectory_payload_to_csv(payload, output_csv_path)
