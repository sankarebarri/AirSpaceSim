# 03 — Engine Extraction Plan

## 1. Where engine-domain code lives today

| Responsibility (brief) | Current location | Layer |
|---|---|---|
| Simulation clock / time | Wall-clock: `time.sleep` loops in `AircraftManager.simulate_aircraft`/`run_batched_for` and `apps/api/app/sessions/runtime.py:_run_loop`; `settings.SIMULATION_SPEED` global multiplier inside `Aircraft.update_position` | Engine + API (impure) |
| Aircraft state | `airspacesim/simulation/aircraft.py` | Engine ✅ |
| Movement / route traversal | `aircraft.py` (`update_position`, segment walking, `_destination_point`) | Engine ✅ |
| Heading / level changes | `aircraft.py` (`assign_heading`, `_update_vertical_profile`, radial/direct-to/hold modes) | Engine ✅ |
| Commands | `airspacesim/simulation/events.py` (`apply_events_idempotent`, 13 types) | Engine ✅ |
| Scripted events / entry-exit | Partial: `appear_after_seconds` exists in scenario templates but is honoured only by `scripts/seed_hosted_demo.py` sleeping in real time before POSTing commands — **not** by the engine | Scripts (wrong layer) |
| Horizontal/vertical separation | `apps/web/src/lib/conflict.ts` (`isSeparated`, `distanceNm`) | React (wrong layer) |
| Loss-of-separation state transitions | `apps/web/src/lib/simulateSummary.ts` (`violatingPairs` set — correct one-event-per-continuous-violation semantics) | React (wrong layer) |
| Practice evaluation | `apps/web/src/lib/practiceOutcome.ts` (scenario-metadata-driven, client-side) | React (wrong layer per persistence, right layer per "not in general monitor") |
| Snapshots | `AircraftManager.save_aircraft_data` (file writes) and `SimulationRuntimeSession.state_snapshot()` (dict) — duplicated serialisation | Engine + API (duplicated) |
| Emitted engine events | None. The WS "events" are transport frames; the engine emits nothing | Missing |
| Run summaries | `simulateSummary.ts` / `practiceOutcome.ts`, displayed only, never persisted | React (wrong layer) |

## 2. Coupling problems (evidence)

1. **File IO in the step path** — `save_aircraft_data` is called from `simulate_aircraft`, `run_batched_for`, `wait_for_completion`; the hosted runtime must neutralise it: `self.manager.save_aircraft_data = lambda: None` (`runtime.py:51`) and again around each command application (`runtime.py:147-152`).
2. **Global mutable settings** — `Aircraft._sanitize_speed_kt` and `update_position` read `settings.SPEED_GUARDRAIL_MODE` / `SIMULATION_SPEED`; `AircraftManager.set_simulation_speed` *writes* the global. Two concurrent hosted runs share one process-wide multiplier if that legacy path is used (the hosted runtime avoids it by passing `interval*sim_rate` per session — two divergent speed mechanisms).
3. **Gao default inside engine logic** — `settings.AIRSPACE_CENTER=(16.25,-0.03)` feeds `classify_traffic_flow_from_waypoints`, so `traffic_flow` labels are wrong for any non-Gao environment.
4. **Threads in the engine** — thread-per-aircraft mode, monitor and cleanup threads bind the engine to real time and make deterministic replay impossible.
5. **No aircraft entry/exit scheduling** — scripted entry times live outside the engine (seed script sleeps), so scenarios are not self-contained or reproducible.
6. **No separation monitoring in core** — duplicated conceptually between Practice (pairwise) and Simulate (all pairs) in TS; sampled at UI poll cadence (1 s refetch), so brief LoS between polls can be missed — a correctness bug the server-side monitor fixes for free.
7. **`ManagerStepper` reaches into privates** — `manager._step_all_aircraft` (`core/stepper.py:15`).
8. **React coupling** — none for movement (good). FastAPI coupling — none inside `airspacesim/` (verified: no fastapi/sqlalchemy imports in the package; `docs/architecture/engine_boundary.md` already states the rule).

## 3. What already belongs to the reusable engine (keep as-is)

`aircraft.py` physics, `events.py` command application, `scenario_runner.py` loading (minus cwd guessing), `core/models.py` + `core/interfaces.py`, `io/contracts.py` validators, `io/airspaces.py` normalisation, `routes/*`, `utils/*`, `performance_database.py` + its JSON.

## 4. What should remain application orchestration

