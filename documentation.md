# AirSpaceSim Documentation (Living Guide)

Last updated: 2026-05-11

## 1) What This Project Is

AirSpaceSim is a simulation-first Python project for:
- modeling aircraft movement along waypoint routes
- rendering airspace/routes/points on a map UI
- publishing aircraft state to JSON contracts consumed by the UI

Primary design rule:
- the core simulation package stays independent from hosted app concerns
- the current compatibility path between backend and UI is files/contracts
- the target hosted path is `FastAPI + React + SQLite` with API/WebSocket transport

Planning source of truth:
- `docs/timeline.md` (milestone tags) and `docs/repository-audit/07_PHASED_REFACTOR_PLAN.md` (phase status).

## 2) Current Architecture (Practical View)

- Backend simulation:
  - `airspacesim/core/models.py`
  - `airspacesim/core/interfaces.py`
  - `airspacesim/simulation/aircraft.py`
  - `airspacesim/simulation/aircraft_manager.py`
  - Execution modes:
    - `thread_per_aircraft` (legacy compatibility)
    - `batched` (single-loop scheduler for larger fleets)
- UI rendering:
  - `apps/web/` (React frontend; the legacy static UI was retired in 0.2.0,
    preserved at git tag `pre-legacy-ui-removal`)
- Data/config contracts:
  - `airspacesim/data/*.json` (package defaults)
  - `data/*.json` (workspace runtime/project overrides)
- CLI:
  - `airspacesim/cli/commands.py` (`airspacesim init` scaffolds airspace packages)
- Hosted app scaffold:
  - `apps/api/` (FastAPI service)
  - `apps/web/` (React frontend)

## 3) File Responsibilities

### Airspace authoring
- `data/airspace_data.json`
- Purpose: source of truth for airspace, waypoints, routes, zones, navaids.
- Modify when: changing domain content (routes, points, coordinates).

### UI map config
- `data/airspace_config.json`
- Purpose: UI-renderable map elements (`polyline`, `circle`, `marker`) plus optional `render` style profile.
- Modify when: changing map style/layer behavior or selecting what is rendered.

### UI map config (versioned)
- `data/map_config.v1.json`
- Purpose: versioned envelope for map config contract.
- Preferred by frontend when available; falls back to `airspace_config.json`.

### Runtime aircraft (legacy)
- `data/aircraft_data.json`
- Purpose: legacy aircraft snapshot consumed by older UI behavior.
- Now includes a v1 schema envelope (`airspacesim.aircraft_data`) plus a root-level compatibility shim.

### Runtime aircraft (canonical)
- `data/aircraft_state.v1.json`
- Purpose: canonical runtime state contract with schema envelope.
- Written atomically by backend; preferred by UI.

### Runtime trajectory (canonical)
- `data/trajectory.v0.1.json`
- Purpose: versioned trajectory/state output contract for simulation consumers.
- Written atomically by backend each simulation save cycle.

### Aircraft ingest
- `data/aircraft_ingest.json`
- Purpose: queue for adding aircraft dynamically.
- Modify when: injecting new aircraft commands.

### Unified scenario input
- `data/scenario.v0.1.json`
- Purpose: single-file scenario startup contract (airspace + aircraft).
- Preferred by scenario loader when present; legacy split scenario files remain supported.

## 4) How To Run

Hosted application (recommended):

1. `docker compose up --build` (or `python3 scripts/start_hosted_dev.py --seed`)
2. Open `http://127.0.0.1:8080` (compose) or `http://127.0.0.1:5174` (dev servers).

Headless engine run:

1. `python3 -m airspacesim.examples.example_simulation --max-wait 5`
   from any working directory (outputs land in `<cwd>/data/`).
2. Offline editable setup for fresh venvs:
   `python3 scripts/offline_editable_install.py --venv .venv-offline`.

> The legacy static-UI run flow (`airspacesim init` workspace + `dev_server.py`
> + `templates/map.html`) was retired in 0.2.0; see git tag
> `pre-legacy-ui-removal`.

## 5) What To Modify (and When)

- Modify `airspace_data.json` when changing operational airspace content.
- Modify `airspace_config.json` when changing rendered layers/styles/marker icons.
- Modify `aircraft_simulation.js` only for UI read/mapping logic (never simulation behavior).
- Modify `aircraft_manager.py` for simulation runtime behavior and contract writes.
- Modify `settings.py` when adding new canonical file path resolution.

## 5.1) Contract Ownership Boundaries

- Airspace authoring owns:
  - waypoint definitions
  - route/airway sequences
  - airspace geometry and metadata
- Simulation backend owns:
  - motion physics
  - stepping/time model
  - resolved aircraft paths and runtime outputs
- UI owns:
  - rendering
  - polling cadence and view behavior
  - operator presentation and interaction

## 6) What Not To Touch Casually

- Do not couple backend to Leaflet/UI code.
- Do not make UI import Python internals directly.
- Do not remove atomic write behavior in runtime state output.
- Do not hardcode environment-specific assumptions into the simulation core (public data uses the fictional Nerava environment).
- Do not break legacy fallback reads unless migration is complete and intentional.

## 7) Data Contract Notes

### Canonical runtime state (`aircraft_state.v1.json`)
- Envelope:
  - `schema.name = airspacesim.aircraft_state`
  - `schema.version = 1.0`
  - `metadata.source`
  - `metadata.generated_utc`
  - `data.aircraft[]`
