# AirSpaceSim Architecture

## Goals
- Keep simulation core independent from presentation and transport layers.
- Keep data contracts versioned and stable.
- Allow multiple ingestion and UI adapters without core changes.

## Module boundaries
- `airspacesim/core/`
  - Stable domain models and interfaces.
  - `models.py`: typed dataclasses (`Waypoint`, `AircraftDefinition`, `ScenarioBundle`, `TrajectoryTrack`).
  - `interfaces.py`: `ScenarioProvider`, `SimulationStepper`, `TrajectorySink`.
  - `stepper.py`: `ManagerStepper` adapter for existing manager runtime.
  - No dependency on UI/web framework.
- `airspacesim/io/`
  - Contract models, schema validation, serializers.
  - Input/output adapters (file, stream, network adapters as plugins).
  - Interoperability exporters (e.g., trajectory JSON -> CSV).
- `airspacesim/cli/`
  - User-facing commands and orchestration only.
- `airspacesim/web/`
  - Templates/static assets and optional API boundary package.
- `airspacesim/config/`
  - Settings domain boundary (`settings` re-export).

## Runtime interaction
1. Ingestion adapter reads external source.
2. Adapter maps raw payloads to canonical events.
3. Core engine applies events and advances simulation clock.
4. Output writer publishes trajectory/state via contract version.
5. UI consumes contract outputs through stable adapter/API.

## Decoupling rules
- UI never imports simulation internals directly.
- Core never imports UI assets/libraries.
- Integration occurs only through versioned contracts and adapter interfaces.

## Enforcement
- `tests/test_framework_agnostic_core.py` validates that `airspacesim/core` does not import UI/web frameworks or map-rendering modules.
