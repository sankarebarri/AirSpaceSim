import os
import shutil
import argparse
from importlib import resources
import json
from pathlib import Path


def _cli_info(message):
    print(message)


def _cli_warn(message):
    print(message)


def _cli_error(message):
    print(message)


def _resolve_resource(package_path, relative_path):
    """Return the resource path if present; otherwise None."""
    candidate = package_path / relative_path
    return candidate if candidate.exists() else None


def copy_file(src, dest, overwrite=False):
    """
    Safely copy a file from package resources to the user's workspace.
    Missing source files are treated as optional and logged as warnings.
    """
    dest = Path(dest)
    if src is None:
        _cli_warn(f"⚠️ Skipped: {dest} (source missing in package)")
        return
    if overwrite or not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        action = "Updated" if overwrite and dest.exists() else "Created"
        _cli_info(f"✅ {action}: {dest}")
    else:
        _cli_warn(f"⚠️ Skipped: {dest} (already exists)")


def copy_directory_contents(src_dir, dest_dir, overwrite=False):
    """
    Copy directory contents recursively without skipping the destination
    root when it already exists.
    """
    if src_dir is None:
        _cli_warn(f"⚠️ Skipped: {dest_dir} (source directory missing in package)")
        return
    src_dir = Path(src_dir)
    dest_dir = Path(dest_dir)
    if not src_dir.exists():
        _cli_warn(f"⚠️ Skipped: {dest_dir} (source directory missing in package)")
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    for root, _, files in os.walk(src_dir):
        root_path = Path(root)
        relative_root = root_path.relative_to(src_dir)
        target_root = dest_dir / relative_root
        target_root.mkdir(parents=True, exist_ok=True)
        for filename in files:
            copy_file(root_path / filename, target_root / filename, overwrite=overwrite)


def _find_config_path():
    """
    Locate the active airspace config file in the working tree.
    Priority:
    1) data/map_config.v1.json
    2) map_config.v1.json
    3) data/airspace_config.json
    4) airspace_config.json
    5) data/gao_airspace.json (legacy)
    6) gao_airspace.json (legacy)
    7) data/gao_airspace_config.json (legacy)
    8) gao_airspace_config.json (legacy)
    """
    candidates = [
        Path.cwd() / "data" / "map_config.v1.json",
        Path.cwd() / "map_config.v1.json",
        Path.cwd() / "data" / "airspace_config.json",
        Path.cwd() / "airspace_config.json",
        Path.cwd() / "data" / "gao_airspace.json",
        Path.cwd() / "gao_airspace.json",
        Path.cwd() / "data" / "gao_airspace_config.json",
        Path.cwd() / "gao_airspace_config.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None

def initialize_project(overwrite=False):
    """Initialize a new AirSpaceSim project with default files."""
    project_dir = Path.cwd()

    _cli_info("\n🚀 Initializing AirSpaceSim project...\n")

    # Define paths inside project folder.
    templates_dir = project_dir / "templates"
    static_js_dir = project_dir / "static" / "js"
    static_css_dir = project_dir / "static" / "css"
    static_icons_dir = project_dir / "static" / "icons"
    data_dir = project_dir / "data"
    examples_dir = project_dir / "examples"

    # Create directories.
    templates_dir.mkdir(parents=True, exist_ok=True)
    static_js_dir.mkdir(parents=True, exist_ok=True)
    static_css_dir.mkdir(parents=True, exist_ok=True)
    static_icons_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)

    # Copy necessary files
    package_path = resources.files("airspacesim")

    copy_file(_resolve_resource(package_path, "templates/map.html"), templates_dir / "map.html", overwrite=overwrite)
    copy_file(
        _resolve_resource(package_path, "static/js/map_renderer.js"),
        static_js_dir / "map_renderer.js",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "static/js/aircraft_simulation.js"),
        static_js_dir / "aircraft_simulation.js",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "static/js/ui_runtime.js"),
        static_js_dir / "ui_runtime.js",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "static/css/map_styles.css"),
        static_css_dir / "map_styles.css",
        overwrite=overwrite,
    )
    copy_directory_contents(_resolve_resource(package_path, "static/icons"), static_icons_dir, overwrite=overwrite)
    copy_file(
        _resolve_resource(package_path, "data/airspace_config.json")
        or _resolve_resource(package_path, "data/gao_airspace.json"),
        data_dir / "airspace_config.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/airspace_data.json"),
        data_dir / "airspace_data.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/map_config.v1.json"),
        data_dir / "map_config.v1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/scenario_airspace.v1.json"),
        data_dir / "scenario_airspace.v1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/scenario.v0.1.json"),
        data_dir / "scenario.v0.1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/scenario_aircraft.v1.json"),
        data_dir / "scenario_aircraft.v1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/inbox_events.v1.json"),
        data_dir / "inbox_events.v1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/render_profile.v1.json"),
        data_dir / "render_profile.v1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/aircraft_data.json"),
        data_dir / "aircraft_data.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/aircraft_state.v1.json"),
        data_dir / "aircraft_state.v1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/trajectory.v0.1.json"),
        data_dir / "trajectory.v0.1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/ui_runtime.v1.json"),
        data_dir / "ui_runtime.v1.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "data/aircraft_ingest.json")
        or _resolve_resource(package_path, "data/new_aircraft.json"),
        data_dir / "aircraft_ingest.json",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "examples/example_simulation.py"),
        examples_dir / "example_simulation.py",
        overwrite=overwrite,
    )
    copy_file(
        _resolve_resource(package_path, "examples/interoperability_export.py"),
        examples_dir / "interoperability_export.py",
        overwrite=overwrite,
    )

    _cli_info("\n🎉 AirSpaceSim project initialized successfully!\n")
    _cli_info("📌 Next Steps:")
    _cli_info("1️⃣ Modify 'data/airspace_config.json' to configure your airspace.")
    _cli_info("2️⃣ Run 'python examples/example_simulation.py' to start the simulation.")
    _cli_info("3️⃣ Open 'templates/map.html' in a browser to visualize the airspace.\n")
    _cli_info("ℹ️ Need help? Check the documentation!\n")

# ------------------------------------------
# 🚀 Command: List Available Routes
# ------------------------------------------

def list_routes():
    """List all available routes from the active airspace config."""
    config_path = _find_config_path()
    if config_path is None:
        _cli_error("❌ Error: no airspace config found. Run 'airspacesim init' first.")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config_data = json.load(file)
        config_root = config_data.get("data", config_data) if isinstance(config_data, dict) else {}
        routes = [element["name"] for element in config_root.get("elements", []) if element["type"] == "polyline"]

        if not routes:
            _cli_warn("⚠️ No routes found in the configuration.")
        else:
            _cli_info("\n🛤️ Available Routes:")
            for route in routes:
                _cli_info(f"   - {route}")
    
    except json.JSONDecodeError:
        _cli_error(f"❌ Error: Invalid JSON format in '{config_path}'.")

# ------------------------------------------
# 🚀 CLI Entry Point
# ------------------------------------------
def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="AirSpaceSim Command Line Interface")
    parser.add_argument("command", choices=["init", "list-routes"], help="Command to run.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite generated files when used with the init command.",
    )

    args = parser.parse_args()

    if args.command == "init":
        initialize_project(overwrite=args.force)
    elif args.command == "list-routes":
        list_routes()

if __name__ == "__main__":
    main()
