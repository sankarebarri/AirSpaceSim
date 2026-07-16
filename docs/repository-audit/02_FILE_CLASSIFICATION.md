# 02 — File Classification

Classifications: `KEEP`, `KEEP AND DOCUMENT`, `REFACTOR`, `MOVE`, `SPLIT`, `MERGE`, `RENAME`, `DELETE CANDIDATE`, `GENERATED — GITIGNORE`, `INVESTIGATE`, `MISSING — CREATE`.

**Updated 2026-07-16 after the owner's decisions** (see `08_OPEN_QUESTIONS.md`): rows previously marked `DELETE CANDIDATE` that the owner approved now read `DELETE (approved — 08 Qn)` and are scheduled in the phased plan; remaining `DELETE CANDIDATE`/`INVESTIGATE` rows are still unapproved proposals. "Evidence" cites imports, tests, tooling, or git state verified during the audit.

## 2.1 Engine package — `airspacesim/`

| Path | Classification | Reason / Evidence | Proposed action | Risk |
|---|---|---|---|---|
| `airspacesim/simulation/aircraft.py` | KEEP (minor REFACTOR later) | Core physics: route following, heading/radial/direct-to/hold, vertical profile. Imported by manager, runtime session, tests. Only impurity: reads global `settings` for speed guardrails/sim speed. | Inject config instead of global `settings` during engine-boundary phase. | Low |
| `airspacesim/simulation/aircraft_manager.py` | SPLIT | Mixes pure stepping (`_step_all_aircraft`, `add_aircraft`) with wall-clock threads (`simulate_aircraft`, `monitor_new_aircraft`, `cleanup_finished_aircraft`) and file IO (`save_aircraft_data`); hosted runtime monkeypatches the file writes away (`apps/api/app/sessions/runtime.py:51`). | Split into pure `Fleet`/stepper (core) + file-publishing/threaded compatibility wrapper (legacy adapter). | High |
| `airspacesim/simulation/events.py` | KEEP AND DOCUMENT (REFACTOR later) | Canonical command application, 13 command types, idempotent semantics, used by both legacy loop and hosted API. 585-line if/elif chain worth a command-registry refactor eventually. | Document command catalogue; later restructure into per-command handlers. | Low |
| `airspacesim/simulation/scenario_runner.py` | KEEP (REFACTOR later) | Scenario loading/normalisation to `ScenarioBundle`; used by API and examples. File-path resolution logic belongs in an adapter, not core. | Keep; move path-guessing (cwd candidates) into IO adapter layer. | Low |
| `airspacesim/simulation/performance.py` | KEEP | Stress/benchmark helpers used by `tests/test_performance_tools.py` and example scripts. | None. | Low |
| `airspacesim/simulation/performance_database.py` + `airspacesim/data/aircraft_performance.v1.json` | KEEP AND DOCUMENT | Data-driven performance profiles (turn rate, climb/descent, speed limits). Exactly the brief's "domain constants as data" pattern. Untracked data file — must be committed. | Commit `aircraft_performance.v1.json`; document authoring format. | Low |
| `airspacesim/simulation/interpolation.py` | KEEP | Pure function used by `aircraft.py`. | None. | Low |
| `airspacesim/core/{models,interfaces,stepper}.py` | KEEP | Typed domain models + Protocols + `ManagerStepper`; the seed of the public core API. `stepper.py` reaches into `manager._step_all_aircraft` (private) — tidy during boundary work. | Grow into the `Simulation` façade per 03. | Low |
| `airspacesim/io/contracts.py` | KEEP AND DOCUMENT | 645 lines of envelope/validators for every contract; used by manager, runner, API services, tests. | Keep; consider per-contract split only if it grows. | Low |
| `airspacesim/io/adapters.py`, `io/exporters.py`, `io/airspaces.py` | KEEP | File snapshot/event adapters; CSV trajectory export; airspace-package normalisation used by API services and seeds. | None. | Low |
| `airspacesim/settings.py` | REFACTOR | Global mutable singleton; cwd-dependent path resolution; hardcoded `AIRSPACE_CENTER=(16.25,-0.03)` (Gao) consumed by traffic-flow classification; engine physics reads `SIMULATION_SPEED` from it. | Split: engine constants → injectable config; workspace paths → legacy CLI/adapter settings; remove Gao default from engine. | High |
| `airspacesim/routes/{manager,processor,registry}.py` | KEEP | Route construction/stitching; `registry.py` has deterministic route resolution + tests (`test_route_registry.py`). | None. | Low |
| `airspacesim/routes/route_manager.py` | DELETE (approved — 08 Q1) | Self-described compatibility shim re-exporting `manager.RouteManager`; kept alive by `tests/test_structure_cleanup.py`. Breaking changes approved for 0.2.0. | Remove in Phase 1 with CHANGELOG/migration-doc entry; update `test_structure_cleanup.py`. | Low |
| `airspacesim/utils/*` | KEEP | Conversions/bearing used everywhere; `logger.py` and `logging_config.py` overlap slightly (MERGE candidate, trivial). | Optionally merge the two logging modules. | Low |
| `airspacesim/cli/commands.py` | KEEP (REFACTOR when data changes) | `airspacesim init` bootstraps the legacy workspace; references `gao_airspace.json` legacy fallbacks. Tested by `test_cli_init.py`, `test_docs_quickstart.py`. | Update asset list when Gao data is replaced. | Medium |
| `airspacesim/dev_server.py` + root `dev_server.py` | KEEP (legacy surface) | Compatibility dev server for package users; root file is a 8-line wrapper. README/docs/tests reference it. | Keep until the legacy static UI is formally retired (see `docs/architecture/legacy_static_ui_decision.md`). | Low |
| `airspacesim/static/`, `airspacesim/templates/map.html` | KEEP until Phase 8, then RETIRE (decided — 08 Q2) | Legacy Leaflet UI shipped in the wheel; exercised by `test_browser_console_clean.py`, `test_phase1_clean_run.py`. Retirement scheduled; final state preserved via git history/release tag, no compatibility package. | Remove from the wheel in Phase 8 with legacy tests retired/rewritten. | Medium |
| `airspacesim/map/{renderer,marker_manager}.py` | INVESTIGATE | Leaflet map-config builders. No imports found from `apps/` or root tests referencing them directly — verify external/package users before touching. | Confirm usage; likely moves out of core with the static UI. | Medium |
| `airspacesim/hello.py` + `say_hello` export | DELETE (approved — 08 Q1) | Tutorial artefact exported from `__init__`; referenced by `tests/test_integration.py` only. | Remove export + test usage in Phase 1; CHANGELOG entry. | Low |
| `airspacesim/api/__init__.py`, `web/__init__.py`, `config/__init__.py`, `tests/__init__.py` | DELETE (approved — 08 Q1) | Empty/near-empty placeholder subpackages inside the engine; `config` only re-exports `settings`; the real API/web live in `apps/`. Nothing imports `airspacesim.api`/`airspacesim.web` (grep). Owner is the only known user — no deprecation shim needed. | Remove in Phase 1; CHANGELOG entry. | Low |
| `airspacesim/data/*.json` (gao_airspace, airspace_data, airspace_config, map_config.v1, scenario_airspace.v1, scenario.v0.1, ui_runtime.v1, render_profile.v1) | REFACTOR (content replacement approved — 08 Q3) | Package seed data is Gao-derived: `GAO_VOR`, real-looking fixes (ETRUL, PILTI, OPUGO…), real airway ids (UA612, UG859, UR971…). Decision: fully fictional environment at neutral coordinates. | Replace contents in Phase 3; keep file names/contracts. `gao_airspace.json` → DELETE (approved, legacy fallback only). | Medium |
| `airspacesim/data/{aircraft_data,aircraft_state.v1,trajectory.v0.1,inbox_events.v1,aircraft_ingest,new_aircraft}.json` | KEEP (seed/runtime templates) | Empty-ish runtime output/ingest templates copied by `init`. `new_aircraft.json` is the legacy alias (fallback in settings) — DELETE approved (08 Q1). | Keep templates; drop `new_aircraft.json` alias + settings fallback in Phase 1. | Low |
| `airspacesim/schemas/*.schema.json` | KEEP | JSON Schemas validated by `tests/test_schemas.py`, shipped in wheel. | None. | Low |
| `airspacesim/examples/*.py` | KEEP | Stress/benchmark/export examples referenced in README and copied by init. | None. | Low |