- Run lifecycle, persistence, checkpoints, WS broadcast (`apps/api/app/sessions/*`, `services/*`).
- Practice completion criteria and debrief composition (reads engine events + scenario metadata; must not enter the general monitor — brief non-negotiable #7).
- Lesson step progression, assistance levels, catalogue, navigation (web).
- Wall-clock pacing: the API decides how often to call `simulation.step()`; the engine only ever receives simulated seconds.

## 5. Proposed core package boundary and public API

Do **not** physically move `airspacesim/` to `packages/airspacesim-core/` yet — it is a published package and the import name is fine. Establish the boundary *inside* the package first; a rename/move is a later, mechanical decision (open question in 08).

Target public API (grows from `core/`):

```python
from airspacesim import (
    Simulation,            # NEW façade
    SimulationClock,       # NEW deterministic stepped clock
    ScenarioBundle, AircraftDefinition, Waypoint,   # existing
    SeparationMonitor, SeparationStandard,          # NEW
    EngineEvent,                                    # NEW typed events
    load_scenario_bundle, apply_events_idempotent,  # existing
)

sim = Simulation(scenario=bundle, standards=SeparationStandard(horizontal_nm=10, vertical_ft=1000))
sim.issue_command("AFR612", {"type": "SET_FL", "flight_level": 310})
sim.step(seconds=0.25)          # simulated seconds; no sleeping, no threads
snapshot = sim.snapshot()       # serialisable dict, single source of truth
events = sim.drain_events()     # aircraft_entered/exited, separation_loss_started/ended, command_applied…
```

Key rules:
- `Simulation` owns a monotonic simulated clock; `sim_rate` becomes an application concern (step more simulated seconds per real tick).
- `SeparationMonitor` ports the TS semantics exactly: separated iff `horizontal ≥ min_h OR vertical ≥ min_v`; one continuous violation per pair = one event (`separation_loss_started` … `separation_loss_ended`), never per tick.
- Aircraft entry/exit becomes engine-scheduled (`entry_time_seconds` honoured by `step()`), replacing the seed script's real-time sleeps.
- Snapshot serialisation defined once in core; `AircraftManager.save_aircraft_data` and `SimulationRuntimeSession.state_snapshot()` both become consumers.
- File writing moves to a `TrajectorySink`/publisher adapter (the Protocol already exists in `core/interfaces.py`).

## 6. Migration sequence (maps to 07 phases)

1. **E0 — Baseline commit + characterisation.** Commit everything; capture current snapshots/contract outputs as golden files.
2. **E1 — Purify stepping.** Extract pure `step(seconds)` from `AircraftManager` (no IO, no sleep, no global speed); keep the legacy threaded/file-writing manager as a thin wrapper delegating to it. Root tests must stay green; hosted runtime drops its monkeypatch.
3. **E2 — Inject configuration.** Engine reads guardrails/centre from an injected `EngineConfig`; `settings.py` keeps workspace-path duties for the legacy CLI only. Remove Gao centre default from engine behaviour (environment supplies it).
4. **E3 — `Simulation` façade + clock + engine events.** Wrap fleet + commands + scheduled entries; add `drain_events()`. API runtime session becomes a driver of `Simulation`.
5. **E4 — `SeparationMonitor` in core.** Port `conflict.ts`/`simulateSummary.ts` semantics with unit tests mirroring the TS behaviour; API includes separation state in snapshots and persists LoS events; frontend consumes instead of computing (TS math kept only for display until parity confirmed, then thinned).
6. **E5 — Run summaries server-side.** Factual Simulate summary and Practice outcome derivation move to API services (Practice criteria stay scenario-specific, outside the monitor); persist `summary_json` on the run.
7. **E6 — Package boundary finalisation (DECIDED — see 08 Q1/Q2).** Breaking changes are approved for 0.2.0. Confirmed-obsolete removals (`hello.py`, `routes/route_manager.py` shim, empty subpackages, `gao_*` fallbacks, obsolete seed aliases) happen early, in Phase 1 of 07. The legacy static UI, templates, dev server, and CLI-init workspace assets are **scheduled for retirement** from the wheel (07 Phase 8), preserved via git history/release tag — no compatibility package, no permanent shims. `airspacesim init` may be repurposed into an environment/scenario scaffolding command.

## 7. Test strategy

- Every phase: root 94 tests + `apps/api` tests + `apps/web` tests green (`just test`, `just test-api`, `just test-web`).
- New core tests: deterministic stepping (same scenario + same step sequence ⇒ identical snapshots), clock independence from wall time, monitor state transitions (enter/exit violation, multi-pair, re-entry counts as a new event), scheduled entry/exit.
- Golden-file characterisation of `aircraft_state.v1` / `trajectory.v0.1` outputs before E1, asserted after each phase (contract compatibility promise in `docs/compatibility-matrix.md`).
- Port the TS monitor semantics as table-driven cases shared conceptually between vitest (existing behaviour) and pytest (new core) until the TS copy is thinned.

## 8. Open-source readiness concerns

- The wheel currently ships a demo UI, dev server, Gao-derived seed data, and `hello.py` — not the image of a focused engine. Resolution is now decided: obsolete items removed in 0.2.0 (07 Phase 1), Gao data replaced (07 Phase 3), static UI retired from the wheel (07 Phase 8).
- Engine docstrings/logs use emoji and operational-sounding phrasing; fine for now, review before promotion.
- `README.md` mixes library and hosted-app identities; the engine needs its own README section or subpackage README before open-sourcing (see 06).
- License is MIT and consistent (`LICENSE`, classifiers) — no blocker.
- No runtime dependencies in the engine (`dependencies = []`) — excellent for reuse; keep it that way (the brief's forbidden-dependency list is currently satisfied).
