# Simulation + UI Contract Plan (v1)

This document captures the agreed direction for a scalable, data-driven, UI/backend-decoupled AirSpaceSim architecture.
Roadmap/status tracking lives in `new_roadmap.md` (single source of truth).

## Capability Snapshot (technical state only)

- Data-driven airspace files (`airspace_data.json` + `airspace_config.json`) drive rendering.
- Coordinate fallback (`dec_coords` then DMS conversion) is in place.
- UI/backend separation: backend does not import Leaflet; UI reads JSON files only.
- Runtime canonical state file is `data/aircraft_state.v1.json`.
- Atomic write behavior is used for runtime aircraft outputs.
- UI polls canonical `aircraft_state.v1.json` first, with legacy fallback to `aircraft_data.json`.
- Strict schema validators are in place for v1 contracts.
- Event contract + idempotent event application uses `inbox_events.v1.json`.
- Canonical startup contracts (`scenario_airspace.v1.json`, `scenario_aircraft.v1.json`) are primary runtime inputs.
- Adapter abstraction layer exists (file snapshot/event adapters).
- Conformance tests cover contracts and adapters.
- Aircraft map markers use SVG aircraft icon with flow colors (`outbound` green, `inbound` red).
- Aircraft tooltip labels show flight level (`FL`) instead of speed.
- Aircraft metadata popup is available on marker click.
- Flight level (`flight_level`) is editable from Operator Controls (`ADD_AIRCRAFT` + `SET_FL`) as metadata-only.
- Operator forms debounce submits while POST is in-flight to reduce duplicate commands.
- UI includes a flow-color legend and explicit `aircraft_id` hint for speed changes.
- Selecting an aircraft highlights it on map/table and pre-fills operator forms (`SET_SPEED`, `SET_FL`).

## Core Decisions

1. Data-driven architecture
- No hardcoded airspace assumptions in core logic.
- Core simulation consumes versioned JSON contracts only.

2. Canonical coordinates
- Canonical engine/storage coordinate format: decimal degrees (`dd`).
- Optional source trace fields may include original DMS (`source_dms`) for audit/debug.
- Renderer and simulation use canonical `dd`.

3. Backend/UI decoupling
- Backend never depends on Leaflet or UI-specific structures.
- UI consumes stable output contracts only.
- Rendering hints are optional and externalized.

4. Event-driven ingestion
- Inbound aircraft updates use event contracts.
- Idempotency via `event_id`.
- Deterministic application order via `sequence` + timestamp.

5. Stable runtime state contract
- Simulation publishes a consistent `aircraft_state` file with schema envelope.
- UI polls this contract and does not read internal Python structures.

6. Safe writes for UI polling
- State/output files are written via temp file + atomic rename.
- Prevents partial reads and corrupted UI updates.

## Contract Set (v1)

1. `scenario_airspace.v1.json`
- Domain truth: points, routes, airspaces, reference metadata.

2. `scenario_aircraft.v1.json`
- Initial aircraft set at simulation start.

3. `inbox_events.v1.json`
- Mid-sim commands/events (`ADD_AIRCRAFT`, `SET_SPEED`, `SET_FL`, `REMOVE_AIRCRAFT`, `REROUTE`).

4. `aircraft_state.v1.json`
- Runtime aircraft snapshot for UI and downstream tools.

5. `render_profile.v1.json` (optional)
- UI rendering/layer/style hints.
- Fully optional; backend must run without it.

## Envelope Requirements (all contracts)

```json
{
  "schema": {
    "name": "airspacesim.<domain>",
    "version": "1.0"
  },
  "metadata": {
    "source": "string",
    "generated_utc": "ISO-8601"
  },
  "data": {}
}
```

## Minimum Validation Rules

1. Airspace/route validation
- Every `waypoint_id` in routes must exist in `points`.
- Routes must contain at least 2 waypoints.

2. Aircraft scenario validation
- Unique aircraft IDs.
- `route_id` must exist.
- `speed_kt > 0`.

3. Event validation
- Required: `event_id`, `type`, `created_utc`, `payload`.
- Ignore duplicates by `event_id`.
- Reject unknown `type` unless explicitly configured.

4. Aircraft state validation
- Required fields: `id`, `position_dd`, `status`, `updated_utc`.
- `position_dd` must be valid `[lat, lon]`.

## Recommended Processing Flow

1. Startup
- Load and validate `scenario_airspace.v1.json`.
- Load and validate `scenario_aircraft.v1.json`.
- Initialize simulation entities.

2. Tick loop
- Advance aircraft by distance-time logic (`speed_kt * dt / 3600`).
- Apply pending validated events in deterministic order.
- Publish `aircraft_state.v1.json` atomically.

3. UI loop
- Poll `aircraft_state.v1.json`.
- Render aircraft, metadata, and status panels.
- Optionally load `render_profile.v1.json` for styling/layers.

## Separation Rules

1. Simulation core
- Handles physics/trajectory/state transitions only.
- No map rendering assumptions.

2. IO layer
- Handles contract loading, schema checks, atomic writes, adapter abstraction.

3. UI layer
- Reads contracts, draws map/layers/panels.
- Never imports simulation internals.

## Backward Compatibility (Transition)

- Continue reading legacy files during migration:
  - `airspace_config.json`
  - `aircraft_data.json`
  - `aircraft_ingest.json`
- New contracts become canonical.
- Add compatibility adapters to map legacy -> v1 canonical structures.

## Implementation Order (historical reference)

For active prioritization and delivery status, use `new_roadmap.md`.

1. Define schema files + strict validators for all v1 contracts.
2. Add IO adapters:
- File snapshot adapter
- File event adapter
- Optional stdin adapter
3. Introduce canonical model mapping (legacy -> v1).
4. Update simulation manager to consume canonical models/events.
5. Update runtime publisher to `aircraft_state.v1.json` with atomic writes.
6. Update UI to read canonical state + optional render profile.
7. Add conformance tests for each adapter and contract.

## Non-Goals (v1)

- Real-time network transport standardization (HTTP/WS/broker) in core package.
- Full flight dynamics/weather modeling.
- Operational ATM claims.
