# AirSpaceSim Tutorial

> **The legacy static-UI walkthrough was retired in 0.2.0** (Phase 8,
> decision Q2). The old `airspacesim init` workspace, `dev_server.py`, and
> `templates/map.html` flow is preserved at the git tag
> `pre-legacy-ui-removal` for reference only.

## Where to go now

- **Use the application (recommended):**
  `python3 scripts/start_hosted_dev.py --seed` or
  `docker compose up --build` — see `docs/user/how_to_start_hosted_app.md`
  and `docs/developer/DEPLOYMENT.md`.
- **Use the engine as a library:**
  `docs/architecture/engine_usage_quickstart.md` covers the `Simulation`
  façade, commands, snapshots, and events.

## Headless engine run (still supported)

Scenario inputs fall back to the packaged fictional Nerava seeds; contract
outputs are written to `<cwd>/data/`:

```bash
python3 -m airspacesim.examples.example_simulation --max-wait 5
```

Outputs:

- `data/aircraft_state.v1.json` — canonical aircraft state contract
- `data/trajectory.v0.1.json` — trajectory output contract

Commands can still be applied headlessly through the inbox-event file
(`data/inbox_events.v1.json`) while the example runs — the canonical event
payloads are documented in `docs/ingestion.md`. Time acceleration is
per-manager: `AircraftManager(sim_rate=...)` or a `SET_SIMULATION_SPEED`
event scoped to that manager.

## Simulation quality tools

```bash
python3 -m airspacesim.examples.stress_simulation --aircraft 100 --duration 5 --speed 420
python3 -m airspacesim.examples.benchmark_simulation --aircraft 200 --steps 50 --writes 25
python3 -m airspacesim.examples.interoperability_export
```
