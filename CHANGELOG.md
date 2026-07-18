# Changelog

All notable changes to this project must be documented in this file.

The format follows Keep a Changelog principles and semantic versioning intent.

## [Unreleased]

## [0.2.0] - 2026-07-16

### Removed (breaking — approved cleanup, see docs/migration.md)
- `airspacesim.hello` module and the `say_hello` top-level export.
- `airspacesim.routes.route_manager` compatibility shim (use `airspacesim.routes.manager.RouteManager`).
- Empty placeholder subpackages `airspacesim.api`, `airspacesim.web`, `airspacesim.tests`, and the `airspacesim.config` re-export shim.
- Process-wide `settings.SIMULATION_SPEED`; time acceleration is now per-manager (`AircraftManager(sim_rate=...)` / `set_simulation_speed`).
- Legacy filename fallbacks `gao_airspace.json`, `gao_airspace_config.json`, and `new_aircraft.json`, plus the packaged `data/gao_airspace.json` and `data/new_aircraft.json` seed files.

### Changed (breaking)
- `Aircraft.update_position(time_step)` now advances by `time_step` **simulated seconds** and reads no global runtime state; callers own time acceleration.
- `SET_SIMULATION_SPEED` events scale only the receiving manager, not the whole process.

### Changed (breaking — fictional environment migration, decision Q3)
- All public Gao-derived aeronautical data replaced by the fully fictional **Nerava FIR** at neutral mid-Atlantic coordinates (Nerava VOR `NRV`, 33.5N 41.0W): new fixes (NARVO, LUMEK, SAVEN, …), new ATS-style routes (UL602, UM731, T45, B12, A1, …), new 60 NM training sector. `airspaces/gao_demo` deleted (last available under git tag `pre-gao-removal`); replaced by `airspaces/nerava_fir` with ported `sector_traffic` and `mixed_traffic` scenarios.
- `airspacesim/data/*.json` package seeds regenerated for the Nerava environment; `settings.AIRSPACE_CENTER` now points at the fictional centre and is overridable per manager (`AircraftManager(airspace_center=...)`); `Simulation`/`initialize_manager_from_scenarios` derive the traffic-flow centre from the loaded airspace (first navaid, then centroid).
- `training_alpha` re-centred to neutral coordinates via an exact longitude rotation (16.25N 40.0W) — an isometry, so every distance, bearing, crossing point, and scenario timing is preserved.
- Real-airline-style callsigns replaced with fictional ones across scenarios, lessons, and the web app (AFR612→NVR231, RAM401→SKL842, DAL217→VLR217, UAE203→KTR203, KLM891→NVR891, SIA328→TIR328, ETH504→RIK504, JBU550→SKL550).
- Web Simulate registry now points at `nerava_fir`/`sector_traffic` (slug `nerava-sector-traffic`); run-workspace defaults and placeholders use `UL602`/`NRV_VOR`.

### Added (Traffic Relationships curriculum, generic runners, EN/FR i18n)
- Separation Fundamentals curriculum (`content/curriculum.v1.json`) with the five-lesson Traffic Relationships journey (Understanding Track, Same-Track, Reciprocal-Track, Crossing-Track, Identify the Relationship) available, and Vertical/Horizontal Separation shown as quiet planned placeholders with outline metadata.
- Six deterministic Traffic Relationships scenarios in `training_alpha` (2 aircraft, ≤3 visible routes, scenario-configurable label placement, `traffic_relationship` classification metadata in scenario data per the content spec).
- Content API: `GET /api/v1/content/curriculum` and `GET /api/v1/content/lessons/{airspace_id}/{lesson_id}` — lesson steps are data (translation keys + scenario references), so adding a lesson requires JSON + locale entries only.
- Generic lesson runner (`LessonRunnerPage`) with observation, classification (correct answer read from scenario metadata), and completion steps driving real engine runs; curriculum-driven Learn page and generic `ConceptPage` with guest-local progress; no prediction metrics anywhere in foundational lessons (asserted by test).
- English/French internationalisation with central keys (`src/locales/en.json`, `fr.json`), a dependency-free provider, and an EN|FR switcher; homepage, navigation, Learn catalogue, concept pages, and all lesson content translated. French drafts pending owner terminology review (decision Q9). Operational simulation surfaces (run workspace, commands) remain English by design.
- i18n coverage tests: every key referenced by curriculum/lesson content must exist in both catalogues, and the catalogues must stay key-identical.

