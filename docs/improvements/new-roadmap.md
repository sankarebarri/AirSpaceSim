# AirSpaceSim Execution Checklist

Last updated: 2026-05-26

## Goal

Build AirSpaceSim as two compatible products:

- a clean `airspacesim` Python package for PyPI
- a hosted application built with `FastAPI + React + SQLite`

The core rule is that the hosted app must be built around the library, not baked into it.

## Working Rules

- [x] Keep `airspacesim/` framework-agnostic.
- [x] Keep FastAPI code out of `airspacesim/core`, `airspacesim/simulation`, `airspacesim/io`, and other core package modules.
- [x] Keep React code out of the Python package.
- [x] Use SQLite for durable application data, not as the per-tick hot simulation path.
- [x] Keep active simulation state in memory and persist at controlled boundaries.
- [x] Preserve JSON contract compatibility during migration for offline users, tests, exports, and examples.
- [ ] Keep PyPI install and local library workflows working while the hosted app is being built.

## Status Model

- `[NOT DONE]` planned, not started
- `[PARTIAL]` started but incomplete
- `[DONE]` completed and validated

## Active Planning Policy

- [x] Make `docs/improvements/new-roadmap.md` the active execution tracker for the migration.
- [ ] Treat `docs/improvements/legacy_static_ui_roadmap.md` as legacy/static-UI planning until it is archived or merged.
- [x] Update `README.md`, `documentation.md`, and docs index pages to point to the active tracker.
- [ ] Keep architecture wording consistent across docs while the static UI and hosted app coexist.

## Target Repository Structure

```text
AirSpaceSim/
  airspacesim/                  # core Python package, publish to PyPI
    __init__.py
    cli/
    core/
    io/
    routes/
    simulation/
    utils/
    schemas/
    examples/
    data/

  apps/
    api/                        # FastAPI app
      app/
        __init__.py
        main.py
        config.py
        dependencies.py
        api/
          __init__.py
          v1/
            __init__.py
            routes/
        db/
          __init__.py
          base.py
          models/
          repositories/
          migrations/
        services/
        sessions/
        ws/
        schemas/
      tests/
      pyproject.toml

    web/                        # React + TypeScript + Vite app
      src/
        app/
        pages/
        features/
        components/
        hooks/
        lib/
        styles/
        types/
      public/
      tests/
      package.json
      vite.config.ts
      tsconfig.json

  docs/
    adr/
    api/
    backend/
    frontend/
    migration/
    deployment/

  tests/                        # core library tests
  scripts/
  docs/improvements/new-roadmap.md

  airspacesim-playground/       # legacy reference during migration only
  dev_server.py                 # temporary compatibility path only
```

## File Placement Rules

- [x] New simulation/domain logic goes in `airspacesim/`.
- [x] New HTTP/API code goes in `apps/api/`.
- [x] New database models, repositories, and migrations go in `apps/api/app/db/`.
- [x] New browser UI code goes in `apps/web/`.
- [x] New frontend state, map rendering, and operator UX go in `apps/web/src/`.
- [x] `airspacesim/templates/`, `airspacesim/static/`, and `airspacesim-playground/` are legacy migration surfaces, not the long-term hosted UI home.
- [x] `dev_server.py` is temporary until FastAPI reaches feature parity for hosted usage.
- [x] `airspacesim init` remains a library/offline workflow and should not become the hosted app bootstrap path.

## Structure Alignment Checklist

- [x] Create `apps/`.
- [x] Create `apps/api/`.
- [x] Create `apps/web/`.
- [x] Create `docs/api/`, `docs/backend/`, `docs/frontend/`, `docs/migration/`, and `docs/deployment/`.
- [x] Mark `airspacesim-playground/` as legacy reference-only in docs.
- [x] Decide which current files remain package assets for `airspacesim init`.
- [x] Decide which current files become hosted-app assets and should not remain in the package long term.
- [ ] Keep the package directory small and intentional as the hosted app grows.

## Current-to-Target Ownership Map

