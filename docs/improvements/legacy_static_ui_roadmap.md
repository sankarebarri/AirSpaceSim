# AirSpaceSim Roadmap

Last updated: 2026-02-23
Status model:
- `[NOT DONE]` planned, not started
- `[PARTIAL]` started but incomplete
- `[DONE]` completed and validated in this cycle

Policy:
- This roadmap contains active work only.
- Old completed items are removed to keep execution focused.
- Move completed items into the `Done` section during the cycle, then prune them after release.

## Partial

1. `[PARTIAL]` Release/packaging hardening
- finalize public docs for release quality while keeping internal workflow notes private
- add one reproducible local release flow (`build`, `twine check`, publish)
- add CI-level packaging smoke step (`pip install dist/*.whl` + `airspacesim init` smoke)

2. `[PARTIAL]` Workspace/runtime path consistency
- keep UI data polling and event sink writing on the same workspace path in all entry modes (`/templates`, `/airspacesim/templates`, `/airspacesim-playground/templates`)
- add regression test for path-mismatch cases (`:5500` static UI + `:8080` dev server)

3. `[PARTIAL]` Operator controls UX safety
- add aircraft ID and route ID autocomplete sourced from live state/contracts
- show authoritative command result feedback (`applied`, `skipped`, `rejected`, reason) in UI
- add guardrail UX for extreme sim-rate changes (warn/confirm threshold)

4. `[PARTIAL]` Contract/runtime convergence (from sim UI contract plan)
- enforce deterministic event ordering policy (`sequence` then `created_utc`) for same poll batch
- close remaining legacy-to-v1 adapter gaps and document final deprecation path
- decide stdin adapter status (implement as supported adapter or remove from plan)

5. `[PARTIAL]` Aircraft panel ergonomics
- add quick filters (route, status, flow)
- add compact live status strip (selected aircraft + sim rate + feed freshness)

## Not Done

1. `[NOT DONE]` Flight-plan style aircraft authoring
- UI form for `departure`, `destination`, ordered `route_ids`, `callsign`, `registration`
- batch insertion of multiple aircraft in one submit
- wire `RouteRegistry` as default resolver in runtime pipelines

2. `[NOT DONE]` Event lifecycle durability
- persist event-ingestion checkpoints across restarts
- add inbox compaction/pruning with optional archive export
- prevent replay of stale events after process restart unless explicitly requested

3. `[NOT DONE]` Startup/runtime command UX
- add `airspacesim run` orchestration command for simulation + UI workflow
- document operating modes (`headless`, `UI-assisted`, `playground`)

4. `[NOT DONE]` UI freshness semantics
- drive `Last Sync` from contract timestamps (`metadata.generated_utc`, `updated_utc`)
- add freshness states (`fresh`, `delayed`, `stale`) with explicit thresholds

5. `[NOT DONE]` Physics evolution
- heading/turn-rate transitions to reduce segment snap behavior
- vertical trend presentation from `vertical_rate_fpm` without conflicting with flow colors
- realism extension backlog (wind, schedules, envelopes, conflict hooks)

6. `[NOT DONE]` Scale and rendering strategy
- benchmark 500/1000 aircraft render/update performance
- define fallback strategy when DOM marker rendering degrades (canvas/throttling)
- set documented threshold for defaulting to batched scheduler

7. `[NOT DONE]` Architecture decision record for server split
- evaluate standalone server package boundary (`scenario in`, `events in`, `state/trajectory out`)
- publish ADR with go/no-go decision and migration impact

## Done

Use this section only for work completed in the current cycle before pruning.
- `[DONE]` None in this refreshed roadmap baseline.
