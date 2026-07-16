# 01 — Current State

Audit date: 2026-07-16. Audited against the implementation brief in `airspacesim_fable5_brief/` and root `CLAUDE.md`. No code was modified during this audit.

> **Addendum (same day):** this document is a point-in-time snapshot of the *pre-baseline* state. Phase 0 has since been completed by the owner (baseline commit `bf2af1b` pushed — `apps/`, `airspaces/`, scripts, and docs are now tracked), the owner deleted `dashboard.html`, root `lessons.md` was moved to `docs/content/traffic_relationships_spec.md`, and all open questions were decided — see `08_OPEN_QUESTIONS.md` for the decision record and `07_PHASED_REFACTOR_PLAN.md` for updated scope. "UNTRACKED" annotations below describe the audited state, not the current one.

## 1. What the repository actually is

The brief describes a target (React + FastAPI + PostgreSQL platform over a reusable engine). The repository is **already most of the way to that shape structurally**, but in mid-migration and largely uncommitted:

- `airspacesim/` — a published PyPI package (v0.1.3 released, v0.2.0 staged in `pyproject.toml`/`CHANGELOG.md`) containing the simulation engine **plus** a legacy static HTML/JS map UI, a file-based dev server, and CLI bootstrap.
- `apps/api/` — a FastAPI service (SQLAlchemy + Alembic, SQLite by default) that runs simulations **server-side, in memory**, using the engine package, with runs/scenarios/commands/checkpoints persistence and a WebSocket stream. *Entirely untracked in git.*
- `apps/web/` — a React 18 + Vite + react-leaflet frontend with Learn / Practice / Simulate flows. *Entirely untracked in git.*
- `airspaces/` — two JSON "airspace packages" (`training_alpha`, `gao_demo`) containing airspace, scenarios, and lesson definitions. *Entirely untracked in git.*
- Legacy compatibility surfaces: root `data/`, `static/`, `templates/`, `examples/`, `dev_server.py`, `airspacesim-playground/` (all produced by `airspacesim init` and gitignored except `dev_server.py`).
- Two generations of documentation (library-era and hosted-era) coexisting under `docs/` plus several planning/prompt files at the root.

**Git state is a major finding in itself**: only 131 files are tracked. The whole hosted application, the airspace packages, most new docs, and `CLAUDE.md` are untracked; ~35 tracked files have uncommitted modifications; 10 tracked files are deleted on disk but not committed (`setup.py`, `sim_ui.md`, `pre-roadmap.md`, `regenerate_dist.bat`, `docs/release-checklist.md`, four legacy templates). Nothing can be safely refactored until this state is committed.

## 2. Repository tree (condensed, generated/ignored items marked)

```text
AirSpaceSim/
├── airspacesim/                  # Python engine package (tracked, published to PyPI)
│   ├── core/                     # typed models, Protocol interfaces, ManagerStepper
│   ├── simulation/               # aircraft physics, manager, events, scenario runner,
│   │                             #   performance database, interpolation
│   ├── io/                       # contract validation, adapters, exporters,
│   │                             #   airspace-package normalisation
│   ├── routes/                   # RouteManager, processor, registry (+ legacy shim)
│   ├── utils/                    # conversions, bearing, logging
│   ├── cli/                      # `airspacesim init`, `list-routes`
│   ├── data/                     # seed JSON contracts (contains Gao-derived data)
│   ├── schemas/                  # JSON Schemas for scenario/trajectory v0.1
│   ├── static/, templates/       # legacy Leaflet UI shipped inside the package
│   ├── examples/                 # stress/benchmark/example scripts
│   ├── map/                      # Leaflet map-config builders (renderer, markers)
│   ├── dev_server.py             # file-serving dev server w/ POST /api/events
│   ├── settings.py               # global mutable Settings singleton (cwd-aware paths)
│   └── api/ config/ web/ tests/  # empty or near-empty placeholder subpackages
├── apps/
│   ├── api/                      # FastAPI app (UNTRACKED)
│   │   ├── app/{api/v1/routes, db/{models,repositories,migrations}, services,
│   │   │        sessions, schemas, ws}
│   │   ├── tests/ (11 files)     # httpx-based API tests incl. migrations
│   │   ├── alembic.ini, pyproject.toml, .env.example
│   │   └── var/airspacesim-api.db      # local SQLite (ignored)
│   └── web/                      # React app (UNTRACKED)
│       ├── src/{app, pages, components, lib, types, styles}
│       └── tests/ (8 vitest files)
├── airspaces/                    # airspace packages (UNTRACKED)
│   ├── training_alpha/           # fictional pack: airspace, 4 scenarios, 7 lesson JSONs
│   └── gao_demo/                 # "Sahel Control": renamed but Gao-derived data
├── scripts/                      # start_hosted_dev, seed_hosted_demo, smoke_hosted_app,
│                                 #   validate_airspace_package (all UNTRACKED except
│                                 #   offline_editable_install.py)
├── tests/                        # 94 collected root tests (engine + hosted smoke)
├── docs/                         # two generations of docs; new subdirs UNTRACKED
├── airspacesim_fable5_brief/     # the implementation brief (+ duplicate nested copy)
├── data/ static/ templates/ examples/ logs/  # `airspacesim init` artefacts (ignored)
├── airspacesim-playground/       # legacy workspace w/ committed-era logs (ignored)
├── var/, *.egg-info/, .venv/     # generated (ignored)
├── dev_server.py                 # thin wrapper → airspacesim.dev_server
├── dashboard.html                # standalone UI design mock (UNTRACKED)
├── documentation.md              # large "living guide"
├── lessons.md                    # Traffic Relationships prompt draft (UNTRACKED)
├── ideas.md, intent.toml, config.json, justfile, CI, packaging files
└── README.md, CHANGELOG.md, CONTRIBUTING.md, LICENSE, CLAUDE.md
```

