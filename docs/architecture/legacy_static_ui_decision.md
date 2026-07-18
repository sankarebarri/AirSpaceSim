# Legacy Static UI Decision

Status: retained as compatibility surface

Date: 2026-06-09

## Decision

The hosted React application in `apps/web/` is the primary user interface for new product work.

The older static UI remains in the repository only for compatibility with the library/offline workflow:

- `airspacesim/templates/`
- `airspacesim/static/`
- `airspacesim/map/`
- `airspacesim/dev_server.py`
- root `dev_server.py` compatibility entrypoint

`airspacesim-playground/` is a legacy reference workspace. It is not the long-term hosted app and should not receive new product UI features.

## Current Ownership

### Hosted App

Owned by:

- `apps/api/`
- `apps/web/`
- `airspaces/`

Use this path for:

- landing page
- lessons
- live simulation workspace
- airspace package listing
- practice-run launcher
- hosted deployment

### Engine And Library Compatibility

Owned by:

- `airspacesim/`

Use this path for:

- reusable simulation engine
- file contracts
- adapters and exporters
- `airspacesim init` compatibility assets
- static map compatibility while the offline workflow still exists

### Legacy Reference Only

Owned by:

- `airspacesim-playground/`

Use this path only for:

- comparing old behavior during migration
- validating path compatibility issues
- temporary regression reference

Do not add new training features, hosted UI work, or product UX there.

## Package Asset Decision

Keep these package assets for now:

- `airspacesim/templates/map.html`
- `airspacesim/static/js/*.js`
- `airspacesim/static/css/*.css`
- `airspacesim/static/icons/*.svg`
- `airspacesim/dev_server.py`
- root `dev_server.py`

Reason: they support the static/offline compatibility workflow and are still referenced by package docs and tests.

Removed as unused cleanup candidates:

- `airspacesim/templates/basic_dashboard.html`
- `airspacesim/templates/hello_world.html`
- `airspacesim/templates/test.html`
- `airspacesim/templates/styles.css`

Reason: they were not part of the hosted React app, not referenced by `airspacesim init`, and only appeared in cleanup tracking docs.

## Retirement Criteria

Do not remove the legacy static UI until all of these are true:

1. Hosted React app covers normal simulation usage.
2. `airspacesim init` has a clear replacement or documented static compatibility path.
3. Package tests no longer require old template/static files beyond the agreed bootstrap set.
4. User docs point new users to `scripts/start_hosted_dev.py` and hosted app routes first.
5. Any remaining offline/static workflow has its own explicit docs.

## Rules Going Forward

- New UI work goes in `apps/web/src/`.
- New API work goes in `apps/api/app/`.
- New airspace/scenario/lesson content goes in `airspaces/`.
- No new hosted-product features should be added to `airspacesim/templates/`, `airspacesim/static/`, or `airspacesim-playground/`.
- Root `dev_server.py` remains a compatibility entrypoint only.


---

## Decision executed (2026-07-18, Phase 8)

Per decision Q2 (`docs/repository-audit/08_OPEN_QUESTIONS.md`), the legacy
static Leaflet UI, file-based dev server, generated workspace flow, and
related wheel assets were removed in 0.2.0 — no compatibility package, no
permanent shims. The final state is preserved at the git tag
`pre-legacy-ui-removal`. `airspacesim init` now scaffolds airspace packages
instead of static-UI workspaces.