- [x] `airspacesim/core/` stays in the package and remains framework-agnostic.
- [x] `airspacesim/simulation/` stays in the package and remains the simulation engine.
- [x] `airspacesim/io/` stays in the package and owns contracts, adapters, and exports.
- [x] `airspacesim/cli/` stays in the package and supports PyPI/library workflows.
- [x] `airspacesim/templates/` remains only as long as static package bootstrap is still supported.
- [x] `airspacesim/static/` remains only as long as static package bootstrap is still supported.
- [x] `airspacesim-playground/` is treated as a temporary migration reference.
- [x] `dev_server.py` is either replaced by FastAPI-hosted routes or moved into a clearly temporary compatibility path.

## Safe Cleanup Candidates

- [x] Remove unused `airspacesim/templates/basic_dashboard.html`.
- [x] Remove unused `airspacesim/templates/hello_world.html`.
- [x] Remove unused `airspacesim/templates/test.html`.
- [x] Remove unused empty `airspacesim/templates/styles.css`.
- [x] Verify when `airspacesim-playground/` can be downgraded from active surface to legacy reference only.
- [x] Verify when `dev_server.py` can be retired in favor of FastAPI-hosted behavior.

## Phase 0: Source of Truth, Automation, and Legacy Inventory

Status: `[PARTIAL]`

### Deliverables

- [x] active roadmap/source-of-truth policy established
- [x] new app scaffolds covered by automation
- [ ] legacy UI/runtime surfaces inventoried and deprecation-ready

### Tasks

- [PARTIAL] Consolidate planning ownership.
  - [x] Make `docs/improvements/new-roadmap.md` the active execution tracker.
  - [ ] Decide the final role of `docs/improvements/legacy_static_ui_roadmap.md` (`archive`, `redirect`, or `merge`).
  - [x] Point `README.md` at the active roadmap.
  - [x] Point `documentation.md` at the active roadmap.
- [PARTIAL] Consolidate architecture messaging.
  - [x] Replace “files/contracts only” wording with migration-aware language.
  - [ ] Mark static JSON polling as the current compatibility path, not the final hosted architecture.
  - [x] Document `apps/api` and `apps/web` as the hosted target stack.
- [PARTIAL] Put new scaffolds under automation immediately.
  - [x] Add `apps/api` test invocation to CI.
  - [x] Add `apps/api` startup/import smoke coverage.
  - [x] Add `apps/web` install/build smoke coverage.
  - [ ] Decide whether root CI owns sub-app checks or a separate workflow does.
- [x] Complete legacy surface inventory.
  - [x] Verify the safe cleanup candidates listed above.
  - [x] Mark `airspacesim-playground/` as legacy reference-only in docs.
  - [x] Document which static/package assets remain required for `airspacesim init`.
  - [x] Document which static/package assets are hosted-app migration leftovers.
- [x] Create deprecation notes.
  - [x] Define retirement criteria for `dev_server.py`.
  - [x] Define retirement criteria for `airspacesim-playground/`.
  - [x] Define retirement criteria for package-level static templates beyond the minimum bootstrap set.

## Phase 1: Package and Architecture Hardening

Status: `[NOT DONE]`

### Deliverables

- [ ] documented architecture boundary between library and hosted app
- [ ] package/runtime path issues fixed
- [ ] wheel smoke tests added
- [ ] public Python API surface defined
- [ ] critical runtime safety paper cuts fixed

### Tasks

- [ ] Write an ADR that formalizes the target architecture.
  - [ ] Define the role of `airspacesim/`.
  - [ ] Define the role of `apps/api/`.
  - [ ] Define the role of `apps/web/`.
  - [ ] Define migration rules for legacy static UI and JSON-file runtime.
- [ ] Fix current runtime path resolution in the package.
  - [ ] Stop falling back to writes inside installed `site-packages`.
  - [ ] Make workspace/runtime output paths explicit and testable.
  - [ ] Separate package seed files from runtime writable files.
- [ ] Fix package scaffolding gaps.
  - [ ] Resolve `dev_server.py` packaging mismatch.
  - [ ] Decide whether to replace it with `airspacesim serve` or keep it as temporary compatibility.
- [ ] Define the public Python package API.
  - [ ] Review `airspacesim/__init__.py`.
  - [ ] Export stable entry points intentionally.
  - [ ] Avoid exposing web-app concerns through the package root.
- [ ] Strengthen release validation.
  - [ ] Add build step.
  - [ ] Add wheel install smoke test.
  - [ ] Add `airspacesim init` smoke test from installed artifact.
  - [ ] Add example-run smoke test from clean install.