## 3. Current runtime flow (hosted app)

1. `scripts/start_hosted_dev.py` starts `uvicorn app.main:app` (from `apps/api`) and `npm run dev` (from `apps/web`); `--seed` creates a demo run from `airspaces/gao_demo`.
2. The web app generates an **anonymous session id** client-side (`apps/web/src/lib/session.ts`) and sends it as `X-Airspacesim-Session`; the API scopes scenarios/runs to it (`apps/api/app/session_identity.py`). There is no authentication.
3. Creating a Practice run (`POST /api/v1/runs/practice`) loads an airspace package manifest, resolves a lesson → scenario template, normalises the airspace payload through `airspacesim.io.normalize_scenario_airspace_payload`, persists a `ScenarioRecord` + `RunRecord`, and builds an in-memory `SimulationRuntimeSession` (`apps/api/app/sessions/runtime.py`).
4. The runtime session drives the engine in `batched` mode on a background thread (0.25 s ticks × `sim_rate`), **monkeypatches `manager.save_aircraft_data` to a no-op** to suppress the engine's file writes, publishes state snapshots to the WebSocket hub, and persists periodic checkpoints.
5. Commands (`ADD_AIRCRAFT`, `SET_FL`, `ASSIGN_HEADING`, `DIRECT_TO`, `HOLD_AT_FIX`, … 13 types in `airspacesim/simulation/events.py`) go through `POST /runs/{id}/commands` → `apply_events_idempotent` on the live manager.
6. The frontend renders state on a Leaflet map (`TrafficMap.tsx`) and computes **all separation monitoring, Practice evaluation, and Simulate loss-of-separation counting in TypeScript** (`lib/conflict.ts`, `lib/practiceOutcome.ts`, `lib/simulateSummary.ts`).

The legacy package flow (`airspacesim init` → `example_simulation.py` → JSON files → static `map.html` + `dev_server.py`) still exists in parallel and is exercised by root tests.

## 4. Learn / Practice / Simulate today

- **Learn**: hardcoded catalogue in `LearnPage.tsx` (one concept: Crossing Traffic). `CrossingTrafficLearnPage.tsx` (459 lines) is a bespoke 5-stage guided page with hardcoded callsigns (`AFR612`, `RAM401`), target FL310, stage copy, and visible-route filter. It **does** drive the real engine via a backend run. `HeadingVersusRadialLessonPage.tsx` similarly hardcodes its lesson steps. Lesson JSON files in `airspaces/training_alpha/lessons/` exist but are only used server-side to resolve `lesson_id → scenario_id`; their teaching content is duplicated (and diverged) in React.
- **Practice**: scenario-metadata-driven (`metadata_payload.practice` carries conflict pair, crossing point, minima, allowed commands, next-step link). Evaluated client-side by `usePracticeOutcome`. Uses the same engine runs.
- **Simulate**: hardcoded registry (`simulateScenarios.ts`, one Gao scenario). General pairwise LoS monitoring client-side (`useSimulateSummary`) — correctly counts one event per continuous violation per pair, per the brief's semantics, but in the wrong layer and not persisted.

