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

### Added
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
