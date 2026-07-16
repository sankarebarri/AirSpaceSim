# Changelog

All notable changes to this project must be documented in this file.

The format follows Keep a Changelog principles and semantic versioning intent.

## [Unreleased]

## [0.2.0] - 2026-07-16

### Added
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
