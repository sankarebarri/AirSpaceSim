# AirSpaceSim
Aircraft Simulation and Airspace Visualization

AirSpaceSim is an air traffic learning and simulation platform built on a reusable simulation engine:
- `airspacesim/` — the standalone Python engine package (published to PyPI)
- `apps/api/` — the FastAPI service layer
- `apps/web/` — the React frontend (Learn / Practice / Simulate)
- `airspaces/` + `content/` — data-driven airspace packages and curriculum

Training and visualisation software only — not for operational use. All
airspaces and scenarios are fictional.

## Purpose

AirSpaceSim exists to support:
- trajectory prototyping
- scenario generation for testing and research
- visualization-driven debugging
- repeatable simulation experiments

It is designed to be useful as a standalone simulator.

## Scope

Current focus:
- deterministic multi-aircraft simulation (`Simulation` façade: clock, commands, separation monitoring, engine events)
- waypoint and route processing (DMS and decimal coordinates)
- versioned JSON contracts for scenarios, state, and trajectories
- hosted Learn/Practice/Simulate application on the same engine
- `airspacesim init` scaffolding for data-driven airspace packages

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
python3 -m build
pip install --no-index --find-links dist airspacesim
```

## Quick Start (hosted application)

Full stack with Docker (PostgreSQL + API + web):

```bash
cp .env.example .env
docker compose up --build
# Web: http://127.0.0.1:8080   API health: http://127.0.0.1:8000/health
```

Or without Docker (SQLite + dev servers):

```bash
python3 scripts/start_hosted_dev.py --seed
```

See `docs/developer/DEPLOYMENT.md` for hosting.

## Quick Start (engine library)

Run a headless simulation from any directory — scenario inputs fall back to
the packaged fictional Nerava seeds and contract outputs are written to
`<cwd>/data/`:

```bash
python3 -m airspacesim.examples.example_simulation --max-wait 5
```

Or drive the engine directly:

```python
from airspacesim import Simulation
from airspacesim.simulation.scenario_runner import load_scenarios

airspace, aircraft = load_scenarios()
simulation = Simulation.from_contracts(airspace, aircraft)
simulation.step(seconds=60)
snapshot = simulation.snapshot()
```

More in `docs/architecture/engine_usage_quickstart.md`.

Scaffold a new airspace package (the data-driven environment format used by
the hosted app):

```bash
airspacesim init my_sector --dir airspaces
```

> The pre-0.2.0 static HTML/JS map UI, file-based dev server, and generated
> workspace were retired; their final state is preserved at the git tag
> `pre-legacy-ui-removal` (see `docs/migration.md`).

Engine behaviour notes:
- `SET_SPEED.payload.aircraft_id` must be the aircraft ID, not the callsign.
- `ADD_AIRCRAFT` skips duplicate aircraft IDs instead of creating duplicates.
- Speed guardrails apply: warning above `700 kt`, rejection above `1200 kt`
  (default mode).

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
python3 -m airspacesim.examples.interoperability_export
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

## Roadmap and documentation

The refactor phases, decisions, and milestone tags are tracked in
`docs/timeline.md` and `docs/repository-audit/`.

Developer guides live under `docs/developer/` (authentication, database,
deployment); engine architecture notes under `docs/architecture/`;
user-facing guides under `docs/user/`.

## Ecosystem Compatibility

This project is independently usable and developed as a standalone system. It also supports interoperability with related ATC research tools through versioned data contracts and documented interfaces.