## 2.2 Hosted API — `apps/api/` (all UNTRACKED — commit first)

| Path | Classification | Reason / Evidence | Proposed action | Risk |
|---|---|---|---|---|
| `apps/api/app/main.py`, `config.py`, `middleware.py`, `limits.py`, `dependencies.py`, `paths.py` | KEEP AND DOCUMENT | Clean app factory; production CORS guard; rate limiting; body-size cap. | Commit; document env vars. | Low |
| `apps/api/app/session_identity.py` | KEEP (extend later) | Anonymous session scoping — this is the current "auth". Brief wants minimal real auth added on top; guest flow already works. | Keep as guest identity; add users/auth alongside in Phase 4. | Low |
| `apps/api/app/sessions/{registry,runtime}.py` | KEEP (REFACTOR with engine) | Server-authoritative sim loop. Contains the `save_aircraft_data = lambda: None` monkeypatch and wall-clock stepping — both symptoms of engine impurities; simplify once core exposes a pure stepper. | Rework against the new core API in Phase 1/2 of 03. | Medium |
| `apps/api/app/services/{runs,scenarios,airspaces,practice_runs}.py` | KEEP | Application services; practice-run creation from packages is the content pipeline. | Commit. | Low |
| `apps/api/app/db/*` (models, repositories, session, migrations) | KEEP AND DOCUMENT | Alembic with 3 migrations incl. session scoping; tests exist (`test_migrations.py`). Baseline is SQLite-flavoured. | Verify/adjust for PostgreSQL in Phase 4 (see 05). | Medium |
| `apps/api/app/ws/hub.py` | KEEP | WebSocket broadcast hub with tests. | None. | Low |
| `apps/api/tests/` (11 files) | KEEP | Real coverage of health, runs, scenarios, sessions, ws, migrations, repositories. | Commit; extend per 03/05. | Low |
| `apps/api/.env.example` | KEEP AND DOCUMENT | Exists and is sane; missing `ENVIRONMENT`, secret-key, log-level entries the brief requires. | Extend in Phase 4/5. | Low |
| `apps/api/var/airspacesim-api.db`, `apps/api/airspacesim_api.egg-info/` | GENERATED — GITIGNORE | Covered by existing `var/`, `*.db`, `*.egg-info/` rules; present on disk only. | Nothing to do. | Low |