- [ ] Fix core runtime hardening items found during audit.
  - [ ] Guard `AircraftManager.add_aircraft()` list mutation with the manager lock.
  - [ ] Add a regression test for concurrent add/save behavior.
- [ ] Split docs by audience.
  - [ ] library user docs
  - [ ] hosted app developer docs
  - [ ] migration docs

## Phase 2: FastAPI Application Skeleton

Status: `[PARTIAL]`

### Deliverables

- [x] `apps/api/` scaffolded
- [x] FastAPI app factory created
- [x] versioned route structure in place
- [x] backend test skeleton in place

### Tasks

- [x] Create `apps/api/`.
  - [x] Add `pyproject.toml`.
  - [x] Add `app/`.
  - [x] Add `tests/`.
- [x] Add FastAPI app factory.
  - [x] `app/main.py`
  - [x] `app/config.py`
  - [x] `app/dependencies.py`
- [x] Add API routing structure.
  - [x] `app/api/v1/`
  - [x] `health` route
  - [x] placeholder `scenarios`, `runs`, and `commands` routers
- [PARTIAL] Add backend schemas.
  - [x] request models
  - [x] response models
  - [x] error response model
- [PARTIAL] Add backend test scaffolding.
  - [x] app startup test
  - [x] health route test
  - [ ] config loading test

## Phase 3: SQLite Persistence Layer

Status: `[PARTIAL]`

### Deliverables

- [x] SQLite engine/session layer
- [x] initial schema
- [x] migrations
- [x] repository/service boundary

### Tasks

- [x] Select and wire persistence stack.
  - [x] SQLAlchemy 2
  - [x] Alembic
  - [x] SQLite session management
- [x] Create DB structure.
  - [x] `app/db/base.py`
  - [x] `app/db/models/`
  - [x] `app/db/repositories/`
  - [x] `app/db/migrations/`
- [PARTIAL] Create initial tables.
  - [x] `scenarios`
  - [x] `simulation_runs`
  - [x] `run_commands`
  - [x] `run_checkpoints`
  - [ ] add normalized scenario tables only if UI scenario authoring requires queryable sub-objects
  - [ ] add stored command-result/export tables only if debrief or audit workflows require them
- [PARTIAL] Add migration workflow.
  - [x] initial migration
  - [x] migration test
  - [x] local dev instructions
- [ ] Define data import/export strategy.
  - [ ] import JSON scenarios into SQLite
  - [ ] export SQLite-backed scenarios to JSON contracts
  - [ ] document compatibility behavior
- [ ] Define persistence policy.
  - [x] run metadata persistence
  - [x] command history persistence
  - [x] checkpoint cadence
  - [x] retention/pruning
  - [ ] backup/restore

## Phase 4: Simulation Session Manager

Status: `[PARTIAL]`

### Deliverables

- [x] active run abstraction
- [x] in-memory session registry
- [x] command application flow
- [x] checkpoint persistence hooks

### Tasks

- [PARTIAL] Add `SimulationSession`.
  - [x] run lifecycle state
  - [x] active manager reference
  - [x] timing/step loop ownership
  - [x] session metadata
- [PARTIAL] Add `SessionRegistry`.
  - [x] create session
  - [x] lookup session
  - [x] list sessions
  - [x] close session
- [PARTIAL] Make hosted runtime default to batched execution.
  - [x] preserve legacy mode for library compatibility
  - [ ] document hosted/runtime default behavior
- [x] Add lifecycle controls.
  - [x] start
  - [x] pause
  - [x] resume
  - [x] stop
- [PARTIAL] Add command pipeline.
  - [x] receive command
  - [PARTIAL] validate command
  - [x] apply command
  - [x] persist result
  - [x] broadcast result
- [PARTIAL] Define recovery behavior.
  - [x] checkpoint-backed reads when runtime is missing
  - [x] reject live mutations when only checkpoint state exists
  - [ ] rehydrate a live runtime session from checkpoint state
- [x] Add persistence hooks.
  - [x] run created
  - [x] run started
  - [x] run paused
  - [x] run resumed
  - [x] run stopped
  - [x] checkpoint written
- [PARTIAL] Add session tests.
  - [x] lifecycle tests
  - [x] command tests
  - [x] checkpoint tests

## Phase 5: FastAPI Read Models and Live Transport

Status: `[PARTIAL]`

### Deliverables