### Changed (server-authoritative debriefs)
- The run workspace debrief now consumes the server-computed run summary and engine separation monitoring: `practiceOutcome.ts` and `simulateSummary.ts` no longer perform client-side separation math (the Phase 2 parity cutover). Practice/Simulate outcomes shown in the UI are exactly what is persisted with the run.

### Added (content versioning and shared validation)
- Semantic `version` fields on airspace package manifests, environment definitions (`metadata.version`), and every scenario template; enforced by `scripts/validate_airspace_package.py`.
- Shared validation module `airspacesim.io.templates`: airspace geometry, aircraft plans (unique ids/callsigns, route existence, performance-based speed/level ranges, entry times), template metadata (semver, supported `active_commands` against `KNOWN_COMMAND_TYPES`), with plain-English error messages. The seeding script and package validator now delegate to it.
- Hosted API validates scenario templates when creating practice runs and returns readable HTTP 400s (e.g. "AC1 references unknown route 'NO_SUCH_ROUTE'."); `content_versions` (airspace id, environment version, template id + version) are stamped into scenario metadata and carried into persisted run summaries for reproducibility. Airspace listings expose the package `version`.

### Added
- Core `Simulation` façade (`airspacesim.Simulation`) owning the deterministic `SimulationClock`, scheduled aircraft entry, command application, serialisable snapshots, factual summaries, and an emitted `EngineEvent` stream (`aircraft_entered/exited`, `separation_loss_started/ended`, `command_applied`, `simulation_completed`).
- General `SeparationMonitor` + `SeparationStandard` in the engine: a pair is separated when either the horizontal or the vertical minimum is satisfied; one continuous loss of separation counts as one event until separation is restored (ported from the frontend monitor so behaviour is preserved).
- Scenario aircraft `appear_after_seconds` / `entry_time_seconds` are now engine-scheduled: hosted practice runs honour staggered entries instead of spawning all aircraft at t=0 (validated by the contract validator; e.g. `beginner_mix` now starts with 4 live + 4 pending aircraft).
- Hosted API: run state and WebSocket snapshots now include `time_seconds`, `separation` (standard, active violations, LoS count), and a live `summary`; factual run summaries (Simulate counters, server-derived Practice outcomes) are persisted to `runs.summary_json` at stop/completion (Alembic `20260716_0004`).
- Server-side Practice outcome tracking (`apps/api/app/sessions/practice.py`), scenario-metadata-driven and kept outside the general engine monitor.
- `AircraftManager.step_aircraft(simulated_seconds)` public pure stepping API.
- `AircraftManager(enable_file_output=False)` and `initialize_manager_from_scenarios(..., enable_file_output=...)` to run the engine without JSON file side effects; the hosted API runtime no longer monkeypatches `save_aircraft_data`.
- Engine stepping guarantees test suite (`tests/test_engine_stepping.py`): deterministic identical-step-sequence states, per-manager sim rate scoping, and no-file-output verification.
- Hosted FastAPI service and React web app for local training workflows.
- Fictional airspace packages, scenarios, and lesson content for guided practice.
- Local dev scripts for starting the hosted app and seeding demo runs.
- Public launch, deployment, frontend, backend, and architecture documentation.
- Guided Learn/Practice/Simulate product flow with live simulator integration.

### Changed
- Development defaults now allow high local run concurrency for easier testing.
- Dashboard map moved toward a no-basemap sector display for simulation-focused use.
- Packaging and repository hygiene updated for GitHub publishing.

### Added
- Initial contribution workflow documentation in `CONTRIBUTING.md`.
- Route registry with deterministic route stitching and intersection handling.
- Speed guardrails and speed/unit correctness tests.

### Changed
- Simulation speed handling clarified and validated (kt, NM, seconds).
- Playground example aircraft speeds updated to realistic cruise values.
