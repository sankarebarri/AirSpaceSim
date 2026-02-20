# File Contracts (Draft)

## Canonical files

### `data/airspace_data.json`
Purpose: metadata-rich source catalog of airspaces. This is where you add new airspaces.

Minimum structure:
- `schema`: version envelope
- `airspaces`: list of airspace definitions
  - `airspace_id`: string
  - `waypoints`: list of waypoint objects
    - `dec_coords`: `[lat, lon]` (preferred when present), or
    - `coords`: DMS object with `lat` and `lon`

Rule:
- Each airspace must contain at least 1 waypoint (`min_waypoints_per_airspace = 1`).

### `data/airspace_config.json`
Purpose: UI load file. Can be generated from `airspace_data.json` selections and can also include manual elements.

Minimum structure:
- `center`: `[lat, lon]`
- `zoom`: integer
- `tile_layer`: object with `url` and `attribution`
- `elements`: list of map elements (`polyline`, `circle`, `marker`)
- Optional source fields:
  - `data_source.airspace_data_file`
  - `data_source.selected_airspaces`
  - `selection_policy.coordinates.fallback_order` (`dec_coords`, then DMS conversion)
- Optional polling config:
  - `render.map.aircraft_poll_interval_ms` (milliseconds, minimum 250; default 1000)

Contract versioning:
- Legacy shape (still accepted): unversioned root fields above.
- Versioned shape (preferred): `data/map_config.v1.json` with envelope:
  - `schema.name = airspacesim.map_config`
  - `schema.version = 1.0`
  - `metadata.source`, `metadata.generated_utc`
  - `data` containing the same map config object fields.

Path resolution:
- Frontend loaders resolve config files relative to `static/js` as `../../data/...` to align with `airspacesim init` project layout.

### `data/aircraft_data.json`
Purpose: dynamic aircraft state consumed by UI polling.

Minimum structure:
- `aircraft_data`: list of objects
  - `id`: string
  - `position`: `[lat, lon]`
  - `callsign`: string
  - `speed`: number

Contract versioning:
- Versioned envelope is now written to this file:
  - `schema.name = airspacesim.aircraft_data`
  - `schema.version = 1.0`
  - `metadata.source`, `metadata.generated_utc`
  - `data.aircraft_data[]`
- Compatibility shim remains at root (`aircraft_data`) for legacy readers.

Path resolution:
- Frontend loader resolves `aircraft_state.v1.json` and `aircraft_data.json` from `../../data/...` relative to `static/js`.

### `data/aircraft_ingest.json`
Purpose: ingest queue/input for new aircraft instructions.

Current accepted shape:
- `aircraft`: list of entries
  - direct entry with `route` (plus optional `id`, `callsign`, `speed`)
  - nested `{ "aircraft": [...] }` entries are also accepted for compatibility

### `data/ui_runtime.v1.json`
Purpose: UI data-source adapter contract that decouples frontend fetch endpoints from backend implementation details.

Minimum structure:
- `schema.name = airspacesim.ui_runtime`
- `schema.version = 1.0`
- `metadata.source`
- `metadata.generated_utc`
- `data.sources.map_config` (candidate endpoints/paths)
- `data.sources.aircraft_state` (candidate endpoints/paths)
- `data.ui.aircraft_poll_interval_ms` (optional, minimum 250)

### `data/scenario.v0.1.json`
Purpose: unified scenario input contract for simulation startup.

Minimum structure:
- `schema.name = airspacesim.scenario`
- `schema.version = 0.1`
- `metadata.source`
- `metadata.generated_utc`
- `data.airspace` (same shape as `scenario_airspace.v1.json` `data`)
- `data.aircraft` (same shape as `scenario_aircraft.v1.json` `data`)

### `data/trajectory.v0.1.json`
Purpose: canonical simulation trajectory/state output feed.

Minimum structure:
- `schema.name = airspacesim.trajectory`
- `schema.version = 0.1`
- `metadata.source`
- `metadata.generated_utc`
- `data.tracks[]`
  - `id`, `route_id`, `position_dd`, `status`, `updated_utc`
  - optional: `callsign`, `speed_kt`, `altitude_ft`, `vertical_rate_fpm`

## Legacy fallback reads (temporary)
- `gao_airspace.json`
- `gao_airspace_config.json`
- `new_aircraft.json`

Writers should use canonical files only.
