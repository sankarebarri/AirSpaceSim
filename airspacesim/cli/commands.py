"""AirSpaceSim CLI: airspace-package scaffolding.

The pre-0.2.0 `init` command that generated the legacy static-UI workspace
was retired together with that UI (git tag `pre-legacy-ui-removal` holds the
final state). `init` now scaffolds a new airspace package — the data-driven
environment format used by the hosted application:

    airspacesim init my_sector --dir airspaces --name "My Sector"

The generated package passes `scripts/validate_airspace_package.py` and can
be discovered by the hosted API immediately.
"""

import argparse
import json
import re
from pathlib import Path

PACKAGE_VERSION = "1.0.0"
DEFAULT_CENTER = [30.0, -45.0]  # neutral fictional mid-Atlantic coordinates


def _cli_info(message):
    print(message)


def _cli_error(message):
    print(message)


def _valid_package_id(value):
    if not re.match(r"^[a-z][a-z0-9_]{2,63}$", value):
        raise argparse.ArgumentTypeError(
            "Package id must be lowercase letters, digits, and underscores "
            "(for example: my_sector)."
        )
    return value


def _titleize(package_id):
    return " ".join(part.capitalize() for part in package_id.split("_"))


def _airspace_definition(package_id, name):
    center = DEFAULT_CENTER
    return {
        "schema": {"name": "airspacesim.scenario_airspace", "version": "1.0"},
        "metadata": {
            "id": package_id,
            "name": f"{name} Airspace",
            "version": PACKAGE_VERSION,
            "source_type": "fictional_training",
            "source": f"airspaces.{package_id}",
            "notes": (
                "Fictional training airspace scaffolded by `airspacesim init`. "
                "Not operationally valid."
            ),
        },
        "data": {
            "reference": {
                "datum": "WGS84",
                "earth_model": "spherical",
                "nm_to_m": 1852,
            },
            "points": {
                "CTR_VOR": {
                    "type": "navaid",
                    "name": f"{name} VOR",
                    "ident": "CTR",
                    "coord": {"dd": center},
                },
                "FIX_W": {"type": "fix", "name": "FIX_W", "coord": {"dd": [center[0], center[1] - 1.4]}},
                "FIX_E": {"type": "fix", "name": "FIX_E", "coord": {"dd": [center[0], center[1] + 1.4]}},
                "FIX_N": {"type": "fix", "name": "FIX_N", "coord": {"dd": [center[0] + 1.2, center[1]]}},
                "FIX_S": {"type": "fix", "name": "FIX_S", "coord": {"dd": [center[0] - 1.2, center[1]]}},
            },
            "routes": [
                {"id": "R1", "waypoint_ids": ["FIX_W", "CTR_VOR", "FIX_E"]},
                {"id": "R2", "waypoint_ids": ["FIX_N", "CTR_VOR", "FIX_S"]},
            ],
            "airspaces": [
                {
                    "id": f"{package_id.upper()}_CTA",
                    "type": "circle",
                    "name": f"{name}: 60 NM Training Sector",
                    "center_point_id": "CTR_VOR",
                    "radius_nm": 60,
                    "lower_limit_ft": 0,
                    "upper_limit_ft": 99999,
                }
            ],
        },
    }


def _scenario_definition(package_id):
    return {
        "schema": {"name": "airspacesim.demo_template", "version": "1.0"},
        "version": PACKAGE_VERSION,
        "metadata": {
            "name": "Basic Traffic",
            "description": (
                "Two aircraft crossing the sector on intersecting routes. "
                "Edit speeds, levels, and entry times to build your scenario."
            ),
        },
        "airspace_id": package_id,
        "aircraft": [
            {
                "id": "TRN101",
                "callsign": "TRN101",
                "aircraft_type": "A320",
                "route_id": "R1",
                "speed_kt": 430,
                "flight_level": 330,
                "appear_after_seconds": 0,
            },
            {
                "id": "TRN202",
                "callsign": "TRN202",
                "aircraft_type": "B738",
                "route_id": "R2",
                "speed_kt": 420,
                "flight_level": 350,
                "appear_after_seconds": 30,
            },
        ],
    }


