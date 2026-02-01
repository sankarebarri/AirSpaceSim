# AirSpaceSim: Aircraft Simulation and Airspace Visualisation

## Project Overview

AirSpaceSim is a modular Python library designed for simulating aircraft movement within defined airspaces and visualising their flight paths on an interactive map. 

Built with extensibility in mind, AirSpaceSim handles multi-threaded aircraft simulations, manages complex flight routes, and facilitates the rendering of real-time aircraft positions using a web-based map interface.

## Key Features

* **Multi-threaded Aircraft Simulation:** Simulate numerous aircraft concurrently, each following its predefined route and updating its position dynamically.
* **Waypoint-Based Route Management:** Define and manage flight paths using a series of waypoints, with support for both Degrees, Minutes, Seconds (DMS) and decimal coordinate formats.
* **Interactive Map Visualisation:** Utilises Leaflet.js to render an interactive map displaying aircraft, routes, and custom airspace elements in real-time.
* **Dynamic Aircraft Tracking:** Aircraft markers on the map are updated frequently, showing their current position, callsign, and speed.
* **Configurable Settings:** Easily customise simulation parameters, data paths, and map settings via a central configuration file.
* **Command-Line Interface (CLI) Tools:** Includes convenient commands for project initialisation (`airspacesim init`)
* **Geographical Utilities:** Provides helper functions for precise geographical calculations, including DMS to decimal conversions and Haversine distance calculations.

## Installation Instructions

To get AirSpaceSim up and running, follow these steps:

1.  **Create a Virtual Environment (Recommended):**
    It's highly recommended to use a virtual environment to manage project dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```

2.  **Installation:**

    **From Source**
    First, clone the AirSpaceSim repository to your local machine:
    ```bash
    git clone https://github.com/sankarebarri/AirSpaceSim.git
    cd AirSpaceSim
    ```
    **Using pip**
    ```bash
    pip install airspacesim
    ```


## Example Usage (How to Get Started)

Once installed, you can quickly set up and run your first simulation:

1.  **Initialise Your Project Space:**
    Use the CLI tool to set up the necessary project directories and default configuration files:
    ```bash
    airspacesim init
    ```
    This command will create (if they don't exist),  `map.html`, `map_renderer.js`, `aircraft_simulation.js`, `default_airspace_config.json`, `aircraft_data.jsonn`,
     `example_simulation.py` in your project's root.



3.  **Run the Simulation:**
    Start the aircraft manager, which will run the simulation in the background and update `aircraft_data.json`:
    ```bash
    python example_simulation.py
    ```
    You will see log messages indicating aircraft movement.

4.  **View the Map Visualisation:**
    Open the `map.html` file in your web browser. This HTML page will load the interactive map and use `airspacesim/static/js/aircraft_simulation.js` to fetch and display the real-time aircraft positions from the data(`routes and aircraft`) defined in the `example_simulation.py`

5.  **Add Your First Aircraft:**
    Open the `new_aircraft.json` file (created by `airspacesim init`) and add an entry for your aircraft, linking it to the route you just created. The simulation will pick up aircraft from this file.

    ```json
    
    {
        "aircraft": [
            {
            "id": "AC003",
            "route": "UG859",
            "callsign": "AC03"
            }
        ]
    }
    ```
