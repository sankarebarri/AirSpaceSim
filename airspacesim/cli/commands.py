# airspacesim/cli/commands.py
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

# ------------------------------------------
# 🚀 Command: List Available Routes
# ------------------------------------------

def list_routes():
    """List all available routes from gao_airspace_config.json."""
    config_path = os.path.join(os.getcwd(), "gao_airspace_config.json")

    if not os.path.exists(config_path):
        print("❌ Error: 'gao_airspace_config.json' not found. Run 'airspacesim init' first.")
        return

    try:
        with open(config_path, "r") as file:
            config_data = json.load(file)
        
        routes = [element["name"] for element in config_data.get("elements", []) if element["type"] == "polyline"]

        if not routes:
            print("⚠️ No routes found in the configuration.")
        else:
            print("\n🛤️ Available Routes:")
            for route in routes:
                print(f"   - {route}")
    
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format in 'gao_airspace_config.json'.")

# ------------------------------------------
# 🚀 Command: List Active Aircraft
# ------------------------------------------

# def list_aircraft():
#     """List all active aircraft from aircraft_data.json."""
#     data_path = os.path.join(os.getcwd(), "aircraft_data.json")

#     if not os.path.exists(data_path):
#         print("❌ Error: 'aircraft_data.json' not found. Run 'airspacesim init' first.")
#         return

#     try:
#         with open(data_path, "r") as file:
#             data = json.load(file)
        
#         aircraft_list = data.get("aircraft_data", [])

#         if not aircraft_list:
#             print("⚠️ No active aircraft found.")
#         else:
#             print("\n✈️ Active Aircraft:")
#             for aircraft in aircraft_list:
#                 print(f"   - ID: {aircraft['id']} | Callsign: {aircraft['callsign']} | Position: {aircraft['position']}")
    
#     except json.JSONDecodeError:
#         print("❌ Error: Invalid JSON format in 'aircraft_data.json'.")

# ------------------------------------------
# 📌 Placeholder: Future CLI Commands
# ------------------------------------------

# def add_route(name, waypoints):
#     """[Future] Add a new route to gao_airspace_config.json."""
#     print(f"🚧 Feature under development: Adding route '{name}' with waypoints {waypoints}.")

# def add_aircraft(id, route, speed):
#     """[Future] Add a new aircraft to aircraft_data.json."""
#     print(f"🚧 Feature under development: Adding aircraft '{id}' to route '{route}' at {speed} knots.")

# ------------------------------------------
# 🚀 CLI Entry Point
# ------------------------------------------
def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="AirSpaceSim Command Line Interface")
    parser.add_argument("command", choices=["init"], help="Initialize a new AirSpaceSim project.")

    args = parser.parse_args()

    if args.command == "init":
        initialize_project()

if __name__ == "__main__":
    main()