# Project Timeline and Milestone Tags

Every meaningful milestone gets an annotated git tag and a row here, in the
same change. Phases refer to `docs/repository-audit/07_PHASED_REFACTOR_PLAN.md`;
decisions refer to `docs/repository-audit/08_OPEN_QUESTIONS.md`.

| Date | Tag | Commit | Milestone |
|---|---|---|---|
| 2026-07-16 | `phase-0-baseline` | `bf2af1b` | Baseline commit: hosted app (`apps/`), airspace packages (`airspaces/`), scripts, and audit documents first tracked in git. Last state containing the pre-audit working tree as-is. |
| 2026-07-16 | — | `930982a` | Audit decisions Q1–Q10 recorded; `lessons.md` promoted to `docs/content/traffic_relationships_spec.md`; `dashboard.html` removed. |
| 2026-07-16 | `phase-1-engine-purification` | `3f1b5b0` | Phase 1 complete: pure engine step path (simulated seconds, no global speed multiplier, injectable file output, hosted runtime monkeypatch removed) plus all Q1-approved 0.2.0 removals. Last tag containing `airspacesim.hello`, the `route_manager` shim, and the legacy `gao_*`/`new_aircraft` fallbacks is `phase-0-baseline`. |
| 2026-07-17 | `phase-2-simulation-core` | `95cf2c1` | Phase 2 core + server complete: `Simulation` façade with deterministic clock, engine events, general `SeparationMonitor` (one event per continuous LoS), engine-scheduled aircraft entry, separation state in API/WS snapshots, persisted run summaries (`runs.summary_json`, Alembic `20260716_0004`), server-side Practice outcomes. Frontend cutover to server summaries deferred to Phase 5. |
| 2026-07-17 | `pre-gao-removal` | `b79fd13` | Last state containing `airspaces/gao_demo` and the Gao-derived package seeds, before the Phase 3 fictional-environment migration. |
| 2026-07-17 | `phase-3-fictional-environment` | `941d88d` | Phase 3 complete: fictional Nerava FIR (`airspaces/nerava_fir`, 33.5N 41.0W, all-new geometry and identifiers) replaces `gao_demo`; package seeds regenerated; `training_alpha` re-centred to 16.25N 40.0W by exact longitude rotation; fictional callsigns everywhere; engine derives traffic-flow centre from environment data; scripts/web/tests/docs migrated in the same change. |

## Tagging conventions

- Tag name: `phase-<n>-<short-slug>` for refactor phases; `v<semver>` for PyPI
  releases; `pre-<event>` for last-state-before tags (e.g. `pre-gao-removal`
  before deleting `airspaces/gao_demo` in Phase 3, per decision Q3).
- Tags are annotated (`git tag -a`) and pushed together with the branch.
- When a phase deletes user-visible content or workflows, the row must name
  the last tag that still contains them.
