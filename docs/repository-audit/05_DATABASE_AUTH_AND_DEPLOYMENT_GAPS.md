# 05 — Database, Auth, and Deployment Gaps

## 1. Current state

### Database
- SQLAlchemy 2.0 + Alembic in `apps/api/app/db/`; SQLite everywhere (`sqlite:///./var/airspacesim-api.db` default; even `docs/deployment/env/api.production.env.example` uses SQLite at `/srv/airspacesim/`).
- Tables: `scenarios` (payload JSON columns), `runs`, `run_commands`, `run_checkpoints` — all scoped by `session_id` string (migration `20260708_0003`).
- Migrations: 3 revisions, with tests (`apps/api/tests/test_migrations.py`). Baseline is explicitly named `initial_sqlite_baseline`; PostgreSQL compatibility unverified (JSON type, server defaults, index names).
- `auto_create_schema=true` by default (dev convenience); production example correctly sets it false — matches the brief's "don't rely on create_all in production".
- Checkpoints store periodic full snapshots (capped at 25/run) — reasonable; **not** per-frame storage, compliant with the brief.

### Authentication
- None. `session_identity.py` documents the model: client-generated UUID header `X-Airspacesim-Session` (or `sid` query param for WS/CSV), validated by regex only. Anyone who guesses/steals an id reads those runs — acceptable for local dev, not for hosting.
- No users table, no login UI (the "Sign in" button in `LearnPage.tsx` does nothing), no token/session handling, no protected routes beyond session scoping. No auth experiments to clean up — greenfield.
- Guest access: effectively total, which satisfies the brief's guest requirements by default.

### Persistence gaps vs the brief's model
- No `users`, `concepts`, `environments`/`environment_versions`, `scenario_versions`, `learning_progress`, `simulation_runs.summary_json`, `run_events`.
- Learn progress lives in browser localStorage (`learnProgress.ts`) — correct for guests, no server counterpart.
- Run summaries (Practice outcome, Simulate summary) computed client-side, displayed once, never stored.
- Scenario records are created per practice-run (a new ScenarioRecord each time) — no versioning/dedup; environment (airspace pack) content is copied into the scenario payload with no version stamp.

### Deployment
- Health endpoint: ✅ `GET /health` with DB probe.
- CORS: ✅ configurable; production guard refuses `*`.
- Env config: ✅ pydantic-settings with `AIRSPACESIM_API_` prefix + `.env.example`; web uses `VITE_API_BASE_URL` with a localhost fallback.
- Rate limiting and body-size middleware exist.
- Missing: Docker/compose; production process docs for uvicorn workers; structured logging (no logging config in `apps/api` at all); SPA fallback story for the built frontend (vite dev server only; no serve config or docs for refresh-on-route); root `.env.example`; secret-key convention (nothing needs one yet — no sessions/tokens); frontend production build pipeline beyond `npm run build` in CI.
- No committed secrets found (checked env files; only localhost defaults). `.gitignore` covers env/DB artefacts correctly.

## 2. Proposed PostgreSQL structure

Keep existing tables; add the brief's persistence model incrementally:

```text
users                 id, email (unique), display_name?, preferred_language, created_at, updated_at
concepts              id, slug, service, family, difficulty, status, metadata_json
environments          id, slug, name, environment_type, current_version_id
environment_versions  id, environment_id, version, definition_json, created_at
scenarios             (existing) + concept_id?, owner_user_id?, is_public, current_version_id
scenario_versions     id, scenario_id, version, definition_json, created_at
learning_progress     id, user_id, concept_id, stage_key, status, updated_at
runs                  (existing) + user_id?, scenario_version_id?, environment_version_id?, summary_json?
run_events            id, run_id, event_type, payload_json, occurred_at   -- meaningful events only
```

Steps:
1. Verify the existing 3 migrations against PostgreSQL (spin up PG in CI; fix JSON/JSONB and server-default dialect issues; consider a consolidated baseline since the app is unreleased — open question 08-Q5).
2. Move file-based airspace packages toward `environments`/`environment_versions` **only when needed** (packages-on-disk are fine for built-in content; DB versions matter for user-created scenarios and run reproducibility).
3. `run_events` receives engine events (separation_loss_started/ended, aircraft_entered/exited, command_applied) once the core monitor exists (03 E4/E5).

## 3. Authentication plan (minimal, per brief)

1. Add `users` + a single auth mechanism (recommend cookie session or short-lived JWT — decide once; no orgs/roles/billing).
2. Sign in / sign out / current-user endpoints; optional display name; preferred language.
3. Keep the anonymous session id as the guest identity; on sign-in, associate/migrate the session's runs & progress to the user (cheap because everything is already `session_id`-scoped).
4. Protected persistence routes: writes to progress/saved scenarios require auth; run creation stays guest-allowed (brief: guests run solo Simulate/Practice).
5. Document local test accounts per brief 09 §7 (seed-based, no hardcoded reusable passwords).

## 4. Hosting blockers (ordered)

1. Entire hosted app is uncommitted (blocker for everything).
2. No PostgreSQL support/verification; production example points at SQLite.
3. No auth → any hosted deployment exposes all runs to session-id guessing; rate limits are the only abuse control.
4. Gao-derived public content (policy blocker for a public site, per brief).
5. No SPA fallback/serving story for the production frontend build.
6. No structured logging → undebuggable in production.
7. No deployment automation (Docker or platform config) and no documented migration-run step for deploys.

## 5. Environment-variable requirements (target)

API (existing prefix `AIRSPACESIM_API_`): `ENVIRONMENT`, `DATABASE_URL` (PostgreSQL in prod), `CORS_ALLOWED_ORIGINS`, `DEBUG`, `LOG_LEVEL` (new), `SECRET_KEY` (new, with auth), `AUTO_CREATE_SCHEMA=false` in prod, rate/limit knobs (existing).
Web: `VITE_API_BASE_URL` (required for prod build; fail the build or warn loudly when unset rather than silently defaulting to 127.0.0.1).
Root: add `.env.example` or a documented pointer to `apps/api/.env.example` + `apps/web/.env.local.example` + `docs/deployment/env/*` (which already exist and are a good start — extend rather than replace).
