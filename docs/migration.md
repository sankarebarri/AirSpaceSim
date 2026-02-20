# Migration Notes (Draft)

## Naming migration
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
- Readers accept both new and legacy names during transition.

## Recommended user action
- Rename legacy files to generic names.
- Update scripts and deployment paths to `data/airspace_config.json` and `data/aircraft_ingest.json`.

## Schema version evolution
- New unified scenario contract is available at `data/scenario.v0.1.json`.
  - Existing split contracts (`scenario_airspace.v1.json`, `scenario_aircraft.v1.json`) remain accepted.
- New trajectory output contract is available at `data/trajectory.v0.1.json`.
  - `aircraft_state.v1.json` and `aircraft_data.json` remain available for compatibility.
