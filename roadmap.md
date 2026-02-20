# AirSpaceSim Master Roadmap & Execution Tracker

Use this as the single source of truth for both pre-roadmap hardening and phased roadmap delivery.

How to update:
- Mark done: change `- [ ]` to `- [x]`
- Re-open: change `- [x]` to `- [ ]`

## Objective

Build AirSpaceSim into a reliable, simulation-first, data-agnostic and framework-agnostic airspace engine with stable data contracts.

## Guiding priorities

- Keep simulation core independent and usable on its own
- Publish explicit, versioned JSON schemas
- Improve reproducibility and test coverage before feature expansion
- Decouple backend and UI so either side can evolve independently
- Distinguish research capabilities from production readiness

## 0. Immediate blockers (must finish first)

- [x] Fix deadlock risk in `AircraftManager` (`Lock` re-entry issue between cleanup and save path)
- [x] Fix `MapRenderer.to_json()` setting key mismatch (`AIRSPACE_DATA_FILE` vs `AIRSPACE_FILE`)
- [x] Make `airspacesim init` resilient when optional assets are missing
- [x] Fix icon-copy behavior in `init` so static icon assets are actually copied
- [x] Ensure `init` writes files into a coherent output structure (`templates/`, `static/`, `data/`)
- [x] Align config filename usage and make canonical names generic

Exit criteria:
- [x] `airspacesim init` runs from a clean environment without manual file creation
- [x] Generated map loads with icons and aircraft polling without missing-file errors

## 1. Packaging and install hygiene

- [x] Replace empty `pyproject.toml` with modern build metadata (`setuptools` backend)
- [x] Remove empty strings from `setup.py` `install_requires`
- [x] Fix package data globs (`static/js/*.js`, `static/css/*.css`)
- [x] Fix license naming mismatch (`LICENCE` vs `LICENSE`) in manifest/metadata
- [x] Add dev dependencies for testing/linting
- [x] Validate source distribution and wheel include required templates/static/data

Exit criteria:
- [x] `pip install -e .` works in offline-constrained environments
- [x] Built wheel/sdist contain runtime assets required by CLI and renderer

## 2. Test baseline (quality gate before new features)

- [x] Fix failing integration test expectation in `tests/test_integration.py`
- [x] Add unit tests for coordinate conversions (`dms_to_decimal`, `haversine`)
- [x] Add tests for route processing (`process_waypoints`, mixed DMS/decimal cases)
- [x] Add deterministic tests for aircraft stepping (`update_position`, segment transitions)
- [x] Add test for CLI `init` output files and idempotency
- [x] Add thread-safety regression test for aircraft cleanup/write flow

Exit criteria:
- [x] Test suite passes locally
- [x] Minimum baseline coverage target agreed and enforced

## 3. Structural cleanup (low risk, high clarity)

- [x] Remove or implement empty modules:
  - [x] `airspacesim/utils/config.py`
  - [x] `airspacesim/utils/calculations.py`
  - [x] `airspacesim/utils/logger.py`
  - [x] `airspacesim/routes/route_manager.py`
- [x] Resolve duplicate route manager naming (`routes/manager.py` vs `routes/route_manager.py`)
- [x] Eliminate commented-out legacy blocks in CLI
- [x] Replace print-based CLI feedback with consistent logger/formatter strategy
- [x] Stop import-time side effects in logging config (no file creation at import)

Exit criteria:
- [x] Module tree has no dead stubs or ambiguous duplicates
- [x] Imports are side-effect minimal

## 4. Redesign track (approved scope)

- [x] Approve target architecture and boundaries
- [x] Introduce clear package domains (`core/`, `io/`, `cli/`, `web/`, `config/`)
- [x] Introduce orchestrated batched scheduler mode (legacy thread-per-aircraft remains available)
- [x] Add explicit typed models (dataclasses or pydantic)
- [x] Introduce stable interfaces for scenario input, stepping, and trajectory output
- [x] Add versioned schema files under `schemas/`
- [x] Define migration notes for old file contracts
- [x] Remove domain-specific naming from core contracts
- [x] Enforce framework-agnostic core (no frontend map/UI dependencies in simulation engine)

