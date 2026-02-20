# ADR 0004: Core Domain Interfaces and Typed Models

## Status
Accepted

## Decision
Introduce a `core` domain package with:
- typed dataclass models (`Waypoint`, `AircraftDefinition`, `ScenarioBundle`, `TrajectoryTrack`)
- stable interfaces (`ScenarioProvider`, `SimulationStepper`, `TrajectorySink`)
- manager adapter (`ManagerStepper`) for incremental migration from legacy simulation manager.

Also formalize package boundaries with explicit `core`, `io`, `cli`, `web`, and `config` domains.

## Rationale
- Makes simulation contracts and orchestration easier to reason about.
- Provides stable seam for replacing implementations while preserving interfaces.
- Enforces framework-agnostic core behavior with direct tests.