**All three modes use the same engine** (via backend runs) for movement — the non-negotiable is satisfied for physics. Separation/evaluation logic, however, lives outside the engine entirely.

## 5. Strengths worth preserving

- Real, working engine physics with performance-profile-driven behaviour (turn rates, climb/descent, speed guardrails, holds, radial intercepts) and 94 passing-in-CI root tests plus API and web test suites.
- Server-authoritative simulation runtime already exists — the hard part of the brief's "extract engine from UI" is materially done; movement logic is not in React.
- Versioned data contracts with validators (`io/contracts.py`), JSON Schemas, and an airspace-package manifest format with discovery, path-escape protection, and a validation script.
- Alembic migrations (including one applied schema evolution) and migration tests.
- Deterministic scenario definitions as data (JSON templates, no randomness).
- Practice metadata format already matches the brief's direction (conflict pair, crossing point, minima as scenario data, not code).
- CI covering 3 Python versions, API tests, web tests, a Playwright browser smoke, and ruff.
- A thoughtful `.gitignore` and clean secret handling (only localhost defaults on disk).

## 6. Technical debt (ranked)

1. **Uncommitted migration**: the entire hosted app, content packs, and new docs exist only in the working tree.
2. **Engine impurities**: wall-clock time and threads inside `AircraftManager`; JSON file writes inside the step path (hosted app must monkeypatch them away); global mutable `settings` singleton with cwd-dependent path resolution and a Gao-coordinate `AIRSPACE_CENTER` default used by `classify_traffic_flow_from_waypoints`; no first-class `Simulation`/clock abstraction; no separation monitor anywhere in the engine.
3. **Separation & evaluation in the frontend**: `conflict.ts` / `practiceOutcome.ts` / `simulateSummary.ts` implement engine-domain logic in TypeScript; summaries are computed and displayed client-side and never persisted.
4. **Bespoke lesson pages**: one React page per lesson, hardcoded copy/callsigns, duplicating lesson JSON content that already exists as data.
5. **Gao-derived public data**: `airspaces/gao_demo` ("Sahel Control") and `airspacesim/data/*.json` retain real-looking fixes (ETRUL, PILTI, TESTI, OPUGO, …), real airway identifiers (UA612, UG859, UR971, UM629, UA603, UT365, UR981), `GAO_VOR` ids, and Gao coordinates (16.25, −0.03) — also baked into `settings.AIRSPACE_CENTER`, package map defaults, and the web app (`simulateScenarios.ts`).
6. **No i18n at all**: every user-facing string is hardcoded English in React components.
7. **No authentication and no PostgreSQL**: anonymous session header only; SQLite everywhere including the "production" env example.
8. **Package/app entanglement**: static UI, dev server, map-config builders, and CLI-init assets ship inside the PyPI engine package.
9. **Doc sprawl**: two doc generations, ≥4 overlapping roadmaps/plans, duplicated brief copies, prompt files at the root.
10. **Monolith components**: `RunDetailPage.tsx` (1,869 lines), `TrafficMap.tsx` (897 lines).

## 7. Major risks

- **Refactoring on an uncommitted tree** — any engine change now is unreviewable and unrevertable. Commit first.
- **PyPI compatibility**: the package is published; moving modules or removing the static UI breaks 0.1.x users unless staged behind deprecations or a 0.2/1.0 boundary decision.
- **Determinism**: the runtime thread steps with wall-clock sleep and per-tick `sim_rate` multiplication; replays and research use will not be reproducible until a stepped, seedable clock owns time.
- **Separation-monitor migration**: moving LoS logic server-side changes Practice/Simulate UX timing; the client currently freezes outcomes based on polling cadence.
- **Alembic baseline is SQLite-flavoured** (`20260511_0001_initial_sqlite_baseline.py`); PostgreSQL compatibility is untested.
- **Gao data removal** touches package defaults, tests, seeds, scripts, and the web registry simultaneously; doing it piecemeal will break the demo flows the tests rely on.
