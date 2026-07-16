# Deployment Guide

This guide describes the current hosting shape for AirSpaceSim.

The recommended deployment model is:

- host `apps/api/` as a Python API service
- host `apps/web/dist/` as a static frontend
- point the frontend at the API with `VITE_API_BASE_URL`

Do not make the FastAPI app serve the React build yet. Keeping them separate is simpler for now and keeps the reusable engine independent from hosted app concerns.

## Components

### Engine

Location: `airspacesim/`

Purpose:

- reusable Python simulation engine
- scenario loading
- aircraft movement
- event/command application
- trajectory export

The engine is imported by the API. It is not deployed as its own web service.

### API

Location: `apps/api/`

Purpose:

- FastAPI HTTP routes
- websocket run stream
- scenario/run persistence
- hosted runtime sessions

### Web

Location: `apps/web/`

Purpose:

- React frontend
- landing page
- lessons
- run workspace
- map and command UI

## API Environment Variables

The API reads environment variables with the `AIRSPACESIM_API_` prefix.

| Variable | Default | Purpose |
| --- | --- | --- |
| `AIRSPACESIM_API_APP_NAME` | `AirSpaceSim API` | FastAPI app title |
| `AIRSPACESIM_API_API_V1_PREFIX` | `/api/v1` | Versioned API prefix |
| `AIRSPACESIM_API_DATABASE_URL` | `sqlite:///./var/airspacesim-api.db` | SQLAlchemy database URL |
| `AIRSPACESIM_API_DATABASE_ECHO` | `false` | SQL query logging |
| `AIRSPACESIM_API_AUTO_CREATE_SCHEMA` | `true` | Create DB schema at startup |
| `AIRSPACESIM_API_CHECKPOINT_RETENTION_PER_RUN` | `25` | Runtime checkpoint retention |
| `AIRSPACESIM_API_CORS_ALLOWED_ORIGINS` | `["*"]` | Allowed browser origins |
| `AIRSPACESIM_API_CORS_ALLOW_CREDENTIALS` | `false` | Credentialed CORS |
| `AIRSPACESIM_API_DEBUG` | `false` | FastAPI debug mode |

For production, set a specific CORS origin instead of `["*"]`.

Example:

```bash
export AIRSPACESIM_API_DATABASE_URL='sqlite:////srv/airspacesim/airspacesim-api.db'
export AIRSPACESIM_API_CORS_ALLOWED_ORIGINS='["https://airspacesim.example.com"]'
export AIRSPACESIM_API_CORS_ALLOW_CREDENTIALS=false
```

Example environment files:

- local API: `apps/api/.env.example`
- staging API: `docs/deployment/env/api.staging.env.example`
- production API: `docs/deployment/env/api.production.env.example`

SQLite is acceptable for early hosted demos. For multi-user production use, plan a proper database migration path before relying on it heavily.

## Web Environment Variables

The web app uses Vite environment variables.

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Base URL for HTTP and websocket API calls |

The websocket URL is derived automatically:

- `http://...` becomes `ws://...`
- `https://...` becomes `wss://...`

Example:

```bash
VITE_API_BASE_URL=https://api.airspacesim.example.com npm run build
```

Example environment files:

- staging web: `docs/deployment/env/web.staging.env.example`
- production web: `docs/deployment/env/web.production.env.example`

## Build And Start Commands

### API Development

```bash
cd apps/api
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### API Production-Style Start

```bash
cd apps/api
alembic upgrade head
../../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For a real deployment, run this under a process manager supplied by the host platform.

### Web Development

```bash
cd apps/web
npm run dev -- --host 127.0.0.1 --port 5174
```

### Web Production Build

```bash
cd apps/web
VITE_API_BASE_URL=https://api.airspacesim.example.com npm run build
```

Deploy the generated `apps/web/dist/` directory to a static host.

### Web Production Preview

This is useful for local verification only:

```bash
cd apps/web
npm run preview -- --host 0.0.0.0 --port 5174
```

## Smoke Test

After deploying or starting the local hosted app, run:

```bash
python3 scripts/smoke_hosted_app.py \
  --api-base-url http://127.0.0.1:8000 \
  --web-base-url http://127.0.0.1:5174
```

For production:

```bash
python3 scripts/smoke_hosted_app.py \
  --api-base-url https://api.airspacesim.example.com \
  --web-base-url https://airspacesim.example.com
```

The smoke test checks:

- `/health`
- database readiness through the health endpoint
- `/api/v1/airspaces`
- `/api/v1/runs`
- optional web HTML response

## Deployment Checklist

1. Build and test the engine.
2. Apply API migrations with `alembic upgrade head`.
3. Start API with production environment variables.
4. Build web with `VITE_API_BASE_URL` pointing at the API.
5. Deploy `apps/web/dist/` to the static host.
6. Open the web app.
7. Confirm top-right API indicator shows the hosted API host.
8. Confirm `/runs`, `/lessons`, and `/airspaces` open.
9. Create or seed a run.
10. Confirm websocket map updates work over `ws://` or `wss://`.
11. Run `scripts/smoke_hosted_app.py`.

## Current Hosting Decision

Use separate hosting for API and web.

Reason:

- the API remains focused on simulation/runtime state
- the web app can be deployed as static files
- the engine remains reusable by non-web projects
- fewer app-boundary changes are needed now

Later, if we want a single deployable artifact, we can add an explicit FastAPI static-file mode. That should be a separate decision, not an accidental coupling.
