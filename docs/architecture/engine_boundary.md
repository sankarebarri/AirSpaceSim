# AirSpaceSim Engine Boundary

This document defines the reusable Python engine boundary.

## Purpose

`airspacesim/` should be usable by other Python projects without requiring the hosted API, SQLite database, websocket layer, or React frontend.

The hosted app can depend on the engine. The engine must not depend on the hosted app.

## Public Engine API

External projects should prefer these imports:

```python
from airspacesim import (
    Aircraft,
    AircraftManager,
    EngineEvent,
    ManagerStepper,
    ScenarioBundle,
    SeparationMonitor,
    SeparationStandard,
    Simulation,
    SimulationClock,
    TrajectoryTrack,
    apply_events_idempotent,
    load_scenario_bundle,
)
```

`Simulation` is the preferred entry point since 0.2.0: it owns the simulated
clock, scheduled aircraft entry, command application, general separation
monitoring (one event per continuous loss of separation), serialisable
snapshots, and the emitted engine-event stream:

```python
simulation = Simulation.from_contracts(scenario_airspace, scenario_aircraft)
simulation.issue_command({"event_id": "c1", "type": "SET_FL",
                          "payload": {"aircraft_id": "NVR231", "flight_level": 310}})
simulation.step(seconds=1.0)   # simulated seconds; caller owns pacing
snapshot = simulation.snapshot()
events = simulation.drain_events()
summary = simulation.summary()
```

Lower-level imports are still available when needed:

```python
from airspacesim.simulation.aircraft_manager import AircraftManager
from airspacesim.simulation.scenario_runner import load_scenario_bundle
from airspacesim.io.contracts import validate_scenario_airspace
```

## Engine-Owned Responsibilities

These belong in `airspacesim/`:

- aircraft state and movement
- flight level, climb, descent, and speed behavior
- turn-rate and performance lookup
- route following
- heading assignment
- radial intercept and tracking
- direct-to behavior
- hold behavior
- resume normal navigation
- scenario loading
- event application
- file contract validation
- trajectory export
- reusable calculations and conversions

## Hosted-App Responsibilities

These belong outside `airspacesim/`.

`apps/api/` owns:

- FastAPI routes
- websocket broadcasting
- hosted run lifecycle
- database persistence
- API schemas
- user/session/auth logic later
- practice-run launch endpoints later

`apps/web/` owns:

- React UI
- landing page
- lessons
- run workspace
- maps and panels
- frontend-only teaching animations
- command forms

## Forbidden Engine Dependencies

The engine should not import:

- `apps.api`
- `fastapi`
- `sqlalchemy`
- `uvicorn`
- React or frontend libraries
- hosted API configuration
- database models

## Current Legacy Assets Inside The Engine Package

The package still contains legacy browser/demo assets:

- `airspacesim/templates/`
- `airspacesim/static/`
- `airspacesim/map/`
- `airspacesim/dev_server.py`
- `airspacesim/cli/commands.py`

For now, these are retained because the packaged `airspacesim init` workflow and compatibility tests still use them.

Decision for the current cleanup phase: keep these assets in place and document them as legacy compatibility assets. Do not move or delete them until the hosted React app fully replaces that workflow and the compatibility tests are updated.

See `docs/architecture/legacy_static_ui_decision.md` for the detailed decision and retirement criteria.

Longer term, choose one of these options:

1. Keep them as a documented legacy demo feature.
2. Move them under a clearer namespace, such as `airspacesim.legacy_static`.
3. Remove them after the hosted React app fully replaces the legacy static UI.

Do not mix these legacy assets with the hosted app in `apps/web/`.

## Package Data

Package data currently includes:

- JSON data contracts and defaults
- JSON schemas
- legacy HTML templates
- legacy static JS/CSS/icons
- example Python files

Before publishing a reusable engine package, review whether legacy UI assets should still ship by default.

## Minimal Engine Example

```python
from airspacesim import AircraftManager

routes = {
    "TRAINING_ROUTE": [
        {"id": "A", "dec_coords": [16.0, -0.5]},
        {"id": "B", "dec_coords": [16.5, 0.0]},
    ]
}

manager = AircraftManager(routes=routes, execution_mode="batched")
manager.add_aircraft(
    id="AC001",
    route_name="TRAINING_ROUTE",
    callsign="TRN01",
    speed=300,
    flight_level=250,
    aircraft_type="B737",
)
manager.step_all(1.0)
```

## Current Guardrails

Tests should keep checking:

- core modules do not import UI/framework libraries
- top-level `airspacesim` imports without API/web dependencies
- the hosted app imports the engine, not the opposite