Exit criteria:
- [x] New structure documented and adopted
- [x] Legacy paths either removed or compatibility-shimmed with deprecation notes
- [x] Core simulation can run headless without web/frontend assets

## 5. Frontend/runtime contract alignment

- [x] Version and document `aircraft_data.json` and map config contracts
- [x] Align JS fetch paths with CLI output layout
- [x] Add robust error states in frontend for missing config/data
- [x] Reduce polling frequency or make it configurable
- [x] Ensure map + aircraft scripts work from generated project root without path hacks
- [x] Decouple UI from backend so either side can evolve independently

Exit criteria:
- [x] Browser console remains clean in normal run
- [x] Frontend can recover from temporary missing/empty aircraft data files
- [x] UI replacement does not require backend engine changes
- [x] Backend replacement does not require UI rework beyond adapter configuration

## 5A. Data use and ingestion architecture

- [x] Define canonical data domains (`scenario`, `aircraft_state`, `aircraft_events`, `trajectory_output`)
- [x] Define versioned schema envelope for all contracts
- [x] Introduce ingestion adapter interface (`poll`, optional `ack`)
- [x] Enforce deterministic ordering + idempotency (`event_id` dedupe)
- [x] Build initial adapters (JSON snapshot, JSON events, stdin stream)
- [x] Keep optional network/broker adapters outside core package

Exit criteria:
- [x] Core simulation consumes normalized events only (not raw source formats)
- [x] At least two adapters pass a shared ingestion conformance test suite

## 6. Documentation and contributor workflow

- [x] Update README quickstart so it matches generated files/paths
- [x] Add `CONTRIBUTING.md` with dev setup, test commands, and conventions
- [x] Add `docs/architecture.md` with module boundaries and data flow
- [x] Add `docs/file-contracts.md` for runtime JSON contracts
- [x] Add changelog policy and release checklist
- [x] Add ingestion docs (`docs/ingestion.md`, `docs/data-contracts.md`, `docs/migration.md`)
- [x] Add ADRs (`0001`, `0002`, `0003`)

Exit criteria:
- [x] New contributor can set up, run tests, and run demo from docs only
- [x] Architecture/data/ingestion decisions are traceable in ADRs

## Phase roadmap

### Phase 1: Foundation Hardening (v0.2)

- [x] Finalize packaging/install reliability in constrained environments
- [x] Close remaining baseline test gaps (thread-safety regression, coverage target)
- [x] Verify clean install + `airspacesim init` + sample run without manual file creation

Exit criteria:
- [x] CI workflow configured for supported Python versions
- [x] CI passes core tests on supported Python versions (remote run evidence recorded)

### Phase 2: Data Contracts (v0.3)

- [x] Introduce `airspacesim.trajectory.v0.1` output schema
- [x] Introduce `airspacesim.scenario.v0.1` input schema
- [x] Add schema validation hooks for simulation I/O
- [x] Publish migration notes for future schema versions

### Phase 3: Simulation Quality and Scale (v0.4)

- [x] Add deterministic run mode where applicable
- [x] Add stress scenarios with increased aircraft count
- [x] Add performance benchmarks for update loop and JSON write path
- [x] Improve thread lifecycle controls and shutdown behavior

### Phase 4: Interoperability and Tooling (v0.5)

- [x] Provide adapters/exporters for downstream conflict and audit workflows
- [x] Add one realistic end-to-end interoperability example
- [x] Publish glossary and phrase conventions
- [x] Add compatibility matrix for schema consumers

## Suggested execution order

- [x] Batch A: blockers + config/path alignment
- [x] Batch B: packaging + test baseline
- [x] Batch C: structural cleanup + naming finalization
- [x] Batch D: data ingestion architecture + UI/backend decoupling
- [x] Batch E: docs/ADRs finalization and roadmap kickoff

## Safety and limitations track

Ongoing across all phases:
- [x] keep explicit non-operational safety disclaimer
- [x] avoid operational readiness claims without validation evidence
- [x] maintain failure-mode documentation for malformed input and runtime issues
