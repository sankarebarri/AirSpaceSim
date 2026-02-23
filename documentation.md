# AirSpaceSim Documentation (Living Guide)

Last updated: 2026-02-23

## 1) What This Project Is

AirSpaceSim is a simulation-first Python project for:
- modeling aircraft movement along waypoint routes
- rendering airspace/routes/points on a map UI
- publishing aircraft state to JSON contracts consumed by the UI

Primary design rule:
- backend simulation and frontend UI stay independent and communicate through files/contracts only.

Planning source of truth:
- `new_roadmap.md` is the only active roadmap/status tracker.
- `roadmap.md` is archived for historical reference.

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
  - `airspacesim/static/js/map_renderer.js`
  - `airspacesim/static/js/aircraft_simulation.js`
  - `airspacesim/templates/map.html`
- Data/config contracts:
  - `airspacesim/data/*.json` (package defaults)
  - `data/*.json` (workspace runtime/project overrides)
- CLI bootstrap:
  - `airspacesim/cli/commands.py` (`airspacesim init`, `airspacesim list-routes`)

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

### Legacy map fallback
- `data/gao_airspace.json`
- Purpose: legacy fallback map config.
- Modify when: only if supporting legacy readers.

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

1. Initialize project files in your working directory:
   - `airspacesim init --force`
   - for offline editable setup in fresh venvs: `python3 scripts/offline_editable_install.py --venv .venv-offline`
   - enforce no-network bootstrap behavior: `python3 scripts/offline_editable_install.py --venv .venv-offline --strict-offline`
2. Run a simulation script (example):
   - `python3 examples/example_simulation.py`
   - optional: `python3 examples/example_simulation.py --max-wait 5`
3. Serve files for browser UI:
   - `python3 dev_server.py`
4. Open:
   - `http://127.0.0.1:8080/templates/map.html`
   - if simulation runs in `airspacesim-playground/`: `http://127.0.0.1:8080/airspacesim-playground/templates/map.html`
5. For live Operator Controls, do not open map from static-only dev servers (for example `:5500`) unless they support `POST /api/events`.

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
- Do not hardcode Gao-specific assumptions into simulation core.
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

### UI compatibility
- UI polls `aircraft_state.v1.json` first.
- If unavailable, UI falls back to `aircraft_data.json`.
- UI accepts both envelope and legacy shapes for `aircraft_data.json`.
- UI loads `map_config.v1.json` first, then falls back to `airspace_config.json`.
- UI resolves data file URLs from JS module location (`static/js -> ../../data`) to match `airspacesim init` output layout.
- Poll interval is configurable via `render.map.aircraft_poll_interval_ms` in `airspace_config.json`
  (minimum 250 ms, default 1000 ms).
- If aircraft feed files are missing/unreadable, UI shows warning state and clears markers/table (recovers automatically when files return).
- Frontend endpoint mapping is driven by `data/ui_runtime.v1.json`, so backend transport/output can change without UI code edits.
- Operator controls use sink candidates with fallback:
  - when UI runs on `:8080`, same-origin sink is used first
  - when UI runs on static-only servers (for example `:5500`), controls try `http://127.0.0.1:8080/.../api/events` first, then same-origin fallback
  - repo-root `dev_server.py` now aliases `/airspacesim/{templates,static,data}/...` to `airspacesim-playground/...` when playground exists, preventing package-vs-playground data leaks
- Aircraft markers use local SVG icon rendering with flow color semantics:
  - `outbound` -> green
  - `inbound` -> red
  - `transit` -> amber
  - `unknown` -> gray
- Aircraft tooltips show `FL` labels; click marker for full metadata popup.
- FL label prefers explicit `flight_level` metadata and falls back to `altitude_ft/100` when `flight_level` is absent.
- UI side panel now includes an explicit flow-color legend so marker colors are self-explanatory.
- Operator submit buttons are debounced/disabled while command POST is in-flight to reduce accidental duplicate submissions.
- Clicking an aircraft (marker or table row) selects it, highlights it on map/table, and pre-fills `SET_SPEED`/`SET_FL` aircraft IDs.
- Operator panel shows selected-aircraft status and current FL for quick verification before sending `SET_FL`.
- ID inputs in `SET_SPEED`/`SET_FL` preserve manual edits during live refresh; autofill updates only on selection change or untouched state.
- FL input auto-suggests from current aircraft level, but manual edits are preserved (not overwritten by poll refresh while editing).

## 7.2) Simulation Units and Time-Stepping

- Authoritative units:
  - `speed_kt`: knots (NM/hour)
  - `altitude_ft`: feet
  - `vertical_rate_fpm`: feet/minute
  - `dt_seconds`: seconds
  - route geometry distance: NM (via haversine), not raw lat/lon degree deltas
- Motion update rule:
  - `distance_nm = (speed_kt / 3600) * dt_seconds * SIMULATION_SPEED`
  - `SIMULATION_SPEED` is global time acceleration (default `1.0`)
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
  - `departure=NIAMEY`, `destination=BAMAKO`, `routes=[UR981, UA612]`
  - resolved path includes turn at `GAO_VOR`
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

## 9) Planning and Status Tracking

- For all feature status, priorities, and execution tracking, use `new_roadmap.md`.
- Do not maintain progress/checklist state in this document.
- Keep this file focused on architecture, contracts, runtime behavior, and safe change workflow.

## 10) Safe Change Workflow

1. Update source contract/data files.
2. Keep UI/backend contract boundaries intact.
3. Run tests:
   - `.venv/bin/pytest -q`
   - baseline coverage is enforced (default threshold `45%`, configurable via `AIRSPACESIM_MIN_COVERAGE`)
   - browser console smoke test is opt-in locally via `AIRSPACESIM_BROWSER_SMOKE=1 pytest -q tests/test_browser_console_clean.py`
4. Do a runtime sanity check:
   - run simulation, confirm `data/aircraft_state.v1.json` updates.
5. Verify UI renders from served files.
6. Prefer `dev_server.py` for operator controls (`POST /api/events` or `POST /airspacesim-playground/api/events`) and use static servers only when command sink is not required.

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

## 13) PyPI Release Process

Run this from repository root:

1. Verify release version:
   - update `pyproject.toml` `project.version`
   - ensure version is not already published on PyPI
2. Run quality gate:
   - `pytest -q`
   - `ruff check .`
3. Build distributions:
   - `python3 -m build`
   - fallback if `build` module is not available: `python3 setup.py sdist bdist_wheel`
4. Validate package metadata:
   - `python3 -m twine check dist/*`
5. Publish:
   - TestPyPI first (recommended): `python3 -m twine upload --repository testpypi dist/*`
   - PyPI: `python3 -m twine upload dist/*`

Operational notes:
- Keep publish credentials outside git (for example, environment variables or local `~/.pypirc`).
- Do not publish from a dirty working tree.
- Tag the release after successful upload and update `CHANGELOG.md`.
