# Failure Modes and Runtime Limits

This document describes expected failure behavior for malformed inputs and runtime issues.

## Input Validation Failures

Validators in `airspacesim/io/contracts.py` reject invalid payloads with `ValidationError`.

Common rejected cases:
- unknown `route_id` in aircraft scenario
- unknown waypoint references in route definitions
- invalid latitude/longitude ranges
- missing required envelope fields (`schema`, `metadata`, `data`)
- unsupported event type in inbox events

Behavior:
- invalid payload is not silently accepted
- caller receives explicit error text

## Route Resolution Failures

Route stitching via `RouteRegistry` may fail with `RouteResolutionError` when:
- route ID does not exist
- route chain has no intersection between consecutive routes
- route sequence cannot be traversed into a valid ordered waypoint path

Behavior:
- simulation setup should fail fast with clear error details
- no partial route path is emitted as if valid

## Aircraft Speed Guardrails

Aircraft speed is interpreted in knots (`kt`) and validated in `Aircraft`.

Behavior:
- speed `<= 0` raises `ValueError`
- speed above warning threshold logs warning
- absurd speed handling uses configured mode:
  - `reject`: raise `ValueError`
  - `clamp`: cap to configured maximum
  - `off`: accept value

## Runtime File/IO Issues

State output uses atomic file writes in `AircraftManager`:
- write temp file
- fsync
- atomic rename

Behavior:
- prevents partially-written JSON reads in UI polling
- write failures are logged and do not crash process by default

## Frontend Runtime Failures

Map/UI JS has graceful fallback behavior:
- config loading tries multiple candidate paths
- aircraft polling tries canonical then legacy files
- missing data updates status panel to warning state
- operator event sink tries configured URL then fallback candidates (including `127.0.0.1:8080`)

Behavior:
- UI stays up with degraded telemetry instead of hard crash

Common operator-control failures:
- `405 Method Not Allowed` on `/api/events`
  - Cause: page served from static-only dev server that does not accept POST.
  - Action: use `python3 dev_server.py` and open map from its URL.
- `SET_SPEED` skipped with "aircraft not found"
  - Cause: `payload.aircraft_id` was a callsign, not aircraft ID.
  - Action: use the runtime `id` value (for example `AC800`), not callsign (`OPS800`).
- `ADD_AIRCRAFT` skipped with duplicate ID
  - Cause: aircraft with same ID already active.
  - Action: send unique `aircraft_id` or remove existing aircraft first.
- speed rejected above guardrail
  - Cause: value exceeded configured absurd threshold (`MAX_ABSURD_SPEED_KTS`).
  - Action: use lower speed, or change guardrail mode/threshold intentionally.

## Restart Replay Behavior

File-based ingestion keeps event history in `data/inbox_events.v1.json`.
When process restarts, events still present can be applied again.

Behavior:
- safe for idempotent event types where repeated application is acceptable
- surprising for additive events (`ADD_AIRCRAFT`) unless IDs are unique or duplicates are blocked

Action:
- clear consumed events before a clean restart, or introduce checkpoint/compaction workflow.

## Known Operational Limits

- not an operational ATM/UTM safety system
- no certified separation assurance logic
- no weather, intent uncertainty, or surveillance fusion model
- intended for simulation/research, not live control