- [x] scenario endpoints
- [x] run endpoints
- [x] live state endpoint
- [x] WebSocket stream

### Tasks

- [x] Add scenario endpoints.
  - [x] list scenarios
  - [x] get scenario
  - [x] create scenario
  - [x] update scenario
- [x] Add run endpoints.
  - [x] create run
  - [x] list runs
  - [x] get run
  - [x] start run
  - [x] pause run
  - [x] resume run
  - [x] stop run
- [PARTIAL] Add command endpoint.
  - [x] submit command
  - [x] return authoritative result envelope
- [PARTIAL] Add read endpoints.
  - [x] current run state
  - [x] trajectory snapshot
  - [x] checkpoint-backed fallback state
  - [x] checkpoint-backed fallback trajectory
  - [x] export endpoint
- [x] Add live transport.
  - [x] WebSocket connection manager
  - [x] session broadcast channel
  - [x] run-state payload shape
  - [x] command-result payload shape
- [ ] Add transport tests.
  - [ ] REST route tests
  - [x] WebSocket connect test
  - [x] WebSocket update test

## Phase 6: React Frontend Foundation

Status: `[PARTIAL]`

### Deliverables

- [x] `apps/web/` scaffolded
- [x] routing and API client set up
- [PARTIAL] design system baseline defined
- [x] map shell in place

### Tasks

- [x] Create `apps/web/`.
  - [x] Vite
  - [x] TypeScript
  - [ ] lint setup
  - [x] test setup
- [x] Create frontend structure.
  - [x] `src/app/`
  - [x] `src/pages/`
  - [x] `src/features/`
  - [x] `src/components/`
  - [x] `src/hooks/`
  - [x] `src/lib/`
  - [x] `src/styles/`
  - [x] `src/types/`
- [PARTIAL] Add app foundations.
  - [x] router
  - [x] React Query
  - [x] API client
  - [x] runtime env config
  - [x] shared error handling
- [PARTIAL] Define design system baseline.
  - [x] color tokens
  - [ ] spacing scale
  - [x] typography system
  - [x] panel patterns
  - [x] map layout pattern
- [x] Add map foundation.
  - [x] Leaflet integration through React
  - [x] map page shell
  - [x] map overlay layers
- [x] Add frontend tests.
  - [x] app render test
  - [x] route render tests
  - [x] API client tests

## Phase 7: Hosted MVP Feature Parity

Status: `[PARTIAL]`

### Deliverables

- [PARTIAL] hosted UI can replace the current static experience for core usage
- [x] live aircraft updates shown in the browser
- [x] operator command flow works through API

### Tasks

- [PARTIAL] Recreate scenario/run flow in React.
  - [x] scenario list page
  - [x] create run flow
  - [x] run detail page
- [x] Build live run workspace.
  - [x] map rendering
  - [x] airspace layers
  - [x] aircraft markers
  - [x] aircraft table
  - [x] selected-aircraft state
- [x] Build operator interaction flow.
  - [x] add aircraft
  - [x] set speed
  - [x] set FL
  - [x] assign heading
  - [x] assign radial
  - [x] direct to fix
  - [x] hold at fix
  - [x] resume navigation
  - [x] set simulation rate
  - [x] show applied/skipped/rejected results
- [PARTIAL] Improve usability beyond the current static page.
  - [x] route filter
  - [x] status filter
  - [x] traffic-flow filter
  - [x] freshness indicator
  - [x] better selected-aircraft drawer
- [x] aircraft labels, heading vectors, reset view, and easier map selection
- [x] Replace raw JSON payload editing with guided UI controls.
- [ ] Add end-to-end test for the main run flow.

## Phase 8: Migration Off File-Based Browser Runtime

Status: `[NOT DONE]`

### Deliverables

- [x] browser no longer depends on `data/*.json` as primary transport
- [ ] compatibility path remains for library/offline flows
- [ ] legacy static surfaces clearly deprecated

### Tasks

- [x] Stop using browser-side direct file polling for hosted usage.
  - [x] state comes from REST/WebSocket
  - [x] commands go through API
- [ ] Keep compatibility adapters.
  - [ ] JSON scenario import
  - [ ] JSON export
  - [ ] offline example support
- [ ] Decide package asset future.
  - [ ] keep minimal static bootstrap for `airspacesim init`
  - [ ] or reduce static assets once hosted app is primary