def _manifest_definition(package_id, name):
    return {
        "schema": {"name": "airspacesim.airspace_package_manifest", "version": "1.0"},
        "id": package_id,
        "version": PACKAGE_VERSION,
        "name": name,
        "description": f"Fictional training airspace package: {name}.",
        "package_type": "fictional",
        "service_types": ["enroute"],
        "difficulty": "beginner",
        "training_modes": ["solo_free_practice"],
        "airspace_file": "airspace.v1.json",
        "default_scenario": "basic_traffic",
        "map": {"default_center": DEFAULT_CENTER, "default_zoom_nm": 85},
        "scenarios": [
            {
                "id": "basic_traffic",
                "title": "Basic Traffic",
                "path": "scenarios/basic_traffic.v1.json",
                "description": "Two aircraft crossing the sector on intersecting routes.",
                "service_type": "enroute",
                "training_mode": "solo_free_practice",
                "difficulty": "beginner",
            }
        ],
        "lessons": [],
    }


def _readme(package_id, name):
    return (
        f"# {name} (fictional training airspace)\n\n"
        f"Scaffolded by `airspacesim init {package_id}`. All fixes, routes, and\n"
        "coordinates are fictional and **not operationally valid**.\n\n"
        "- `package.v1.json` — package manifest (discovered by the hosted API)\n"
        "- `airspace.v1.json` — points, routes, and the training sector\n"
        "- `scenarios/basic_traffic.v1.json` — a starter scenario template\n\n"
        "Validate after editing:\n\n"
        "```bash\n"
        f"python3 scripts/validate_airspace_package.py airspaces/{package_id}\n"
        "```\n"
    )


def _write_json(path, payload, overwrite):
    if path.exists() and not overwrite:
        _cli_info(f"⚠️ Skipped (exists): {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    _cli_info(f"✅ Wrote: {path}")


def scaffold_airspace_package(package_id, *, base_dir="airspaces", name=None, overwrite=False):
    """Create a new airspace package skeleton; returns the package directory."""

    name = name or _titleize(package_id)
    package_dir = Path(base_dir) / package_id

    _write_json(
        package_dir / "package.v1.json",
        _manifest_definition(package_id, name),
        overwrite,
    )
    _write_json(
        package_dir / "airspace.v1.json",
        _airspace_definition(package_id, name),
        overwrite,
    )
    _write_json(
        package_dir / "scenarios" / "basic_traffic.v1.json",
        _scenario_definition(package_id),
        overwrite,
    )
    readme_path = package_dir / "README.md"
    if not readme_path.exists() or overwrite:
        readme_path.write_text(_readme(package_id, name))
        _cli_info(f"✅ Wrote: {readme_path}")

    _cli_info(
        f"\n🎉 Airspace package '{package_id}' scaffolded under {package_dir}/.\n"
        "Next steps: edit the fixes/routes/scenario, then validate with\n"
        f"  python3 scripts/validate_airspace_package.py {package_dir}\n"
    )
    return package_dir


def main():
    parser = argparse.ArgumentParser(
        description="AirSpaceSim CLI — scaffold airspace packages."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init", help="Scaffold a new airspace package."
    )
    init_parser.add_argument(
        "package_id",
        type=_valid_package_id,
        help="Package id (lowercase, e.g. my_sector).",
    )
    init_parser.add_argument(
        "--dir",
        default="airspaces",
        help="Directory the package folder is created under (default: airspaces).",
    )
    init_parser.add_argument("--name", help="Human-readable package name.")
    init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing files."
    )

    args = parser.parse_args()
    if args.command == "init":
        scaffold_airspace_package(
            args.package_id,
            base_dir=args.dir,
            name=args.name,
            overwrite=args.force,
        )


if __name__ == "__main__":
    main()
