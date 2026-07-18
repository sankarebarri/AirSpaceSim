# Database (Developer Guide)

## Engines

- **Local development**: SQLite (`sqlite:///./var/airspacesim-api.db`,
  created automatically) — zero setup.
- **Hosted/production**: **PostgreSQL** via
  `AIRSPACESIM_API_DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/airspacesim`
  and `pip install -e ./apps/api[postgres]`.

## Migrations (Alembic)

History starts from a single squashed, PostgreSQL-verified baseline
(`20260718_0001_initial_baseline`, decision Q5). Commands run from
`apps/api/`:

```bash
alembic upgrade head          # apply migrations
alembic downgrade base        # tear down (DEV ONLY — destroys data)
alembic revision -m "..."     # create a new migration
```

Production must run `alembic upgrade head` on deploy and set
`AIRSPACESIM_API_AUTO_CREATE_SCHEMA=false` (never rely on automatic table
creation in production).

**Never reset or downgrade a production database as a troubleshooting step.**

## Tables

| Table | Purpose |
|---|---|
| `users` | Accounts: email, scrypt password hash, display name, preferred language |
| `auth_sessions` | Server-side login sessions (token hashes + expiry) |
| `learning_progress` | Per-user lesson/stage completion |
| `scenarios` | Durable scenario definitions (session- and user-scoped) |
| `runs` | Run lifecycle, versions in metadata, factual `summary_json` |
| `run_commands` | Operator command envelopes per run |
| `run_checkpoints` | Periodic state snapshots (capped per run; not per-tick) |

## Local PostgreSQL for testing

```bash
docker run -d --name airspacesim-pg -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=airspacesim_test -p 55432:5432 postgres:16-alpine

# run the ENTIRE API suite (incl. migration up/down) against it:
cd apps/api
AIRSPACESIM_TEST_DATABASE_URL="postgresql+psycopg2://postgres:test@127.0.0.1:55432/airspacesim_test" \
  python -m pytest -q
```

CI runs the same matrix in `.github/workflows/postgres.yml` on every push.

## Reset workflow (development only)

- SQLite: delete `apps/api/var/airspacesim-api.db`.
- PostgreSQL: drop/recreate the database, then `alembic upgrade head`.
- Re-seed the demo content with `scripts/seed_hosted_demo.py` and a dev
  account with `scripts/seed_dev_user.py`.

## Retention

Anonymous stopped runs older than
`AIRSPACESIM_API_ANONYMOUS_RUN_RETENTION_DAYS` (default 14) are pruned by a
background sweep; user-owned data is kept indefinitely. See
`docs/developer/AUTHENTICATION.md`.
