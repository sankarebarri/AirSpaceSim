# 07 — Phased Refactor Plan

Ordering principle: commit first, purify the engine second, replace public data third, then build content/i18n, then persistence/auth, then deployment. Every phase leaves the app runnable (`scripts/start_hosted_dev.py`) and all three test suites green (`pytest -q`, `just test-api`, `just test-web`).

---

## Phase 0 — Baseline commit and hygiene (no behaviour change)

**Goal**: a reviewable, revertable baseline.
**Files affected**: git state only, plus `.gitignore` micro-edits (06 §5) and removal of the duplicate nested brief copy / `CLAUDE(1).md` (requires approval).
**Steps**: commit pending modifications and deletions; commit `apps/`, `airspaces/`, `scripts/`, new `docs/`, `CLAUDE.md`, brief folder; tag the baseline.
**Behaviour preserved**: everything (no code changes).
**Tests required**: full suite green before and after.
**Rollback**: `git revert`/tag — trivial once committed; impossible before.
**Done when**: `git status` is clean; CI green on the pushed baseline.

## Phase 1 — Engine boundary, part A: pure stepping (03 E1–E2)

**Goal**: engine step path free of file IO, sleeps, threads, and global settings; hosted runtime drops its monkeypatch.
**Files**: `airspacesim/simulation/{aircraft_manager,aircraft}.py`, `airspacesim/core/*`, `airspacesim/settings.py`, `apps/api/app/sessions/runtime.py`; new core tests.
**Behaviour preserved**: legacy `AircraftManager` API and JSON outputs (golden-file characterisation before starting); hosted API responses unchanged.
**Tests**: golden contract files; determinism test (identical step sequences ⇒ identical snapshots); all existing suites.
**Rollback**: wrapper delegation means each extraction is a small commit; revert individually.
**Done when**: `runtime.py` contains no `save_aircraft_data = lambda: None`; engine modules import no `time.sleep` in the step path; root tests green.

## Phase 2 — Engine boundary, part B: Simulation façade, clock, events, separation monitor (03 E3–E5)

**Goal**: `Simulation`, `SimulationClock`, engine events, `SeparationMonitor` (one event per continuous violation), scheduled aircraft entry; run summaries derived server-side.
**Files**: new `airspacesim/core/` modules; `apps/api/app/sessions/runtime.py`, `services/runs.py`, schemas; `apps/web/src/lib/{conflict,practiceOutcome,simulateSummary}.ts` thinned to consumers; run summary persisted (`summary_json` column → small migration).
**Behaviour preserved**: Practice/Simulate UX outcomes identical (port TS semantics with mirrored test tables); Practice criteria remain scenario-specific, outside the general monitor.
**Tests**: monitor state-transition unit tests; parity tests between old TS-computed and new server-computed outcomes on the crossing-traffic scenarios; WS payload contract tests.
**Rollback**: feature-flag the server-computed summary (client keeps computing until parity confirmed), then remove the client computation.
**Done when**: separation state and LoS events come from the API; a stopped run has a persisted factual summary; frontend performs no separation math except display formatting.

## Phase 3 — Fictional environment replaces Gao data (04 §2–3)

**Goal**: no Gao-derived identifiers, fixes, airways, or names anywhere public.
**Files**: `airspaces/<new-pack>/**` (new), `airspaces/gao_demo/**` (removed after approval), `airspacesim/data/*.json` (content swap), `airspacesim/settings.py` (`AIRSPACE_CENTER` from environment), `cli/commands.py` (drop `gao_*` fallbacks), `scripts/*`, `apps/web/src/lib/simulateScenarios.ts`, affected tests and docs, CHANGELOG (breaking-data note for package users).
**Behaviour preserved**: same demo/lesson flows on new geometry; deterministic scenarios; contract shapes unchanged.
**Tests**: pack validation via `scripts/validate_airspace_package.py` (promoted into shared code + pytest); update fixtures asserting on names; browser smoke.
**Rollback**: pack swap is data-only — keep the old pack on a branch, not in main.
**Done when**: `grep -ri gao` over tracked files returns only historical CHANGELOG/audit references.

