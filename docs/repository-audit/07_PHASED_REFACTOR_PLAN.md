# 07 — Phased Refactor Plan

**Updated 2026-07-16 to incorporate the owner's decisions in `08_OPEN_QUESTIONS.md`** (breaking changes allowed in 0.2.0; legacy static UI scheduled for retirement; `gao_demo` fully replaced; JSON packs; squashed PostgreSQL baseline; static-frontend + PaaS + managed-PG hosting with Docker for local dev; email+password session auth; 14-day anonymous-run retention).

Ordering principle: commit first, purify the engine second, replace public data third, then build content/i18n, then persistence/auth, then deployment. Every phase leaves the app runnable (`scripts/start_hosted_dev.py`) and all three test suites green (`pytest -q`, `just test-api`, `just test-web`).

---

## Phase 0 — Baseline commit and hygiene ✅ COMPLETED

Baseline commit `bf2af1b` pushed by the owner; `apps/`, `airspaces/`, scripts, and new docs are tracked. Remaining micro-items to fold into the next commit: `dashboard.html` deletion (owner's), `lessons.md` → `docs/content/traffic_relationships_spec.md` move, audit-document updates, `.gitignore` micro-fixes (06 §5), removal of the duplicate nested brief copy and `CLAUDE(1).md`.

## Phase 1 — Engine boundary, part A: pure stepping + approved removals (03 E1–E2, Q1)

**Goal**: engine step path free of file IO, sleeps, threads, and global settings; hosted runtime drops its monkeypatch. Because breaking changes are approved for 0.2.0, the confirmed-obsolete removals happen here rather than in a later deprecation phase.
**Files**: `airspacesim/simulation/{aircraft_manager,aircraft}.py`, `airspacesim/core/*`, `airspacesim/settings.py`, `apps/api/app/sessions/runtime.py`; removals: `airspacesim/hello.py` (+ export + `test_integration.py` usage), `airspacesim/routes/route_manager.py` (+ shim assertions in `test_structure_cleanup.py`), empty `airspacesim/{api,web,tests}` subpackages, `gao_*` fallbacks in `settings.py`/`cli/commands.py`, `new_aircraft.json` seed alias; new core tests; `CHANGELOG.md` + `docs/migration.md` entries for every removal.
**Behaviour preserved**: legacy `AircraftManager` public API and JSON contract outputs (golden-file characterisation before starting); hosted API responses unchanged.
**Tests**: golden contract files; determinism test (identical step sequences ⇒ identical snapshots); all suites updated for removals.
**Rollback**: small commits per extraction/removal; revert individually.
**Done when**: `runtime.py` contains no `save_aircraft_data = lambda: None`; no `time.sleep` in the engine step path; removals documented in CHANGELOG; root tests green.

## Phase 2 — Engine boundary, part B: Simulation façade, clock, events, separation monitor (03 E3–E5) ✅ CORE + SERVER COMPLETE

Delivered 2026-07-17 (tag `phase-2-simulation-core`): `Simulation`, `SimulationClock`, `EngineEvent` stream, `SeparationMonitor` (one event per continuous violation, TS-parity semantics), engine-scheduled aircraft entry (`appear_after_seconds` honoured end-to-end), separation state + live summary in API/WS snapshots, `runs.summary_json` persistence (Alembic `20260716_0004`), and server-side Practice outcome tracking outside the general monitor. **Remaining for full "done when"**: cutting the frontend debrief/summary UI over to the server-computed values and thinning `conflict.ts`/`practiceOutcome.ts`/`simulateSummary.ts` to display-only — deliberately deferred to Phase 5, where the debrief UI is rebuilt inside the generic runners anyway (per this phase's rollback note: client keeps computing until parity cutover).

**Goal**: `Simulation`, `SimulationClock`, engine events, `SeparationMonitor` (one event per continuous violation), scheduled aircraft entry; run summaries derived server-side.
**Files**: new `airspacesim/core/` modules; `apps/api/app/sessions/runtime.py`, `services/runs.py`, schemas; `apps/web/src/lib/{conflict,practiceOutcome,simulateSummary}.ts` thinned to consumers; run summary persisted (`summary_json` — lands in the squashed baseline if Phase 6 hasn't shipped it yet, otherwise a migration).
**Behaviour preserved**: Practice/Simulate UX outcomes identical (port TS semantics with mirrored test tables); Practice criteria remain scenario-specific, outside the general monitor.
**Tests**: monitor state-transition unit tests; parity tests between old TS-computed and new server-computed outcomes on the crossing-traffic scenarios; WS payload contract tests.
**Rollback**: feature-flag the server-computed summary (client keeps computing until parity confirmed), then remove the client computation.
**Done when**: separation state and LoS events come from the API; a stopped run has a persisted factual summary; frontend performs no separation math except display formatting.

## Phase 3 — New fictional FIR replaces gao_demo (04 §2–3, Q3) ✅ COMPLETE

Delivered 2026-07-17 (tag `phase-3-fictional-environment`; last pre-removal state tagged `pre-gao-removal`): `airspaces/nerava_fir` created with new geometry at 33.5N 41.0W and deleted `airspaces/gao_demo`; package seeds regenerated; `training_alpha` re-centred by exact longitude rotation (behaviour-preserving); fictional callsigns throughout; engine derives the traffic-flow centre from environment data; scripts/web/tests/docs migrated in the same change. Tracked-file Gao references now exist only in historical/instructional documents (brief, CLAUDE.md, CHANGELOG, migration notes, audit, timeline, archived planning docs).

**Goal**: a completely new fictional environment at **neutral fictional coordinates**; `airspaces/gao_demo` deleted; no Gao names, fixes, VOR/airway identifiers, frequencies, or exact geometry anywhere. No slug/seed/link compatibility required.
**Files**: `airspaces/<new-pack>/**` (new); `airspaces/gao_demo/**` (deleted after reference migration); `airspacesim/data/*.json` (content swap to fictional sample, `gao_airspace.json` deleted); `airspacesim/settings.py` (`AIRSPACE_CENTER` becomes environment-supplied); `scripts/seed_hosted_demo.py`, `start_hosted_dev.py`; `apps/web/src/lib/simulateScenarios.ts`; affected tests, docs, and defaults — all in the same migration; CHANGELOG breaking-data note.
**Behaviour preserved**: same demo/lesson *flows* on new geometry; deterministic scenarios; contract shapes unchanged.
**Tests**: pack validation via `scripts/validate_airspace_package.py` (promoted into shared code + pytest); update fixtures asserting on names; browser smoke.
**Rollback**: data-only swap; old pack remains in git history (tag before deletion), not in main.
**Done when**: `grep -ri gao` over tracked files returns only historical CHANGELOG/audit references; `airspaces/gao_demo` no longer exists.

## Phase 4 — Scenario/environment schema versioning + validation (04 §4–5, Q4) ✅ COMPLETE

Delivered 2026-07-17 (tag `phase-4-versioned-validation`): semver `version` on pack manifests, environment definitions, and all scenario templates (enforced by the package validator); shared validation module `airspacesim/io/templates.py` (single source for geometry/aircraft-plan/metadata checks incl. supported-command whitelist) with the seed script and `validate_airspace_package.py` delegating to it; hosted API validates templates at practice-run creation with plain-language 400s and stamps `content_versions` into scenario metadata and persisted run summaries. Entry times were already engine-honoured (Phase 2).

**Goal**: versioned, validated **JSON** packs and scenario templates with plain-language errors; engine honours entry times. (JSON confirmed canonical; any future friendly template generates JSON.)
**Files**: `airspacesim/io/contracts.py` (+ template validator), pack manifests (`version` fields), `apps/api/app/services/{practice_runs,scenarios}.py` (validate on load, stamp versions into run metadata), `scripts/validate_airspace_package.py` (delegates to shared validator).
**Behaviour preserved**: existing packs validate cleanly; invalid content produces readable 400s.
**Tests**: validator unit tests (missing route, duplicate callsign, bad level/speed, unknown command); API tests for invalid templates.
**Rollback**: validation initially warn-only behind a setting, then enforced.
**Done when**: every run record stores scenario + environment version identifiers.

## Phase 5 — Data-driven runners + Traffic Relationships + i18n (Q9 + content spec) ✅ CORE COMPLETE

Delivered 2026-07-18 (tag `phase-5-traffic-relationships`): curriculum + five TR lessons as data (`content/curriculum.v1.json`, `airspaces/training_alpha/lessons/tr_*.v1.json`, six new scenarios with classification metadata); content API endpoints; generic `LessonRunnerPage`/`ConceptPage` + curriculum-driven Learn page (planned placeholders for Vertical/Horizontal Separation); EN/FR i18n with central keys, coverage tests, and FR drafts awaiting owner review; server-summary cutover done (client separation math removed from practiceOutcome/simulateSummary). **Remaining in this phase's scope**: converting the bespoke CrossingTraffic Learn/Practice pages onto the runners (needs a CommandStep runner step for the management lesson) and translating the Practice intro pages — per the plan's route-level cutover strategy, those pages stay live and English until converted.

**Prerequisite reading**: `docs/content/traffic_relationships_spec.md` (authoritative content specification, moved from root `lessons.md`) alongside brief docs 04/07. Where it gives more detailed Traffic Relationships instructions, follow it unless it conflicts with `CLAUDE.md` or the non-negotiables.
**Goal**: generic `ConceptPage`/`LearnRunner`/`PracticeRunner`/`SimulationRunner` + step components; lesson JSON served by the API and rendered, not duplicated in TSX; the five Traffic Relationships lessons; Vertical/Horizontal Separation visible as planned; EN/FR via central keys, operational commands English-only. **French translations drafted by the implementer** for owner review of aviation/lesson terminology (Q9).
**Files**: `apps/api` (lesson/concept content endpoints), `apps/web/src` (runners, i18n setup, `locales/en` + `locales/fr`, catalogue from API), `airspaces/*/lessons/**` (Traffic Relationships content), existing CrossingTraffic pages converted last.
**Behaviour preserved**: Crossing Traffic Learn/Practice flows keep working throughout — converted to the runners only after the runners prove out on Traffic Relationships (brief priority #6).
**Tests**: runner component tests; lesson-content contract tests; i18n key-coverage test; browser flow for the new journey; assertion that no prediction metrics are displayed (brief non-negotiable #10).
**Rollback**: bespoke pages remain routable until parity; route-level cutover per lesson.
**Done when**: adding a lesson requires JSON + locale keys only (prove with the fifth Traffic Relationships lesson); all five lessons complete in EN and FR (FR pending owner terminology review).

## Phase 6 — PostgreSQL + email/password auth + persistence + retention (05, Q5/Q7/Q10)

**Goal**: **squashed single PostgreSQL-verified Alembic baseline** (Q5); `users`; email+password auth with secure server-side sessions and HTTP-only secure cookies (Q7); guest→user data migration; server-side `learning_progress` and run history for signed-in users; preferred language on the profile; **anonymous completed-run retention job, configurable, default 14 days** (Q10).
**Files**: `apps/api/app/db/**` (models; migrations squashed to one baseline covering the current schema + `users` + `summary_json` + retention-relevant indexes); auth module (registration, sign in/out, current-user, password hashing, session cookies); dev-only test-account seed; `config.py` (`SECRET_KEY`, `SESSION_*`, `RETENTION_*`, `LOG_LEVEL`); `apps/web` (wire the Sign in button, registration/account page, preferred-language setting); docs (`AUTHENTICATION.md`, `DATABASE.md`).
**Behaviour preserved**: guests keep full Learn/Practice/solo-Simulate access with immediate debriefs and local-storage progress/summaries; existing anonymous sessions keep working within retention.
**Tests**: migration tests upgrading from an **empty PostgreSQL database** (PG in CI); auth flow tests (register/login/logout/cookie security); protected-route rejection tests; retention job tests; guest-flow regression.
**Rollback**: auth routes additive; PG adoption via `DATABASE_URL` (SQLite path remains for quick local dev until compose lands).
**Done when**: brief Phase-4 acceptance criteria pass; baseline migration is the preserved start of future history; anonymous runs older than the retention window are pruned automatically.

## Phase 7 — Deployment readiness (05 §4–5, Q6) ✅ COMPLETE

Delivered 2026-07-18 (tag `phase-7-deployment`): API Dockerfile (repo-root context, migrate-then-serve entrypoint with DB wait), web Dockerfile (build + nginx SPA fallback) plus `dist/_redirects` for static hosts, root `docker-compose.yml` with PostgreSQL 16 and root `.env.example`, structured key=value API logging via `AIRSPACESIM_API_LOG_LEVEL`, loud production guard for unset `VITE_API_BASE_URL`, and `docs/developer/DEPLOYMENT.md`. Verified live on the compose stack: smoke script green (health/airspaces/runs/web HTML), registration + session cookie against containerized PostgreSQL, curriculum served from the image, a practice run simulating live in the container, deep-route refresh returning HTTP 200, structured logs flowing. The site disclaimer footer ships on all pages.

## Phase 7 — original scope (for reference)

**Goal**: deployable per the decided architecture — **static-hosted React frontend, PaaS-hosted FastAPI backend, managed PostgreSQL** — plus **Dockerfiles and local docker-compose** for portable development. Provider-specific configuration kept minimal and documented for PaaS portability.
**Files**: `Dockerfile` (api), `Dockerfile`/static-build docs (web), `docker-compose.yml` (api + web + postgres for local dev), structured logging config, `.env.example` completion, SPA-fallback config for the static host, CI production-build checks, `docs/developer/DEPLOYMENT.md`, site disclaimer footer.
**Tests**: production build in CI; `/health` check in the smoke script against a built deployment; route-refresh browser test; compose-up smoke locally.
**Done when**: brief §Deployment acceptance list is verifiably green in a staging environment reachable from the static frontend.

## Phase 8 — Legacy static UI retirement + engine packaging finalisation (03 E6, Q1/Q2) ✅ COMPLETE

Delivered 2026-07-18 (tag `phase-8-legacy-ui-retired`; last legacy state at `pre-legacy-ui-removal`): static UI, map helpers, dev server, workspace-init flow, and UI seed data removed from the package; `airspacesim init` repurposed into an airspace-package scaffolder (validated output); legacy tests retired or rewritten (headless quickstart + scaffolder tests); README/tutorial/documentation/boundary docs updated; wheel verified clean (54 files: cli/core/data/examples/io/routes/schemas/simulation/utils only). **All eight refactor phases are complete.**

## Phase 8 — original scope (for reference)

**Goal**: retire the legacy static Leaflet UI, file-based dev server, generated-workspace flow, and related wheel assets from the core package (decided — no compatibility package, no permanent shims). Tag the last release containing the legacy surface so its final state is preserved in git history. Optionally repurpose `airspacesim init` into an environment/scenario scaffolding command.
**Files**: `airspacesim/{static,templates,map,dev_server.py}`, root `dev_server.py`, `cli/commands.py` (init asset list → scaffolding or removal), `pyproject.toml` package-data, legacy tests (`test_browser_console_clean`, `test_phase1_clean_run`, `test_cli_init`, `test_docs_quickstart` — retired or rewritten against the new surface), README/docs updates, CHANGELOG.
**Behaviour preserved**: hosted app unaffected (it never used the static UI); PyPI users get a documented breaking release.
**Rollback**: tag before removal (`legacy-static-ui-final` or the 0.2.x release tag).
**Done when**: the wheel contains only engine code + schemas + data needed by the engine; no static UI assets; docs describe the retirement and the git tag where the old workflow lives.
