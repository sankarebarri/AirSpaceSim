# Contract Compatibility Matrix

| Producer | Contract | Version | Consumers | Status |
|---|---|---|---|---|
| Simulation runtime | `airspacesim.aircraft_state` | `1.0` | UI polling, tooling | Canonical |
| Simulation runtime | `airspacesim.aircraft_data` | `1.0` (+ legacy root shim) | Legacy UI readers | Compatibility |
| Simulation runtime | `airspacesim.trajectory` | `0.1` | Exporters/audit workflows | Canonical |
| Scenario authoring | `airspacesim.scenario` | `0.1` | Scenario loader | Canonical (preferred) |
| Scenario authoring | `airspacesim.scenario_airspace` + `airspacesim.scenario_aircraft` | `1.0` | Scenario loader | Compatibility |
| Event producers | `airspacesim.inbox_events` | `1.0` | Event adapters + engine | Canonical |
| UI config | `airspacesim.map_config` | `1.0` | Map renderer | Canonical (preferred) |
| UI runtime adapter | `airspacesim.ui_runtime` | `1.0` | Frontend source resolution | Canonical |

## Policy

- Backward-compatible additions may occur within existing versions.
- Breaking changes require a new `schema.version` and migration notes.
- Legacy compatibility contracts remain read-compatible until roadmap deprecation.
