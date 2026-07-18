# How To Test AirSpaceSim

This guide covers three things:

1. automated validation
2. manual testing of the legacy package compatibility UI
3. manual testing of the hosted `FastAPI + React + SQLite` stack

Use this file as the practical test checklist for the current repository state.

## 1. Files To Know Before You Start

These are the main files worth opening while testing:

- [README.md](/home/sankarebarri/code/aircore/AirSpaceSim/README.md)
- [docs/improvements/new-roadmap.md](/home/sankarebarri/code/aircore/AirSpaceSim/docs/improvements/new-roadmap.md)
- [documentation.md](/home/sankarebarri/code/aircore/AirSpaceSim/documentation.md)

Core package and compatibility UI:

- [airspacesim/settings.py](/home/sankarebarri/code/aircore/AirSpaceSim/airspacesim/settings.py)
- [airspacesim/simulation/aircraft_manager.py](/home/sankarebarri/code/aircore/AirSpaceSim/airspacesim/simulation/aircraft_manager.py)
- [airspacesim/static/js/aircraft_simulation.js](/home/sankarebarri/code/aircore/AirSpaceSim/airspacesim/static/js/aircraft_simulation.js)
- [airspacesim/static/js/map_renderer.js](/home/sankarebarri/code/aircore/AirSpaceSim/airspacesim/static/js/map_renderer.js)
- [airspacesim/static/js/ui_runtime.js](/home/sankarebarri/code/aircore/AirSpaceSim/airspacesim/static/js/ui_runtime.js)

Hosted backend:

- [apps/api/app/main.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/main.py)
- [apps/api/app/config.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/config.py)
- [apps/api/app/api/v1/routes/scenarios.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/api/v1/routes/scenarios.py)
- [apps/api/app/api/v1/routes/runs.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/api/v1/routes/runs.py)
- [apps/api/app/api/v1/routes/commands.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/api/v1/routes/commands.py)
- [apps/api/app/sessions/runtime.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/sessions/runtime.py)
- [apps/api/app/sessions/registry.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/sessions/registry.py)

Hosted frontend:

- [apps/web/src/app/App.tsx](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/app/App.tsx)
- [apps/web/src/pages/RunsPage.tsx](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/pages/RunsPage.tsx)
- [apps/web/src/pages/RunDetailPage.tsx](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/pages/RunDetailPage.tsx)
- [apps/web/src/components/TrafficMap.tsx](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/components/TrafficMap.tsx)
- [apps/web/src/lib/api.ts](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/lib/api.ts)
- [apps/web/src/lib/scenario-map.ts](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/lib/scenario-map.ts)
- [apps/web/src/styles/index.css](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/styles/index.css)

## 2. One-Time Setup

Run this from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pip install -r requirements-dev.txt
pip install -e ./apps/api[dev]
cd apps/web
npm install
cd ../..
```

Optional browser setup for Playwright smoke tests:

```bash
python -m playwright install --with-deps chromium
```

## 3. Fast Automated Checks

Run these from the repository root.

Lint:

```bash
just lint
```

Full Python test suite:

```bash
just test
```

API-only tests:

```bash
just test-api
```

Frontend unit and interaction tests:

```bash
just test-web
```

Frontend production build:

```bash
just build-web
```

Full repo validation directly:

```bash
pytest -q
```

Optional browser smoke tests:

```bash
AIRSPACESIM_BROWSER_SMOKE=1 AIRSPACESIM_ENFORCE_COVERAGE=0 pytest -q tests/test_browser_console_clean.py tests/test_hosted_browser_flow.py
```

Notes:

- `tests/test_browser_console_clean.py` checks the legacy generated map path.
- `tests/test_hosted_browser_flow.py` checks the hosted stack path.
- On restricted environments, the hosted browser smoke may skip if loopback socket binding is blocked.

## 4. Manual Test A: Headless Engine Run

> The legacy static-UI compatibility test was retired in 0.2.0 (Phase 8);
> the old flow is preserved at git tag `pre-legacy-ui-removal`.

From a clean temporary directory:

```bash
mkdir -p /tmp/airspacesim-manual && cd /tmp/airspacesim-manual
source /home/sankarebarri/code/aircore/AirSpaceSim/.venv/bin/activate
python -m airspacesim.examples.example_simulation --max-wait 5
```

Pass condition:

- `data/aircraft_state.v1.json` exists with schema `airspacesim.aircraft_state`
- `data/trajectory.v0.1.json` exists with schema `airspacesim.trajectory`
- both contain at least one aircraft/track

## 5. Manual Test B: Hosted FastAPI + React Stack

This tests the new hosted application path.

### 5.1 Start the API

From the repository root:

```bash
cd apps/api
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

What to open:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

Expected:

- `/health` returns a healthy payload
- `/docs` shows the FastAPI schema and interactive routes

### 5.2 Seed one durable scenario

The easiest path is to create a scenario that uses the packaged default airspace and aircraft contracts.

From a new terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scenarios \
  -H "Content-Type: application/json" \
  -d '{"name":"Manual Smoke Scenario","description":"Scenario created for hosted manual testing"}'
