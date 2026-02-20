# ADR 0001: Split Contracts by Data Domain

## Status
Accepted (draft)

## Decision
Separate scenario, ingest events, state snapshots, and trajectory output into distinct contracts.

## Rationale
Reduces coupling and allows independent evolution of producers/consumers.
