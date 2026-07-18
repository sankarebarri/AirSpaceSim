#!/bin/sh
# Wait for the database, apply migrations, then serve the API.
set -e

echo "[entrypoint] waiting for database..."
python - <<'PY'
import time
import sys

from sqlalchemy import create_engine, text

from app.config import get_settings

url = get_settings().database_url
for attempt in range(30):
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        print(f"[entrypoint] database ready (attempt {attempt + 1})")
        break
    except Exception as exc:  # noqa: BLE001 - retry loop
        print(f"[entrypoint] database not ready yet: {exc}")
        time.sleep(2)
else:
    sys.exit("[entrypoint] database never became ready")
PY

echo "[entrypoint] applying migrations..."
alembic upgrade head

echo "[entrypoint] starting uvicorn..."
UVICORN_LOG_LEVEL=$(echo "${AIRSPACESIM_API_LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --log-level "$UVICORN_LOG_LEVEL"
