# Ingestion Model (Draft)

## Principle
Simulation consumes normalized events, not source-specific payloads.

## Canonical event types
- `ADD_AIRCRAFT`
- `SET_SPEED`
- `REMOVE_AIRCRAFT`
- `REROUTE`
- `SET_VERTICAL_RATE`

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
