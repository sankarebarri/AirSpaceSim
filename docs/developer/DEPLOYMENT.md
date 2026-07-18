# Deployment (Developer Guide)

Decided hosting architecture (decision Q6 in
`docs/repository-audit/08_OPEN_QUESTIONS.md`):

```text
Static host  ──────  React build (apps/web/dist)
     │  VITE_API_BASE_URL
     ▼
PaaS service ──────  FastAPI API (apps/api, Docker or buildpack)
     │  AIRSPACESIM_API_DATABASE_URL
     ▼
Managed PostgreSQL
```

Provider-specific configuration is deliberately minimal so the app can move
between PaaS providers. Do not optimise for unmanaged single-server hosting.

## Local full stack (docker-compose)

```bash
cp .env.example .env          # adjust if needed
docker compose up --build
# Web: http://127.0.0.1:8080   API: http://127.0.0.1:8000/health
docker compose down           # add -v to also drop the database volume
```

The API container waits for PostgreSQL, runs `alembic upgrade head`, then
serves uvicorn (`apps/api/docker-entrypoint.sh`). The web container serves
the production bundle through nginx with the SPA fallback.

## Backend (PaaS)

1. Build/deploy `apps/api/Dockerfile` with the **repository root** as build
   context (the image needs `airspacesim/`, `airspaces/`, and `content/`).
   Platforms without Docker can run
   `pip install . && pip install "./apps/api[postgres]"` and start
   `uvicorn app.main:app` from `apps/api/` after `alembic upgrade head`.
2. Required environment (see `docs/deployment/env/api.production.env.example`):
   - `AIRSPACESIM_API_ENVIRONMENT=production`
   - `AIRSPACESIM_API_DATABASE_URL=postgresql+psycopg2://...` (managed PG)
   - `AIRSPACESIM_API_CORS_ALLOWED_ORIGINS=["https://your-frontend-domain"]`
     — production startup **fails** on `*`, localhost, or 127.0.0.1 origins
   - `AIRSPACESIM_API_AUTO_CREATE_SCHEMA=false`
   - `AIRSPACESIM_API_LOG_LEVEL=INFO`
3. Migrations: the Docker entrypoint applies them on boot. If the platform
   separates release/run phases, run `alembic upgrade head` in the release
   phase instead.
4. Health check endpoint: `GET /health` (also probes the database).
5. Logs are single-line `key=value` structured records; point the
   platform's log drain at stdout.

## Frontend (static hosting)

```bash
cd apps/web
VITE_API_BASE_URL=https://api.your-domain.example npm run build
# deploy dist/
```

- **`VITE_API_BASE_URL` is mandatory for production builds** — the build
  prints a loud warning and the bundle logs a console error if it is
  missing (it would otherwise target localhost).
- SPA fallback (browser refresh on deep routes) must serve `index.html`:
  - `dist/_redirects` covers Netlify-style hosts;
  - `apps/web/nginx.conf` shows the nginx rule (used by the Docker image);
  - for other hosts, configure "rewrite all to /index.html".
- Cookies: authentication uses credentialed requests, so the API's CORS
  origins must list the exact frontend origin (scheme + host).

## Rollback

- API: redeploy the previous image/commit. Migrations are additive from the
  `20260718_0001` baseline; if a future migration must be reverted, run
  `alembic downgrade <revision>` **only after taking a database backup**.
- Frontend: redeploy the previous `dist/` build (stateless).
- Never reset a production database as a troubleshooting step.

## Deployment checklist

1. `docker compose up --build` locally → `scripts/smoke_hosted_app.py`
   passes against it.
2. Provision managed PostgreSQL; set the API env vars above.
3. Deploy the API; check `GET /health` and the startup log line showing
   migrations applied.
4. Build the frontend with the real `VITE_API_BASE_URL`; deploy `dist/`.
5. Verify from a browser: deep-route refresh, EN/FR switch, guest lesson,
   register/sign-in, run history.
6. `python3 scripts/smoke_hosted_app.py --api-base-url https://... --web-base-url https://...`
