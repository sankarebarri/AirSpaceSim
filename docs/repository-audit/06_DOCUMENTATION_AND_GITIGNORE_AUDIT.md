# 06 — Documentation and .gitignore Audit

## 1. Existing documentation inventory

### Library-era (tracked, mostly current for the legacy surface)
`docs/index.md` (good index), `architecture.md`, `data-contracts.md`, `file-contracts.md`, `ingestion.md`, `migration.md`, `tutorial.md`, `compatibility-matrix.md`, `failure-modes.md`, `glossary.md`, `interoperability-example.md`, `docs/adr/0001–0004`, `documentation.md` (root, 600+ lines "living guide"), `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.

### Hosted-era (mostly untracked)
- `docs/architecture/`: `engine_boundary.md` (**directly aligned with the brief — keep as the seed of the core API doc**), `engine_usage_quickstart.md`, `codebase_tidy_and_packaging_plan.md`, `legacy_static_ui_decision.md`.
- `docs/backend/README.md`, `docs/frontend/README.md` (+ `run_workspace_ux_spec.md`), `docs/api/README.md`, `docs/deployment/README.md` + `env/*.env.example`, `docs/migration/README.md`.
- `docs/user/`: `how_to_start_hosted_app.md`, `how_to_use_app.md`, `how_to_test.md`, `quick_test_guide.md`, `run_simulation.md` — **named "user" but written for developers** (terminal commands, seeding scripts).
- `docs/improvements/` (9 planning docs): `new-roadmap.md` (active tracker), `legacy_static_ui_roadmap.md`, `long_term_training_roadmap.md`, `post_performance_phase_plan.md`, `public_launch_hardening_plan.md`, `training_modes_lessons_design.md`, `multi_airspace_custom_airspace_design.md`, `collaboration_progress_and_deployment_design.md`, `aircraft_performance_plan.md`.

### Root-level strays
`airspacesim_architecture_and_product_direction.md` (near-duplicate of the brief's REFERENCE copy), `ideas.md` (ignored notes), `airspacesim_fable5_brief/` containing a byte-identical nested copy of itself and `CLAUDE(1).md` (identical to root `CLAUDE.md`). Resolved 2026-07-16: root `lessons.md` moved to `docs/content/traffic_relationships_spec.md` and designated an **authoritative content specification** for the curriculum phase (08 §Additional authoritative content source); root `dashboard.html` deleted by the owner.

## 2. Duplicates and contradictions

| Issue | Files | Recommendation |
|---|---|---|
| Two migration docs | `docs/migration.md` (data contracts) vs `docs/migration/README.md` (app architecture) | RENAME one (e.g. `docs/migration.md` → `docs/contract-migration.md`) or merge; update index. |
| Four+ overlapping roadmaps/plans | `new-roadmap.md`, `legacy_static_ui_roadmap.md`, `long_term_training_roadmap.md`, `post_performance_phase_plan.md`, `public_launch_hardening_plan.md` | Keep `new-roadmap.md` as the single tracker (README already says so); mark others `ARCHIVED —` header or move to `docs/improvements/archive/`. The brief + this audit supersede much of their content. |
| Brief duplicated 3× | root `airspacesim_architecture_and_product_direction.md`, `airspacesim_fable5_brief/REFERENCE_…`, nested `airspacesim_fable5_brief/airspacesim_fable5_brief/` | One canonical copy in the brief folder; delete the nested copy and `CLAUDE(1).md` (unapproved delete candidates). |
| `documentation.md` vs README vs docs/ | Setup/architecture repeated in three places with different ages | Distribute into `docs/developer/*`; keep `documentation.md` as a short pointer or retire it (approval needed). |
| "User" docs that are developer docs | `docs/user/*` | Move to `docs/developer/` equivalents; write real end-user guides per brief 09. |
| Stale statements | `README.md` still describes file-based UI as the primary path and labels hosted split as "being migrated"; `docs/index.md` lacks the audit/new docs | Refresh in the docs phase. |

## 3. Missing required documents (brief 09)

Developer set (`docs/developer/`): `GETTING_STARTED.md`, `LOCAL_DEVELOPMENT.md`, `TESTING.md` (with the manual browser checklist), `AUTHENTICATION.md`, `DATABASE.md`, `DEPLOYMENT.md`, `TROUBLESHOOTING.md`, `ARCHITECTURE.md`, `CONTENT_AUTHORING.md`, `COMMAND_REFERENCE.md`.
Much raw material exists (`how_to_start_hosted_app.md` → GETTING_STARTED; `how_to_test.md` → TESTING; `engine_boundary.md` → ARCHITECTURE; `docs/deployment/README.md` → DEPLOYMENT) — this is largely a **reorganise-and-complete** job, not greenfield writing.

User set (`docs/user/`): `USER_GUIDE.md`, `LEARN_GUIDE.md`, `PRACTICE_GUIDE.md`, `SIMULATE_GUIDE.md`, `ACCOUNT_AND_PROGRESS.md`, `FAQ.md` — all missing in the brief's sense (plain-language, non-technical). Blocked partly on i18n/auth decisions but drafts can start once the fictional environment lands.

## 4. Proposed documentation structure

```text
README.md                      # concise, navigational (trim current)
docs/
├── index.md                   # updated master index
├── developer/                 # brief 09 §1 set (10 files above)
├── user/                      # real end-user guides (6 files above)
├── architecture/              # engine_boundary, ADRs (move docs/adr/ here or keep)
├── contracts/                 # data-contracts, file-contracts, compatibility, schemas
├── content/                   # authoritative content specs (traffic_relationships_spec.md)
├── deployment/                # existing + env examples
├── repository-audit/          # this audit
└── improvements/archive/      # superseded roadmaps/plans
```

Maintenance rule (adopt verbatim from brief): docs update in the same change as any command/port/env/schema/flow change; a feature is incomplete without its documentation.

## 5. .gitignore audit

Current `.gitignore` is already strong. Verified: no tracked egg-info, logs, DBs, env files, `node_modules`, playground, or editor state; `!.env.example` / `!.env.*.example` negations work; `var/`, `*.db`, playwright/test-results covered; root-only ignores for `/data/`, `/static/`, `/templates/`, `/logs/`, `/examples/` correctly scope init artefacts without hiding `airspacesim/data/` etc.

### Exact recommended additions

```gitignore
# Frontend test/build extras (future-proof; some already covered)
apps/web/coverage/

# Alembic ephemeral
apps/api/var/

# OS/editor (already present — no change)
```

Notes rather than additions:
- `apps/web/dist/` and `.vite/` already covered.
- `apps/api/var/` is already matched by the unanchored `var/` rule — the explicit line above is optional clarity, not a behaviour change.
- `.claude/` is ignored; `CLAUDE.md` (tracked intent) is correctly not ignored.

### Recommended removals / corrections

```gitignore
# Remove (typo rule, harmless but dead):
airspacesim-palyground/

# Reconsider: `how_to` and `todo` are bare names that would silently ignore
# any future file/dir with those names anywhere in the tree. If the private
# notes are gone, remove both lines; otherwise anchor them: /how_to, /todo
```

- Keep ignoring `ideas.md` only while it remains personal notes; if it holds product decisions worth keeping, move content into `docs/improvements/` and stop ignoring.
- Do **not** ignore: `airspaces/` packs, lesson/scenario JSON, `apps/api/app/db/migrations/`, `apps/web/package-lock.json`, `.env.example` variants, `docs/` — all currently correctly tracked-or-trackable.

### Hygiene actions needed (not .gitignore changes)
1. Commit the pending deletions (`setup.py`, `sim_ui.md`, `pre-roadmap.md`, `regenerate_dist.bat`, `docs/release-checklist.md`, legacy templates) — they are deleted on disk but still tracked.
2. Commit the untracked application/content/docs trees (the audit's Phase 0).
3. `airspacesim.egg-info/` + `AirSpaceSim.egg-info/` on disk are stale build artefacts (ignored); safe to clean locally at any time — they are not in git.