## 2.3 Web app — `apps/web/` (all UNTRACKED — commit first)

| Path | Classification | Reason / Evidence | Proposed action | Risk |
|---|---|---|---|---|
| `src/app/{App,routes,query-client}.tsx/ts`, `main.tsx`, `index.html`, `vite.config.ts`, `tsconfig.json`, `package.json`, `package-lock.json` | KEEP | Standard app shell; lock file must be committed. | Commit. | Low |
| `src/components/TrafficMap.tsx` (897 lines) | KEEP (SPLIT later) | The reusable map renderer — central asset. Oversized; label placement, measurement, overlays could split. | Split into subcomponents opportunistically. | Low |
| `src/pages/RunDetailPage.tsx` (1,869 lines) | SPLIT | Monolith: run workspace + command forms + practice/simulate panels + debrief UI in one file. | Extract command console, run header, debrief sections; becomes the base of `SimulationRunner`. | Medium |
| `src/lib/conflict.ts` | MOVE (logic to engine) | Separation minima + `isSeparated` in TS — engine-domain logic per brief. Well-written; semantics should be ported to the core `SeparationMonitor`, with the TS copy reduced to display helpers. | Port semantics to core in 03 Phase 3; keep thin display math client-side. | High |
| `src/lib/practiceOutcome.ts` | REFACTOR | Practice evaluation reads scenario metadata (good, data-driven) but runs client-side and is never persisted. | Move outcome derivation server-side (run summary); keep client rendering. | High |
| `src/lib/simulateSummary.ts` | REFACTOR | General LoS monitor: correct one-event-per-continuous-violation semantics, but client-side, unpersisted, and only sampled at poll rate. | Reimplement in core monitor; persist as run summary. | High |
| `src/lib/simulateScenarios.ts` | REFACTOR | Hardcoded Simulate registry pointing at `gao_demo`. Comment admits it's deliberate MVP hardcoding. | Drive from `/api/v1/airspaces` package manifests. | Low |
| `src/pages/CrossingTraffic{Intro,Learn,PracticeIntro,Practice2Intro}Page.tsx` | REFACTOR (fold into runners) | Bespoke per-lesson pages with hardcoded callsigns/copy — explicitly what the brief forbids for *new* lessons. Behaviour must be preserved while generic `LearnRunner`/`PracticeRunner` are introduced. | Convert to data-driven runners in content phase; do not delete until parity. | Medium |
| `src/pages/HeadingVersusRadialLessonPage.tsx` | REFACTOR | Hardcoded `lessonSteps` duplicating `airspaces/training_alpha/lessons/heading_vs_radial.v1.json`. | Same as above; serve lesson JSON via API. | Medium |
| `src/pages/{Home,Learn,Airspaces,Scenarios,Simulate,SimulateBrief,Runs}Page.tsx` | KEEP (light REFACTOR) | Catalogue/navigation pages; Learn catalogue is hardcoded; `LearnPage` has a non-functional "Sign in" button (brief: no broken controls). | Data-drive catalogues; remove or wire the Sign in button. | Low |
| `src/lib/{api,session,format,learnProgress,scenario-map}.ts`, `src/types/api.ts` | KEEP | Clean API client with env-based URL + session header; guest-local progress in localStorage matches brief. | Commit. | Low |
| `tests/` (8 vitest files) | KEEP | Component/route/api tests. | Commit; extend with runner tests later. | Low |
| `.env.local` | GENERATED — GITIGNORE | Ignored by `.env.*` rule; `.env.local.example` is kept by the `!.env.*.example` negation. | Nothing to do. | Low |
| `src/assets/console-preview.jpg`, `public/README.md`, `src/{features,hooks}/README.md` | KEEP | Placeholder structure docs; harmless. | Commit. | Low |

