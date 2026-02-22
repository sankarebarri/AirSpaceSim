# AirSpaceSim Documentation (Living Guide)

Last updated: 2026-02-22

## 1) What This Project Is

AirSpaceSim is a simulation-first Python project for:
- modeling aircraft movement along waypoint routes
- rendering airspace/routes/points on a map UI
- publishing aircraft state to JSON contracts consumed by the UI

Primary design rule:
- backend simulation and frontend UI stay independent and communicate through files/contracts only.

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
  - `id`, `callsign`, `speed_kt`, `altitude_ft`, `vertical_rate_fpm`, `route_id`, `position_dd`, `status`, `updated_utc`

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
  - configured sink from `ui_runtime.v1.json`
  - same-origin `/api/events`
  - fallback to `http://127.0.0.1:8080/.../api/events` when opened from another dev host/port

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
- `ADD_AIRCRAFT` with existing `aircraft_id` is skipped to prevent duplicate runtime instances.
- Speed updates go through guardrails in `Aircraft._sanitize_speed_kt(...)`:
  - warning above `700 kt`
  - default rejection above `1200 kt`
- Inbox event dedupe is process-local:
  - events are deduped by `event_id` during one process lifetime
  - restarting simulation re-reads existing events still present in `data/inbox_events.v1.json`
  - for a clean run, clear consumed events before restart

## 8) UI/Backend Independence Rules

- Backend output is a contract file, not a UI structure.
- UI may change styles/layout/rendering freely if contract shape is honored.
- Backend may evolve simulation internals if contract outputs remain compatible.

## 9) Current Progress Snapshot

Completed:
- Data-driven Gao airspace/routes/points integrated.
- Marker/icon behavior aligned (triangles for fixes, VOR icon for center, circle for aircraft).
- Runtime canonical aircraft state contract + atomic writes implemented.
- UI reads canonical aircraft state with legacy fallback.
- UI runtime adapter contract (`ui_runtime.v1.json`) added to map UI sources without JS code changes.
- Strict v1 contract validators implemented under `airspacesim/io/contracts.py`.
- File adapter abstraction implemented under `airspacesim/io/adapters.py`.
- Ingestion adapter interface added (`EventIngestionAdapter`) with `poll()` + optional `ack()`.
- `StdinEventAdapter` added for stream-based event ingestion.
- Event contract handling + idempotent application implemented (`inbox_events.v1.json` + `apply_events_idempotent`).
- Unified scenario contract support added (`scenario.v0.1.json`) with compatibility to split v1 files.
- Trajectory output contract added (`trajectory.v0.1.json`) and validated on write.
- Versioned JSON schema artifacts published under `airspacesim/schemas/`.
- Canonical scenario startup path implemented via `airspacesim/simulation/scenario_runner.py`.
- Conformance tests added for validators/adapters/events.
- Simulation stepping now carries residual distance across multiple segments in a single tick.
- Aircraft manager now supports explicit shutdown signaling with bounded thread joins.
- Aircraft model now supports altitude and climb/descent rate (`altitude_ft`, `vertical_rate_fpm`).
- Aircraft manager now supports batched scheduler mode for higher aircraft counts.
- Utility module stubs were implemented and duplicate route manager naming was consolidated via compatibility shim.
- Logging config no longer creates log files/directories at import time.
- Stress scenario runner added: `python -m airspacesim.examples.stress_simulation`.
- Performance benchmark runner added: `python -m airspacesim.examples.benchmark_simulation`.
- Failure-mode guide added: `docs/failure-modes.md`.
- Shared ingestion conformance tests cover file + stdin adapters (`tests/test_contracts_and_adapters.py`).
- Phase-1 clean-run smoke test added: CLI `init` + example run end-to-end (`tests/test_phase1_clean_run.py`).
- Trajectory-to-CSV interoperability exporter added (`airspacesim/io/exporters.py` + `examples/interoperability_export.py`).
- Offline editable bootstrap installer added and tested (`scripts/offline_editable_install.py` + `tests/test_offline_editable_install.py`).
- Core typed models/interfaces added (`airspacesim/core/*`) and adopted in scenario normalization + trajectory output generation.
- Framework-agnostic core guard added (`tests/test_framework_agnostic_core.py`).
- CI workflow added for Python `3.10/3.11/3.12` (`.github/workflows/ci.yml`).
- CI is configured and has passed remotely on GitHub Actions for supported Python versions (`3.10`, `3.11`, `3.12`).
- `.gitignore` now scopes runtime artifact ignores to repository-root (`/data`, `/static`, `/templates`, `/logs`) so package assets under `airspacesim/` are tracked and included in CI.
- Browser console smoke check added and wired in CI (`tests/test_browser_console_clean.py`).
- Operator controls sink pathing hardened:
  - supports `/api/events` and `/airspacesim-playground/api/events`
  - resilient fallback when UI is opened from a static-only server host/port
- Operator event handling improvements:
  - duplicate `ADD_AIRCRAFT` IDs are skipped
  - `SET_SPEED` now logs explicit hints when callsign is provided instead of aircraft ID

Pending (from `sim_ui.md`):
- none currently marked pending in `sim_ui.md`.

Current improvement backlog (post-roadmap):
- Wire `RouteRegistry` as the default resolver for flight plans/events so route chains do not require manual waypoint expansion.
- Persist ingestion checkpoints / compact inbox events so simulation restarts do not replay already-applied historical events.
- Add UI affordances that reduce operator errors:
  - route ID autocomplete from loaded scenario routes
  - aircraft ID selector for speed/reroute commands
  - de-dup warning before submitting an existing aircraft ID
- Add event outcome feedback channel from backend to UI (applied/skipped/rejected with reason) so operator panel shows authoritative result.

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
- progress snapshot section

## 12) Safety and Failure-Mode Policy

- AirSpaceSim is explicitly non-operational and non-certified.
- Do not describe the system as production-ready ATM/UTM control.
- For malformed input or invalid contracts, fail fast with explicit validator errors.
- For runtime file output, keep atomic writes enabled to avoid partial reads.
- Keep `docs/failure-modes.md` updated whenever behavior changes.
