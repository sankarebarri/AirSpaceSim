# Engine Usage Quickstart

This guide is for using `airspacesim` as a Python simulation engine outside the hosted web app.

For the boundary rules, see `docs/architecture/engine_boundary.md`.

## Install During Development

From the repository root:

```bash
python3 -m pip install -e .
```

This installs the reusable engine package, not the hosted API or React app.

## Basic Import

Prefer the top-level public API:

```python
from airspacesim import AircraftManager, apply_events_idempotent
```

Lower-level imports remain available:

```python
from airspacesim.simulation.aircraft_manager import AircraftManager
from airspacesim.simulation.scenario_runner import load_scenario_bundle
```

## Minimal Simulation

```python
from airspacesim import AircraftManager

routes = {
    "ROUTE_ALPHA": [
        {"id": "A", "dec_coords": [16.0, -0.4]},
        {"id": "B", "dec_coords": [16.3, 0.0]},
        {"id": "C", "dec_coords": [16.6, 0.4]},
    ]
}

manager = AircraftManager(routes=routes, execution_mode="batched")
manager.add_aircraft(
    id="AC001",
    route_name="ROUTE_ALPHA",
    callsign="TRN01",
    speed=300,
    flight_level=250,
    aircraft_type="B737",
)

manager.step_all(1.0)
track = manager.get_trajectory_payload()
```

## Apply Commands

Use canonical event payloads when you want command-style control:

```python
from airspacesim import apply_events_idempotent

events = [
    {
        "event_id": "evt-001",
        "type": "SET_HEADING",
        "payload": {"aircraft_id": "AC001", "heading_deg": 265},
    }
]

result = apply_events_idempotent(manager, events)
```

## What The Engine Should Not Need

Engine-only use should not require:

- FastAPI
- SQLAlchemy
- Uvicorn
- React
- Vite
- the hosted API database
- browser websocket sessions

Those belong to the hosted application in `apps/api/` and `apps/web/`.

## Legacy Static Demo Note

The package still ships legacy static demo assets used by `airspacesim init`.

Those assets are retained for compatibility. New hosted-app work should happen in `apps/web/`, not inside the legacy static package assets.

See `docs/architecture/legacy_static_ui_decision.md` for the current retention decision.