- Aircraft item includes:
  - `id`, `callsign`, `speed_kt`, `flight_level`, `altitude_ft`, `vertical_rate_fpm`, `route_id`, `position_dd`, `status`, `updated_utc`

### UI compatibility (retired)

The static-UI polling/fallback behaviour documented here was retired in
0.2.0 together with the legacy UI (git tag `pre-legacy-ui-removal`). The
hosted React frontend consumes the API/WebSocket state instead.

## 7.2) Simulation Units and Time-Stepping

- Authoritative units:
  - `speed_kt`: knots (NM/hour)
  - `altitude_ft`: feet
  - `vertical_rate_fpm`: feet/minute
  - `dt_seconds`: seconds
  - route geometry distance: NM (via haversine), not raw lat/lon degree deltas
- Motion update rule:
  - `distance_nm = (speed_kt / 3600) * simulated_seconds`
  - Time acceleration is per-manager since 0.2.0: `AircraftManager(sim_rate=...)` /
    `set_simulation_speed()` scale simulated seconds per tick. The old global
    `settings.SIMULATION_SPEED` was removed.
- Guardrails:
  - warn above `REALISTIC_ENROUTE_SPEED_WARNING_KTS` (default `700`)
  - reject/clamp/off behavior controlled by `SPEED_GUARDRAIL_MODE`
  - hard absurd threshold `MAX_ABSURD_SPEED_KTS` (default `1200`)
- Implemented in:
  - `airspacesim/simulation/aircraft.py`
  - tested in `tests/test_aircraft.py` (`480 kt ~= 480 NM in 1 sim hour`, `10x acceleration` equivalence)

## 7.3) Route Registry and Flight Plan Resolution

- `RouteRegistry` maps `route_id -> ordered waypoint IDs` and resolves route chains deterministically.
- `FlightPlan` contract:
  - `departure_id`
  - `destination_id`
  - `route_ids` (ordered)
- Consecutive route stitching:
  - if no intersection: raise `RouteResolutionError`
  - if multiple intersections: choose deterministic shortest/ordered candidate and log selection
- Example:
  - `departure=VESTA`, `destination=TARUM`, `routes=[UT88, UL602]`
  - resolved path includes turn at `NRV_VOR`
- Current integration status:
  - registry + tests implemented in `airspacesim/routes/registry.py` and `tests/test_route_registry.py`
  - not yet wired as the default path resolver inside runtime scenario/event pipelines

## 7.4) Operator Event Runtime Behavior

- `SET_SPEED.payload.aircraft_id` expects aircraft ID, not callsign.
  - Example:
    - valid: `AC800`
    - invalid for this field: `OPS800` (callsign)
- `SET_FL.payload.aircraft_id` follows the same rule (runtime aircraft ID only).
- `ADD_AIRCRAFT` with existing `aircraft_id` is skipped to prevent duplicate runtime instances.
- `ADD_AIRCRAFT.payload.flight_level` is optional metadata (display only, no motion/physics effect).
- `SET_FL` updates display FL metadata at runtime (no effect on speed, route progression, or vertical physics).
- UI pre-check warns before sending `ADD_AIRCRAFT` when entered `aircraft_id` already exists in runtime state.
- Speed updates go through guardrails in `Aircraft._sanitize_speed_kt(...)`:
  - warning above `700 kt`
  - default rejection above `1200 kt`
- `traffic_flow` is published in `aircraft_state.v1.json` and derived from route geometry against configured airspace center.
- Inbox event dedupe is process-local:
  - events are deduped by `event_id` during one process lifetime
  - restarting simulation re-reads existing events still present in `data/inbox_events.v1.json`
  - for a clean run, clear consumed events before restart

## 8) UI/Backend Independence Rules

- Backend output is a contract file, not a UI structure.
- UI may change styles/layout/rendering freely if contract shape is honored.
- Backend may evolve simulation internals if contract outputs remain compatible.
- Hosted migration rule:
  - browser-facing hosted runtime should move to API/WebSocket transport rather than shared filesystem polling

## 9) Planning and Status Tracking

- For all active status and execution tracking, use `docs/timeline.md` and `docs/repository-audit/07_PHASED_REFACTOR_PLAN.md`.
- `docs/improvements/` holds superseded planning documents kept for history.
- Do not maintain progress/checklist state in this document.
- Keep this file focused on architecture, contracts, runtime behavior, and safe change workflow.

## 10) Safe Change Workflow

1. Update source contract/data files.
2. Keep UI/backend contract boundaries intact.
3. Run tests:
   - `.venv/bin/pytest -q` (baseline coverage enforced, default `45%`,
     configurable via `AIRSPACESIM_MIN_COVERAGE`)
   - hosted browser smoke is opt-in via
     `AIRSPACESIM_BROWSER_SMOKE=1 pytest -q tests/test_hosted_browser_flow.py`
4. Do a runtime sanity check:
   - headless engine run writes `data/aircraft_state.v1.json`, or the hosted
     stack passes `scripts/smoke_hosted_app.py`.

## 11) Documentation Maintenance Rule

This file is a living guide. On each meaningful change, update:
- impacted files/ownership
- contract behavior changes
- what is now safe/unsafe to modify
- and the linked roadmap location if tracking conventions change.

## 12) Safety and Failure-Mode Policy

- AirSpaceSim is explicitly non-operational and non-certified.
- Do not describe the system as production-ready ATM/UTM control.
- For malformed input or invalid contracts, fail fast with explicit validator errors.
- For runtime file output, keep atomic writes enabled to avoid partial reads.
- Keep `docs/failure-modes.md` updated whenever behavior changes.