## 2.4 Content — `airspaces/` (UNTRACKED — commit first)

| Path | Classification | Reason / Evidence | Proposed action | Risk |
|---|---|---|---|---|
| `airspaces/training_alpha/**` | KEEP AND DOCUMENT | Fictional pack (Alpha VOR + generic fixes) with manifest, 4 scenarios, 7 lesson JSONs; already the environment-pack pattern the brief wants. Centered on Gao coordinates (16.25, −0.03) — geometry-only reuse; see 04. | Commit; becomes the template for the canonical fictional environment. | Low |
| `airspaces/gao_demo/**` | DELETE after replacement (approved — 08 Q3) | Renamed "Sahel Control" but retains `gao_demo` id, `GAO_VOR`, real fixes/airways, "Gao Sector Traffic" scenario title. Referenced by `scripts/seed_hosted_demo.py`, `scripts/start_hosted_dev.py`, `apps/web/src/lib/simulateScenarios.ts`, `docs/user/*`. No slug/seed compatibility required. | Phase 3: create a new fictional pack at neutral coordinates, migrate all references in one change, tag, then delete `gao_demo`. | Medium |

## 2.5 Scripts, root files, config

| Path | Classification | Reason / Evidence | Proposed action | Risk |
|---|---|---|---|---|
| `scripts/{start_hosted_dev,seed_hosted_demo,smoke_hosted_app,validate_airspace_package}.py` | KEEP AND DOCUMENT | Dev workflow entry points; validate script imports from seed script (acceptable, slightly odd). All untracked. Tests exist (`test_seed_hosted_demo_validation.py`, `test_validate_airspace_package.py`). | Commit; reference from developer docs. | Low |
| `scripts/offline_editable_install.py` | KEEP | Tracked; tested by `test_offline_editable_install.py`; README documents it. | None. | Low |
| `pyproject.toml`, `MANIFEST.in`, `requirements*.txt`, `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md` | KEEP | Packaging of the engine. Version 0.2.0 staged. | Commit pending edits. | Low |
| `intent.toml`, `justfile`, `.github/workflows/ci.yml` | KEEP AND DOCUMENT | justfile/CI are "GENERATED BY intent — DO NOT EDIT"; document the intent tool in developer docs so nobody hand-edits them. | Document. | Low |
| `config.json` | INVESTIGATE → DELETE CANDIDATE | Points at `custom_data/…` paths that don't exist; no code reads a root `config.json` (settings resolves `data/`/cwd candidates instead; `utils/config.py` is generic). Appears to be a stale example. | Confirm no external doc references, then remove or convert into a documented example. | Low |
| `dashboard.html` | RESOLVED — deleted by owner (08 Q8) | Standalone design mock; owner deleted it on 2026-07-16. | Include the deletion in the next commit. | Low |
| `documentation.md` | SPLIT / MERGE into `docs/` | 600+-line living guide overlapping README + docs; brief requires structured `docs/developer/`. | Distribute into the 09-structure docs; leave a pointer. | Low |
| `lessons.md` | MOVED ✅ (owner instruction) | Authoritative Traffic Relationships content specification. | Moved to `docs/content/traffic_relationships_spec.md` on 2026-07-16; must be read before the curriculum phase (07 Phase 5). | Low |
| `airspacesim_architecture_and_product_direction.md` (root) | MERGE / DELETE CANDIDATE | Near-duplicate of `airspacesim_fable5_brief/REFERENCE_architecture_and_product_direction.md` (differs slightly). Two copies will drift. | Keep the brief copy as canonical; drop the root copy after diff review. | Low |
| `ideas.md`, `.codex`, `.local/`, `.vscode/` | GENERATED — GITIGNORE | Already ignored personal notes/editor state. | Nothing to do. | Low |
| `airspacesim_fable5_brief/airspacesim_fable5_brief/` (nested copy) + `CLAUDE(1).md` | DELETE CANDIDATE | Byte-identical duplicate of the brief (and of root `CLAUDE.md`) from a double-unzip. | Remove nested folder + `CLAUDE(1).md`. | Low |
| Tracked-but-deleted files: `setup.py`, `sim_ui.md`, `pre-roadmap.md`, `regenerate_dist.bat`, `docs/release-checklist.md`, `airspacesim/templates/{basic_dashboard,hello_world,test}.html`, `airspacesim/templates/styles.css` | DELETE (already done, uncommitted) | Deleted in working tree; git still tracks them. | Include deletions in the baseline commit. | Low |
| Root `data/ static/ templates/ examples/ logs/`, `airspacesim-playground/`, `*.egg-info/`, `var/` | GENERATED — GITIGNORE | All already covered by `.gitignore` (verified: none tracked). | Nothing to do. | Low |

