# 08 — Open Questions → Decisions

All ten questions were answered by the project owner on 2026-07-16. This document is now the **decision record** for the refactor. Documents 03–07 have been updated to match; where any older wording conflicts, this document wins.

**Q1 — PyPI compatibility posture. DECIDED: breaking changes allowed in 0.2.0.**
The owner is the only known user of the package and application. No prolonged deprecation cycles for artefacts only the owner uses. Approved removals: `hello.py` + its export, `routes/route_manager.py` shim, `gao_*` settings and CLI fallbacks, empty placeholder subpackages (`airspacesim/{api,web,tests}`), obsolete seed aliases (e.g. `new_aircraft.json`) and their tests. All removals must be documented in `CHANGELOG.md` and migration documentation. Genuinely useful engine APIs are preserved.

**Q2 — Legacy static UI and `airspacesim init`. DECIDED: schedule retirement.**
The static Leaflet UI, file-based dev server, generated workspace, and related wheel assets will be retired from the core package. Their final state is preserved via git history / a release tag — **not** via permanent compatibility code, and **no** separate compatibility package unless a concrete need is discovered. `airspacesim init` may later be repurposed into an environment/scenario scaffolding command; the current static-UI workflow is not preserved for its own sake.

**Q3 — `gao_demo`. DECIDED: full replacement and deletion.**
Create a completely new fictional FIR/environment; delete `airspaces/gao_demo` once all references are migrated. No compatibility with current slugs, seeds, routes, or links. No Gao names, fixes, VOR identifiers, airway identifiers, frequencies, or exact geometry. Use **neutral fictional coordinates** (similar geographic scale acceptable; must not reconstruct the Gao operational environment). Scenarios, seeds, frontend links, tests, documentation, and defaults update in the same migration.

**Q4 — Pack format. DECIDED: JSON stays canonical.**
Evolve the existing JSON manifests, validators, schemas, API pipeline, and tests. The brief's YAML examples were illustrative. A future user-friendly template may *generate* canonical JSON.

**Q5 — Alembic history. DECIDED: squash.**
Squash the three SQLite-oriented migrations into one clean, PostgreSQL-verified initial baseline that: creates the intended first production schema, upgrades from an empty PostgreSQL database, is covered by migration tests, and becomes the preserved starting point for all future history.

**Q6 — Hosting. DECIDED: static frontend + PaaS API + managed PostgreSQL.**
Also provide Dockerfiles and a local docker-compose setup for portability. Do not optimise for unmanaged single-server self-hosting. Keep provider-specific configuration limited and documented so the app can move between PaaS providers.

**Q7 — Authentication. DECIDED: email + password with secure server-side sessions.**
Required: registration, sign in, sign out, current user, secure password hashing, HTTP-only secure cookies, protected persistence routes, development-only test-account seed/setup, preferred language on the user profile. Guest access remains fully useful (guest → value → optional account). Google OAuth is not mandatory; may be added later as an optional provider.

**Q8 — `dashboard.html`. RESOLVED: deleted by the owner** (working-tree deletion pending in the next commit).

**Q9 — French content. DECIDED: implementer drafts FR translations.**
The owner reviews and validates aviation and lesson terminology. Ordinary navigation/account/button/product translations drafted normally. Operational simulation commands remain English-only.

**Q10 — Guest summaries. DECIDED: local-first with server retention.**
Guest progress and recent summary history stay in browser session/local storage. Anonymous server-side runs get automatic **configurable retention, default 14 days for completed runs**. Authenticated users get persistent run history. No permanent cross-device history for anonymous users.

## Additional authoritative content source

`docs/content/traffic_relationships_spec.md` (moved from root `lessons.md` per owner instruction) is an **authoritative content specification** for the curriculum/content phase, alongside the brief. Where it provides more detailed Traffic Relationships instructions, follow it — unless it conflicts with `CLAUDE.md` or the architectural non-negotiables, which take precedence. It must be read before implementing Phase 5.

## Phase 0 status

Completed by the owner: baseline commit `bf2af1b` pushed to GitHub; `apps/`, `airspaces/`, scripts, and new docs are now tracked. Outstanding working-tree items for the next commit: `dashboard.html` deletion, the `lessons.md` → `docs/content/traffic_relationships_spec.md` move, and these audit-document updates.
