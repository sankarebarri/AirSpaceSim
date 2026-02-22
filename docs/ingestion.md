# Ingestion Model (Draft)

## Principle
Simulation consumes normalized events, not source-specific payloads.

## Canonical event types
- `ADD_AIRCRAFT`
- `SET_SPEED`
- `REMOVE_AIRCRAFT`
- `REROUTE`
- `SET_VERTICAL_RATE`
- `SET_SIMULATION_SPEED`

## Required event fields
- `event_id`
- `created_utc`
- `type`
- `payload`

## Adapter interface
- `EventIngestionAdapter.poll() -> list[dict]`
- Optional `EventIngestionAdapter.ack(event_ids=None)` for checkpoint-style sources

## Determinism and idempotency
- Deduplicate by `event_id`.
- Apply strict ordering by `(sequence, created_utc, event_id)`.
- Deduplication state is process-local for file/stdin adapters; restarting simulation re-reads events still present in inbox files.

## Initial adapters
- JSON snapshot file
- JSON append/event file
- stdin stream

Implemented adapters:
- `FileSnapshotAdapter` (snapshot I/O)
- `FileEventAdapter` (canonical event files, deterministic order + dedupe)
- `StdinEventAdapter` (newline-delimited JSON events/envelopes)

Conformance:
- Shared ingestion conformance tests validate deterministic order + idempotency across both `FileEventAdapter` and `StdinEventAdapter`.

Scope boundary:
- Network/broker adapters stay outside core package unless explicitly added as optional integrations.

## Operational command semantics

- `SET_SPEED.payload.aircraft_id` must use aircraft ID (for example `AC800`), not callsign.
- `ADD_AIRCRAFT` events are rejected as duplicates when `aircraft_id` already exists at runtime.
- Speed guardrails are enforced on add/update:
  - warning above realistic threshold
  - rejection/clamp above absurd threshold according to settings.