## 2.6 Tests — root `tests/`

| Path | Classification | Reason / Evidence | Proposed action | Risk |
|---|---|---|---|---|
| Engine tests (`test_aircraft*, test_conversions, test_core_domain, test_route_*, test_schemas, test_contracts_and_adapters, test_trajectory_export, test_performance_tools, test_settings`) | KEEP | Direct engine coverage; migrate import paths only if modules move. | Keep green through every phase. | Low |
| Workflow/legacy tests (`test_cli_init, test_docs_quickstart, test_phase1_clean_run, test_offline_editable_install, test_integration, test_structure_cleanup`) | KEEP (legacy contract) | Pin the `init` + file-contract + packaging behaviour. `test_integration.py` partially trivial (`say_hello`). | Retire only with the legacy surface itself. | Low |
| Browser tests (`test_browser_console_clean, test_hosted_browser_flow`) | KEEP AND DOCUMENT | Playwright smokes, env-gated in CI (`AIRSPACESIM_BROWSER_SMOKE`). | Document how to run locally. | Low |
| Hosted validation (`test_seed_hosted_demo_validation, test_validate_airspace_package`) | KEEP | Cover the new scripts; untracked — commit. | Commit. | Low |

## 2.7 Missing — CREATE

| Missing item | Why | Target |
|---|---|---|
| Core `Simulation` façade + deterministic clock + `SeparationMonitor` + engine event stream | Brief's engine contract; nothing owns sim time or separation today | `airspacesim/` (see 03) |
| Canonical fictional environment pack (replacing Gao data end-to-end) | Brief non-negotiable #4 | `airspaces/<new-fictional>/` (see 04) |
| Scenario/environment schema versioning + validator errors in plain language | Brief 03 §Validation; current validators raise contract errors but scenario templates (`demo_template`) have no schema_version discipline | `airspacesim/io` + `scripts/validate_airspace_package.py` |
| Generic `ConceptPage`/`LearnRunner`/`PracticeRunner`/`SimulationRunner` + step components | Brief content architecture | `apps/web/src` |
| Traffic Relationships curriculum content (5 lessons) + planned placeholders | Brief Phase 3 | `airspaces/` + web |
| i18n framework + `locales/en`, `locales/fr` | Brief languages; zero i18n exists | `apps/web` |
| Users table, minimal auth, progress + run-summary persistence | Brief Phase 4; only anonymous sessions exist | `apps/api` |
| PostgreSQL support + PG-verified migrations + `DATABASE_URL` docs | Brief database requirement; SQLite-only today | `apps/api` |
| Root `.env.example` (or documented pointer to per-app examples) | Brief deployment §; only `apps/api/.env.example` + web example exist | repo root |
| `docs/developer/*` and `docs/user/*` sets per brief 09 | Required documentation contract (see 06) | `docs/` |
| Docker/dev-compose (optional but referenced by target architecture) | Brief target tree lists `docker-compose.yml` | repo root (decide in 05) |
| Structured logging config for the API | Brief backend requirements | `apps/api` |
