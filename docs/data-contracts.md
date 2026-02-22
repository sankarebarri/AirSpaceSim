# Data Contracts (Draft)

## Contract domains
- `scenario`: static context (routes, constraints, map metadata)
- `airspace_data`: metadata source catalog for one or more airspaces (authoring file)
- `aircraft_state`: latest known state snapshot
- `aircraft_events`: append-only event stream
- `trajectory_output`: time-stepped simulation output

Runtime canonical domain mapping in code (`airspacesim/io/contracts.py`):
- `scenario`: `airspacesim.scenario_airspace`, `airspacesim.scenario_aircraft`
- `aircraft_state`: `airspacesim.aircraft_state`, `airspacesim.aircraft_data`
- `aircraft_events`: `airspacesim.inbox_events`
- `trajectory_output`: reserved (`airspacesim.trajectory`)

## Envelope
Each file/message should include:
- `schema.name`
- `schema.version`
- `metadata.generated_utc`
- `data`

## Event stream notes (`airspacesim.inbox_events`)

- Required event keys: `event_id`, `type`, `created_utc`, `payload`.
- Runtime ordering key: `(sequence, created_utc, event_id)`.
- Idempotency key: `event_id` (process-local dedupe for file/stdin adapters).
- Restart behavior: events still present in inbox file can replay after process restart unless compacted/cleared.

## Naming policy
Canonical generic names:
- `data/airspace_data.json`
- `data/airspace_config.json`
- `data/map_config.v1.json`
- `data/scenario.v0.1.json`
- `data/aircraft_data.json`
- `data/trajectory.v0.1.json`
- `data/ui_runtime.v1.json`
- `data/aircraft_ingest.json`

Temporary legacy compatibility (read-only fallback):
- `gao_airspace.json`
- `gao_airspace_config.json`
- `new_aircraft.json`

## Compatibility policy
- Patch/minor versions: backward-compatible additions.
- Major versions: breaking changes with migration notes.

## Schema files
- Versioned JSON schemas are published under `airspacesim/schemas/`.
- Current files:
  - `airspacesim/schemas/airspacesim.scenario.v0.1.schema.json`
  - `airspacesim/schemas/airspacesim.trajectory.v0.1.schema.json`