## Phase 4 — Scenario/environment schema versioning + validation (04 §4–5)

**Goal**: versioned, validated packs and scenario templates with plain-language errors; engine honours entry times.
**Files**: `airspacesim/io/contracts.py` (+ template validator), pack manifests (`version` fields), `apps/api/app/services/{practice_runs,scenarios}.py` (validate on load, stamp versions into run metadata), `scripts/validate_airspace_package.py` (delegates to shared validator).
**Behaviour preserved**: existing packs validate cleanly; invalid content produces readable 400s.
**Tests**: validator unit tests (missing route, duplicate callsign, bad level/speed, unknown command); API tests for invalid templates.
**Rollback**: validation initially warn-only behind a setting, then enforced.
**Done when**: every run record stores scenario + environment version identifiers.

## Phase 5 — Data-driven runners + Traffic Relationships + i18n

**Goal**: generic `ConceptPage`/`LearnRunner`/`PracticeRunner`/`SimulationRunner` + step components; lesson JSON served by the API and rendered, not duplicated in TSX; the five Traffic Relationships lessons; Vertical/Horizontal Separation visible as planned; EN/FR via central keys, operational commands English-only.
**Files**: `apps/api` (lesson/concept content endpoints), `apps/web/src` (runners, i18n setup, locales, catalogue from API), `airspaces/*/lessons/**` (Traffic Relationships content), existing CrossingTraffic pages converted last.
**Behaviour preserved**: Crossing Traffic Learn/Practice flows keep working throughout — convert them to the runners only after the runners prove out on Traffic Relationships (brief priority #6).
**Tests**: runner component tests; lesson-content contract tests; i18n key-coverage test (no hardcoded strings in translated areas); browser flow for the new journey; no prediction metrics displayed (explicit assertion per brief non-negotiable #10).
**Rollback**: bespoke pages remain routable until parity; route-level cutover per lesson.
**Done when**: adding a lesson requires JSON + locale keys only (prove with the fifth Traffic Relationships lesson); all five lessons complete in EN and FR.

## Phase 6 — PostgreSQL + minimal auth + persistence (05)

**Goal**: PG-verified migrations; `users`; sign-in/out/current-user; guest→user data migration; server-side `learning_progress` and run history; preferred language on profile.
**Files**: `apps/api/app/db/**` (models, migrations), auth module, `config.py` (SECRET_KEY, LOG_LEVEL), `apps/web` (auth UI — wire the existing Sign in button, account page), docs (`AUTHENTICATION.md`, `DATABASE.md`).
**Behaviour preserved**: guests keep full Learn/Practice/solo-Simulate access with immediate debriefs; existing anonymous sessions keep working.
**Tests**: migrations against PostgreSQL in CI; auth flow tests; protected-route rejection tests; guest-flow regression.
**Rollback**: auth routes additive; PG adoption via `DATABASE_URL` (SQLite path remains for local dev).
**Done when**: brief Phase-4 acceptance criteria pass (progress + summaries persist for signed-in users; guests unaffected).

## Phase 7 — Deployment readiness (05 §4–5)

**Goal**: deployable frontend + backend + PostgreSQL per brief acceptance criteria.
**Files**: structured logging config, `.env.example` completion, SPA-fallback serving config, Docker/compose (if chosen — 08-Q6), CI deploy checks, `docs/developer/DEPLOYMENT.md`, site disclaimer footer.
**Tests**: production build in CI; `/health` check in smoke script against a built deployment; route-refresh browser test.
**Done when**: brief §Deployment acceptance list is verifiably green in a staging environment.

## Phase 8 — Engine packaging decision (03 E6) — deliberately last

**Goal**: resolve what ships in the open-source engine wheel (static UI, dev server, CLI init assets, `hello.py`, shims, empty subpackages) via deprecation policy or a 1.0 boundary.
**Blocked on**: open questions 08-Q1/Q2; not urgent for the hosted product.
