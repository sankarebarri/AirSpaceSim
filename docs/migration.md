# Migration Notes

## 0.2.0 breaking changes (engine cleanup)

Approved removals with no deprecation cycle (see
`docs/repository-audit/08_OPEN_QUESTIONS.md`, Q1):

- **`airspacesim.hello` / `say_hello`** — removed. Tutorial artefact with no
  replacement.
- **`airspacesim.routes.route_manager`** — removed. Import
  `airspacesim.routes.manager.RouteManager` instead.
- **`airspacesim.config`, `airspacesim.api`, `airspacesim.web`,
  `airspacesim.tests` subpackages** — removed. For settings, import
  `airspacesim.settings.settings` directly; the hosted API/web apps live in
  `apps/`, not inside the engine package.
- **`settings.SIMULATION_SPEED` (process-wide time acceleration)** — removed.
  Use `AircraftManager(sim_rate=...)` or
  `AircraftManager.set_simulation_speed(...)`; the rate is scoped to one
  manager. `Aircraft.update_position(time_step)` now interprets `time_step`
  as **simulated seconds** and no longer applies any global multiplier.
- **Legacy filename fallbacks** — removed: `gao_airspace.json`,
  `gao_airspace_config.json` (use `airspace_config.json`), and
  `new_aircraft.json` (use `aircraft_ingest.json`). The packaged
  `data/gao_airspace.json` and `data/new_aircraft.json` seed files were
  deleted.

New in 0.2.0:

- `AircraftManager(enable_file_output=False)` (also exposed through
  `initialize_manager_from_scenarios(...)`) disables all JSON file writes so
  embedding applications can drive the engine without filesystem side
  effects. The hosted API uses this instead of monkeypatching
  `save_aircraft_data`.

## Naming migration (pre-0.2.0 history)
- Old: `gao_airspace.json`
- New: `airspace_config.json`

- Old: `new_aircraft.json`
- New: `aircraft_ingest.json`

## Contract migration map

| Legacy / older contract | Current preferred contract | Status |
|---|---|---|
| `airspace_config.json` (unversioned root) | `map_config.v1.json` (`airspacesim.map_config`) | Preferred migrated, legacy accepted |
| `aircraft_data.json` legacy root only | `aircraft_state.v1.json` + `aircraft_data.json` envelope | Preferred migrated, legacy shim retained |
| `scenario_airspace.v1.json` + `scenario_aircraft.v1.json` | `scenario.v0.1.json` (`airspacesim.scenario`) | Preferred migrated, split files accepted |
| n/a | `trajectory.v0.1.json` (`airspacesim.trajectory`) | New canonical output |

## Current behavior
- Writers use new generic names.
- Since 0.2.0, readers accept only the generic names (legacy fallbacks removed).

## Recommended user action
- Rename legacy files to generic names.
- Update scripts and deployment paths to `data/airspace_config.json` and `data/aircraft_ingest.json`.

## Schema version evolution
- New unified scenario contract is available at `data/scenario.v0.1.json`.
  - Existing split contracts (`scenario_airspace.v1.json`, `scenario_aircraft.v1.json`) remain accepted.
- New trajectory output contract is available at `data/trajectory.v0.1.json`.
  - `aircraft_state.v1.json` and `aircraft_data.json` remain available for compatibility.