```

Why this matters:

- the hosted UI can create runs without a stored scenario
- but a stored scenario gives you route and airspace overlays on the Leaflet map

### 5.3 Start the frontend

From the repository root:

```bash
cd apps/web
npm run dev
```

Open:

- `http://127.0.0.1:5173`

Optional production-like frontend check:

```bash
npm run build
python -m http.server 4173 -d dist
```

Open:

- `http://127.0.0.1:4173`

### 5.4 Files to inspect during hosted testing

Backend:

- [apps/api/app/api/v1/routes/scenarios.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/api/v1/routes/scenarios.py)
- [apps/api/app/api/v1/routes/runs.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/api/v1/routes/runs.py)
- [apps/api/app/api/v1/routes/commands.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/api/v1/routes/commands.py)
- [apps/api/app/sessions/runtime.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/sessions/runtime.py)
- [apps/api/app/sessions/registry.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/sessions/registry.py)

Frontend:

- [apps/web/src/pages/RunsPage.tsx](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/pages/RunsPage.tsx)
- [apps/web/src/pages/RunDetailPage.tsx](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/pages/RunDetailPage.tsx)
- [apps/web/src/components/TrafficMap.tsx](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/components/TrafficMap.tsx)
- [apps/web/src/lib/scenario-map.ts](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/lib/scenario-map.ts)

Database:

- `apps/api/var/airspacesim-api.db` if you use the default API DB path

Useful SQLite check:

```bash
sqlite3 apps/api/var/airspacesim-api.db ".tables"
```

### 5.5 Hosted features to test

#### Overview page

Open `http://127.0.0.1:5173/`

Check:

- the page loads
- navigation works
- counts for scenarios and runs appear
- no browser console errors

#### Runs page

Open `http://127.0.0.1:5173/runs`

Check:

- you can create a draft run
- you can choose `Manual Smoke Scenario` in the scenario dropdown
- after creation, the UI routes into the run workspace

#### Run detail page

In the run workspace, test this flow:

1. Click `Launch`.
2. Confirm the run transitions to running.
3. Confirm the Leaflet map renders.
4. Confirm route and airspace overlays appear for scenario-backed runs.
5. Confirm `Export CSV` is present.

Then test operator controls:

1. `Send ADD_AIRCRAFT`
2. `Send SET_SPEED`
3. `Send SET_FL`
4. `Send SET_SIMULATION_SPEED`

For `ADD_AIRCRAFT`, try:

- Aircraft ID: `AC901`
- Callsign: `OPS901`
- Route ID: `UL602`
- Speed: `420`
- Flight level: `350`

Check:

- the aircraft appears in the visible roster
- the aircraft appears on the map
- the selected-aircraft panel updates
- the last command result card shows the command and status

#### Filters and selection

Test:

- search by callsign, aircraft ID, and route
- route filter
- status filter
- traffic-flow filter
- `Reset` button
- clicking the aircraft in the roster
- clicking the aircraft on the map

Pass condition:

- the visible aircraft count changes correctly
- the selected aircraft stays coherent after filtering
- the selected-aircraft panel always matches the current selection

#### Run lifecycle

Test:

- `Pause`
- `Resume`
- `Stop`

Check:

- the connection health card updates
- runtime state changes are visible
- the status pill changes

## 6. Direct API Checks With curl

These are useful when you want to separate backend behavior from frontend behavior.

Create scenario:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scenarios \
  -H "Content-Type: application/json" \
  -d '{"name":"API Test Scenario"}'
```

List scenarios:

```bash
curl http://127.0.0.1:8000/api/v1/scenarios
```

Create run:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"name":"API Test Run","scenario_id":"<scenario-id-here>"}'
```

Start run:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/runs/<run-id>/start
```

Get run state:

```bash
curl http://127.0.0.1:8000/api/v1/runs/<run-id>/state
```

Add aircraft:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/runs/<run-id>/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type":"ADD_AIRCRAFT",
    "payload":{
      "aircraft_id":"AC950",
      "callsign":"OPS950",
      "route_id":"UL602",
      "speed_kt":420,
      "flight_level":350
    }
  }'
```

Set speed:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/runs/<run-id>/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type":"SET_SPEED",
    "payload":{
      "aircraft_id":"AC950",
      "speed_kt":460
    }
  }'
```

Pass condition:

- command responses return both the persisted command and a result envelope
- run state reflects the command

## 7. What Good Looks Like

Use this final checklist:

- `pytest -q` passes
- `npm run test` passes in `apps/web`
- `npm run build` passes in `apps/web`
- legacy `airspacesim init` workspace still works
- hosted API starts cleanly
- hosted frontend starts cleanly
- scenario-backed run shows overlays on the map
- guided commands work from the hosted UI
- no browser console errors during normal use

## 8. Known Limits While Testing

- The hosted browser smoke test may skip in restricted environments that do not allow loopback socket binding.
- The current FastAPI HTTP-client transport stack is still awkward for full in-process REST route tests, which is why coverage leans on route-layer tests, websocket tests, browser smoke, and manual flow checks instead.
- The React app currently has strong unit and interaction coverage, but the most trustworthy final validation is still a real browser session through the hosted flow.
