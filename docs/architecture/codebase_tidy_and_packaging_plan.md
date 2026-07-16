# Codebase Tidy And Packaging Plan

This plan is for making AirSpaceSim easier to host as an app and easier to reuse as a simulation engine in other projects.

## Main Goal

Keep the reusable Python simulation engine independent from the hosted product.

The project should have clear ownership boundaries:

- `airspacesim/`: reusable simulation engine and file contracts
- `apps/api/`: hosted backend API that uses the engine
- `apps/web/`: hosted frontend app
- `airspaces/`: airspace packages and scenario templates
- `docs/`: architecture, user guides, and improvement plans
- `scripts/`: developer/demo automation

## Current Shape

Good existing separation:

- The engine is already mostly under `airspacesim/`.
- The hosted API is already under `apps/api/`.
- The web app is already under `apps/web/`.
- Custom airspaces are already under `airspaces/`.
- API and web dependencies are already separate.

Main cleanup risks:

- Root-level docs are scattered.
- Root `/templates/` is ignored as generated output, but now contains source-like lesson/scenario files.
- The engine still contains older browser/demo assets under `airspacesim/templates`, `airspacesim/static`, `airspacesim/map`, and `airspacesim/dev_server.py`.
- Some generated/local directories exist in the workspace, such as `dist`, `build`, `*.egg-info`, `__pycache__`, `.pytest_cache`, `apps/web/dist`, and runtime DB files.
- The seed script has grown into both a developer tool and scenario launcher logic.

## Target Structure

```text
airspacesim/
  core/
  io/
  routes/
  simulation/
  utils/
  data/
  schemas/

apps/
  api/
  web/

airspaces/
  gao_demo/
  training_alpha/

docs/
  architecture/
  frontend/
  backend/
  deployment/
  improvements/
  user/

scripts/
  seed_hosted_demo.py
  validate_airspace_package.py
```

## Source Vs Generated Files

Source files should stay in version control:

- engine code
- API code
- web source code
- airspace packages
- scenario templates
- lesson templates
- docs
- tests

Generated/local files should stay ignored:

- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.venv/`
- `dist/`
- `build/`
- `*.egg-info/`
- `apps/web/dist/`
- `apps/web/node_modules/`
- `apps/api/var/*.db`
- root generated `data/`, `static/`, `templates/`, `logs/`, `examples/`

## Important Decision: Templates

Root `/templates/` is currently treated as generated local output by `.gitignore`.

That means source lesson/scenario files should not live there long term.

Recommended destination:

- Move reusable lesson templates to `airspaces/<airspace_id>/lessons/` when tied to an airspace.
- Move global lesson templates to `docs/lesson_templates/` or `content/lessons/` if they are not tied to one airspace.
- Keep scenario templates inside each airspace package, for example:

```text
airspaces/training_alpha/
  airspace.v1.json
  scenarios/
    beginner_mix.v1.json
  lessons/
    heading_vs_radial.v1.json
```

Recommended immediate action:

- [x] Move `airspaces/training_alpha/lessons/heading_vs_radial.v1.json` into an airspace-owned lesson folder.
- [x] Move `airspaces/gao_demo/scenarios/mixed_traffic_demo.v1.json` into `airspaces/gao_demo/scenarios/`.
- Keep root `/templates/` ignored because it is also used by legacy generated local app output.

## Engine Boundary

The reusable engine should not depend on the hosted app.

Allowed inside `airspacesim/`:

- aircraft movement
- route/radial/heading/direct-to/hold logic
- performance database lookup
- scenario loading
- event application
- file contracts
- trajectory export

Avoid inside `airspacesim/`:

- FastAPI app code
- React/web app assumptions
- hosted run/session storage
- database models
- deployment settings
- homepage/lesson UI behavior

## Hosted API Boundary

The API should be a thin hosted layer around the engine.

Allowed inside `apps/api/`:

- HTTP routes
- websocket broadcasting
- run/session registry
- database persistence
- API schemas
- auth/roles later
- practice-run launch endpoints later

Avoid inside `apps/api/`:

- core aircraft movement logic
- route interception math
- aircraft performance calculations
- frontend-specific display logic

## Web App Boundary

The web app should own UI and lesson presentation.

Allowed inside `apps/web/`:

- landing page
- lessons
- run workspace
- maps and panels
- command forms
- frontend-only lesson animations

Avoid inside `apps/web/`:

- authoritative simulator physics
- backend validation decisions
- persistent run truth

Frontend-only lesson demos are allowed because they are teaching visuals, not authoritative simulation runs.

## Cleanup Phases

### Phase 1: File Ownership

- [x] Move source templates out of root `/templates/`.
- [x] Move user docs into `docs/user/`.
- [x] Move roadmap/planning docs into `docs/improvements/`.
- [x] Keep only essential project files in repo root.
- [x] Update README links after moves.
- [x] Update startup docs after moves.

### Phase 2: Engine Packaging

- [x] Review what package data should ship with `airspacesim`.
- [x] Decide whether legacy `airspacesim/templates` and `airspacesim/static` still belong in the engine package.
  - Current decision: retain them as legacy compatibility assets for `airspacesim init`; do not move them until that workflow is replaced or retired.
- [x] Keep core engine installable without the hosted API and web app.
- [x] Add a small import test that proves `airspacesim` imports without API/web dependencies.
- [x] Add a documented public engine API for external projects.

### Phase 3: Hosted App Packaging

- [x] Add deployment docs for API.
- [x] Add deployment docs for web.
- [x] Add environment variable reference.
- [x] Add local, staging, and production environment examples.
- [x] Add production build/start commands.
- [x] Add migration command to production startup docs.
- [x] Add hosted deployment smoke test script.
- [x] Decide whether API serves web static files or web is hosted separately.
  - Current decision: host API and web separately; deploy `apps/web/dist/` as static files.
- [x] Add one command or script for local hosted dev startup later.
  - `scripts/start_hosted_dev.py` starts API and web together, with optional demo seeding.

### Phase 4: Scenario And Airspace Packages

- [ ] Standardize airspace package structure.
- [x] Add `validate_airspace_package.py`.
- [x] Add package metadata fields for service type, difficulty, and training mode.
- [x] Add lesson references inside packages.
- [x] Make frontend list available packages from API later.

### Phase 5: Script Cleanup

- [ ] Keep `scripts/seed_hosted_demo.py` as a developer tool.
- [ ] Extract shared scenario-loading logic into reusable engine/API helpers if needed.
- [x] Add a frontend/API practice-run launcher later so end users do not need scripts.

## Recommended Next Action

Start with Phase 1.

Reason:

It is low risk and removes confusion before bigger code moves. It also protects source templates from being hidden by `.gitignore`.
