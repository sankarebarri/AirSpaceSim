import os
import shutil
import argparse
from importlib import resources

def copy_file(src, dest):
    """Safely copy a file from package resources to the user's workspace."""
    if not os.path.exists(dest):
        shutil.copyfile(src, dest)
        print(f"✅ Created: {dest}")
    else:
        print(f"⚠️ Skipped: {dest} (already exists)")

def copy_directory(src, dest):
    """Recursively copy a directory from package resources to the user's workspace."""
    if not os.path.exists(dest):
        shutil.copytree(src, dest)
    else:
        print(f"⚠️ Skipped: {dest} (already exists)")

def initialize_project():
    """Initialize a new AirSpaceSim project with default files."""
    # project_dir = os.path.join(os.getcwd(), "airspacesim_project")
    project_dir = os.path.join(os.getcwd())
    os.makedirs(project_dir, exist_ok=True)

    print("\n🚀 Initializing AirSpaceSim project...\n")

    # Define paths inside project folder
    # templates_dir = os.path.join(project_dir, "templates")
    # static_js_dir = os.path.join(project_dir, "static", "js")
    # static_icons_dir = os.path.join(project_dir, "static", "icons")
    # data_dir = os.path.join(project_dir, "data")

    templates_dir = os.path.join(project_dir)
    static_js_dir = os.path.join(project_dir)
    static_icons_dir = os.path.join(project_dir)
    data_dir = os.path.join(project_dir)

    # Create directories
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_js_dir, exist_ok=True)
    os.makedirs(static_icons_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)


    # Copy necessary files
    package_path = resources.files("airspacesim")

    copy_file(package_path / "templates/map.html", os.path.join(templates_dir, "map.html"))
    copy_file(package_path / "static/js/map_renderer.js", os.path.join(static_js_dir, "map_renderer.js"))
    copy_file(package_path / "static/js/aircraft_simulation.js", os.path.join(static_js_dir, "aircraft_simulation.js"))
    copy_directory(package_path / "static/icons", static_icons_dir)
    copy_file(package_path / "data/gao_airspace_config.json.example", os.path.join(data_dir, "gao_airspace_config.json"))
    copy_file(package_path / "data/aircraft_data.json", os.path.join(data_dir, "aircraft_data.json"))
    copy_file(package_path / "examples/example_simulation.py", os.path.join(project_dir, "example_simulation.py"))

    print("\n🎉 AirSpaceSim project initialized successfully!\n")
    print("📌 Next Steps:")
    print("1️⃣ Modify 'gao_airspace_config.json' to configure your airspace.")
    print("2️⃣ Run 'python example_simulation.py' to start the simulation.")
    print("3️⃣ Open 'map.html' in a browser to visualize the airspace.\n")
    print("ℹ️ Need help? Check the documentation!\n")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="AirSpaceSim Command Line Interface")
    parser.add_argument("command", choices=["init"], help="Initialize a new AirSpaceSim project.")

    args = parser.parse_args()

    if args.command == "init":
        initialize_project()

if __name__ == "__main__":
    main()