# AirSpaceSim Documentation (Living Guide)

Last updated: 2026-02-20

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
   - `python3 -m http.server 8000`
4. Open:
   - `http://127.0.0.1:8000/templates/map.html`

## 5) What To Modify (and When)

- Modify `airspace_data.json` when changing operational airspace content.
- Modify `airspace_config.json` when changing rendered layers/styles/marker icons.
- Modify `aircraft_simulation.js` only for UI read/mapping logic (never simulation behavior).
- Modify `aircraft_manager.py` for simulation runtime behavior and contract writes.
- Modify `settings.py` when adding new canonical file path resolution.

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
- CI currently configured locally; remote GitHub run confirmation is still pending.
- `.gitignore` now scopes runtime artifact ignores to repository-root (`/data`, `/static`, `/templates`, `/logs`) so package assets under `airspacesim/` are tracked and included in CI.

Pending (from `sim_ui.md`):
- none currently marked pending in `sim_ui.md`.

Roadmap simulation work still pending (from `roadmap.md`):
- none in Phase 3 currently.

## 10) Safe Change Workflow

1. Update source contract/data files.
2. Keep UI/backend contract boundaries intact.
3. Run tests:
   - `.venv/bin/pytest -q`
   - baseline coverage is enforced (default threshold `45%`, configurable via `AIRSPACESIM_MIN_COVERAGE`)
4. Do a runtime sanity check:
   - run simulation, confirm `data/aircraft_state.v1.json` updates.
5. Verify UI renders from served files.

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