- [ ] Mark legacy paths clearly.
  - [ ] `airspacesim-playground/`
  - [ ] `airspacesim/templates/`
  - [ ] `airspacesim/static/`
  - [ ] `dev_server.py`
- [ ] Write migration docs.
  - [ ] old flow
  - [ ] new flow
  - [ ] compatibility guarantees

## Phase 9: Testing, Performance, and Release Gates

Status: `[NOT DONE]`

### Deliverables

- [ ] full layered test strategy
- [ ] performance thresholds
- [ ] release gates for package and hosted app

### Tasks

- [ ] Add backend unit tests.
  - [x] services
  - [x] repositories
  - [x] command flow
  - [x] session manager
- [ ] Add migration tests.
  - [x] schema creation
  - [x] upgrade path
  - [x] downgrade path if needed
- [ ] Add transport tests.
  - [ ] REST
  - [ ] WebSocket
- [ ] Add frontend tests.
  - [x] component tests
  - [x] interaction tests
  - [x] page tests
- [ ] Add Playwright tests.
  - [x] run creation
  - [x] live updates
  - [x] command submission
  - [x] selected-aircraft workflow
- [ ] Add performance tests.
  - [ ] 100 aircraft
  - [ ] map/render degradation thresholds
- [ ] Add release gates.
  - [ ] build core package
  - [ ] install built wheel
  - [ ] run package smoke tests
  - [x] run hosted backend tests
  - [x] run hosted frontend tests

## Phase 10: Deployment and First Hosted Release

Status: `[NOT DONE]`

### Deliverables

- [ ] deployable FastAPI + React stack
- [ ] operational SQLite strategy
- [ ] first hosted release checklist complete

### Tasks

- [ ] Package the backend for deployment.
  - [ ] container build
  - [ ] env config
  - [ ] startup command
- [ ] Define frontend serving strategy.
  - [ ] reverse proxy
  - [ ] static build hosting
  - [ ] backend static mount for first release if needed
- [ ] Define SQLite operational strategy.
  - [ ] DB file location
  - [ ] backup policy
  - [ ] restore policy
  - [ ] rotation/retention policy
- [ ] Add observability basics.
  - [ ] structured logs
  - [ ] request logging
  - [ ] session/run metrics
  - [ ] error reporting hooks
- [ ] Create deployment docs.
  - [ ] local dev
  - [ ] staging
  - [ ] production
- [ ] Verify first hosted release criteria.
  - [ ] scenario CRUD
  - [ ] run lifecycle
  - [ ] live map
  - [ ] command results
  - [ ] exports
  - [ ] playback alpha
  - [ ] docs complete
  - [ ] PyPI package still independently usable

## Immediate Next Build Order

- [x] Add migration execution coverage for `apps/api` so Alembic revisions are validated, not only `create_all`.
- [PARTIAL] Add session recovery rules and decide whether stopped/completed runs are read-only or resumable from checkpoints.
- [x] Implement checkpoint retention/pruning so long-running sessions do not grow SQLite without bounds.
- [ ] Add end-to-end websocket transport tests once the FastAPI client stack is stable in this environment.
- [x] Recreate current map + aircraft live view in React.
- [x] Replace file-based operator controls with API command flow.

## Product Backlog After MVP

- [ ] scenario presets and guided demo mode
- [ ] timeline playback with scrub, pause, and replay
- [ ] conflict/proximity alerts
- [ ] batch aircraft import
- [ ] richer route authoring and flight-plan composition
- [ ] collaborative multi-user sessions
- [ ] role-based access control
- [ ] rendering fallback strategy for very large aircraft counts

## Deferred To Avoid Bloat

These are not rejected permanently, but they should not drive near-term architecture:

- normalized scenario sub-object tables before scenario authoring needs them
- separate stored command-result/export tables before debrief or audit needs them
- 500/1000 aircraft performance targets before a 100-aircraft target is useful
- weather and wind overlays before core ATC training workflows are stable
- run comparison and analytics before exercise/debrief data exists

## Notes

- The current static UI remains useful as a migration reference, not as the long-term hosted architecture.
- The current JSON contract flow remains useful for package examples, exports, and compatibility.
- SQLite is the right first persistence layer here only if writes are deliberate and batched where appropriate.
- File structure should evolve with this checklist, not independently from it.
