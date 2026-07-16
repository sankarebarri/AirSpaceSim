# Migrations

Alembic migration files will live here once the SQLite schema is introduced.
Alembic migration files for the FastAPI service live here.

Current baseline:
- `alembic.ini` in `apps/api/`
- `env.py` for app-configured database URLs
- `versions/20260511_0001_initial_sqlite_baseline.py` for the first SQLite schema

Typical commands from `apps/api/`:

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```
