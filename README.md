# AirSpaceSim
Aircraft Simulation and Airspace Visualization

AirSpaceSim is a simulation-first Python library for modeling aircraft movement in structured airspace and visualizing trajectories on map-based interfaces.

## Purpose

AirSpaceSim exists to support:
- trajectory prototyping
- scenario generation for testing and research
- visualization-driven debugging
- repeatable simulation experiments

It is designed to be useful as a standalone simulator.

## Scope

Current focus:
- multi-aircraft movement simulation with per-aircraft threads
- waypoint and route processing (DMS and decimal coordinates)
- map configuration and visualization helpers (Leaflet-compatible)
- JSON-based aircraft state output for downstream tooling
- CLI bootstrap with `airspacesim init`

Non-goals:
- operational ATM/UTM control
- certified safety-critical deployment
- full 4D flight dynamics or weather-integrated ops modeling

## Installation

From PyPI:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install airspacesim
```

From source:

```bash
git clone https://github.com/sankarebarri/AirSpaceSim.git
cd AirSpaceSim
pip install -e .
```

## Quick Start

Initialize project files in your working directory:

```bash
airspacesim init
```

Then run your simulation script (for example `example_simulation.py`) and open `map.html` in a browser.

Note: in the current repository state, template/static scaffolding exists, but some CLI-seeded data/example assets referenced by `init` are not yet present in `airspacesim/data` and `airspacesim/examples`.

## Minimal Runnable Example

```python
from airspacesim.utils.conversions import dms_to_decimal, haversine

wp1 = (16, 15, 0, "N"), (0, 2, 0, "W")
wp2 = (16, 30, 0, "N"), (0, 5, 0, "E")

lat1, lon1 = dms_to_decimal(*wp1[0]), dms_to_decimal(*wp1[1])
lat2, lon2 = dms_to_decimal(*wp2[0]), dms_to_decimal(*wp2[1])

distance_nm = haversine(lat1, lon1, lat2, lon2)
print(round(distance_nm, 2))
```

## Edge-Case Example (Mixed Coordinates)

When creating aircraft routes, a waypoint can already provide decimal coordinates (`dec_coords`) while another uses DMS (`coords`). `AircraftManager.add_aircraft(...)` accepts both patterns and converts DMS waypoints during load.

```python
routes = {
    "MIXED_ROUTE": [
        {"coords": {"lat": [16, 10, 0, "N"], "lon": [0, 3, 0, "W"]}},
        {"dec_coords": [16.45, 0.08]},
    ]
}
```

## Interoperability

AirSpaceSim can act as a scenario and trajectory producer for:
- conflict modeling pipelines (for example SPECTRA)
- robustness/invariance audit pipelines (for example AIRE)
- language + trajectory paired research workflows

Planned output contracts:
- `airspacesim.trajectory.v0.1` for time-stepped aircraft state
- `airspacesim.scenario.v0.1` for route and airspace definitions

## Research vs Production Claims

Research claims:
- suitable for simulation, prototyping, and experimentation workflows
- useful for generating structured trajectory data for algorithm testing

Production claims:
- none at this stage; this repo is not positioned as operational ATM software

## Safety and Limitations

- Not an operational separation assurance system
- No regulatory assurance, certification, or operational safety case
- Results depend on scenario design and model assumptions
- Current packaging/docs need consolidation for full out-of-the-box setup

## Roadmap

Execution milestones are in `roadmap.md`.

## Ecosystem Compatibility

This project is independently usable and developed as a standalone system. It also supports interoperability with related ATC research tools through versioned data contracts and documented interfaces.
