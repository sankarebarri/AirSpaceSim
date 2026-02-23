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
- multi-aircraft movement simulation with both legacy thread-per-aircraft mode and scalable batched scheduler mode
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

Offline-constrained source install (no index access):

```bash
pip install --no-build-isolation --no-deps -e .
```

If a fresh offline venv lacks `setuptools`, bootstrap it and install editable:

```bash
python3 scripts/offline_editable_install.py --venv .venv-offline
```

Offline install from local wheel:

```bash
python3 setup.py sdist bdist_wheel
pip install --no-index --find-links dist airspacesim
```

## PyPI Release Checklist

From repository root:

```bash
# 1) clean old artifacts
rm -rf dist build *.egg-info

# 2) run quality gate
pytest -q
ruff check .

# 3) build distributions
python3 -m build

# 4) verify package metadata/rendering
python3 -m twine check dist/*

# 5) upload (requires PYPI_TOKEN in env)
python3 -m twine upload dist/*
```

Recommended:
- publish first to TestPyPI with `--repository testpypi` before main PyPI.
- tag release in git after upload.
- if `python3 -m build` is unavailable in your environment, fallback build is:
  - `python3 setup.py sdist bdist_wheel`

## Quick Start

Initialize project files in your working directory:

```bash
airspacesim init
```

Then run your simulation script (for example `examples/example_simulation.py`) and open `templates/map.html` in a browser.

The default generated data files are:
- `data/map_config.v1.json`
- `data/airspace_config.json`
- `data/airspace_data.json`
- `data/scenario_airspace.v1.json`
- `data/scenario.v0.1.json`
- `data/scenario_aircraft.v1.json`
- `data/inbox_events.v1.json`
- `data/render_profile.v1.json`
- `data/aircraft_data.json`
- `data/aircraft_state.v1.json`
- `data/trajectory.v0.1.json`
- `data/ui_runtime.v1.json`
- `data/aircraft_ingest.json`

## UI Simulation Test

Run these in separate terminals from your initialized project directory:

```bash
python3 examples/example_simulation.py
```

Optional quick run:

```bash
python3 examples/example_simulation.py --max-wait 5
```

```bash
python3 dev_server.py
```

Then open one of:
- `http://127.0.0.1:8080/templates/map.html`
- `http://127.0.0.1:8080/airspacesim-playground/templates/map.html` (when running simulation from `airspacesim-playground`)

Operator controls notes:
- Use `dev_server.py` for POST support. Static-only servers (for example Live Server on `:5500`) may return `405` on `/api/events`.
- `SET_SPEED.payload.aircraft_id` must be the aircraft ID (for example `AC800`), not callsign (for example `OPS800`).
- `ADD_AIRCRAFT` now skips duplicate aircraft IDs instead of creating duplicate runtime entries.
- Speed guardrails apply:
  - warning above `700 kt`
  - rejection above `1200 kt` (default mode)

## Simulation Quality Tools

Stress scenario:

```bash
python3 -m airspacesim.examples.stress_simulation --aircraft 100 --duration 5 --speed 420
```

Performance benchmark:

```bash
python3 -m airspacesim.examples.benchmark_simulation --aircraft 200 --steps 50 --writes 25
```

Interoperability export example:

```bash
python3 examples/interoperability_export.py
```

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

Execution milestones are in `new_roadmap.md`.

Operational/developer guide is maintained in `documentation.md`.
Hands-on walkthrough is in `docs/tutorial.md`.

## Ecosystem Compatibility

This project is independently usable and developed as a standalone system. It also supports interoperability with related ATC research tools through versioned data contracts and documented interfaces.
