# How To Start The Hosted App And See Data

This guide is the shortest working path for the hosted AirSpaceSim app.

If you ran `npm run dev` and saw the React app but no data, that is expected when one of these is true:

- the FastAPI backend is not running
- the frontend is not pointed at the backend
- no run has been created
- the run has not been launched
- no aircraft have been added

This file fixes that step by step.

## What You Will Do

Fast path:

```bash
python3 scripts/start_hosted_dev.py --seed
```

That starts the API, starts the web app, and creates a Gao demo run.

Manual path:

You can still use three terminals:

1. one terminal for the API backend
2. one terminal for the React frontend
3. one terminal to create demo data

At the end, you will open one URL and immediately see a live run with aircraft.

## Files You Will Use

Open these files if you want to confirm what is happening:

- [apps/web/.env.local.example](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/.env.local.example)
- [scripts/start_hosted_dev.py](/home/sankarebarri/code/aircore/AirSpaceSim/scripts/start_hosted_dev.py)
- [scripts/seed_hosted_demo.py](/home/sankarebarri/code/aircore/AirSpaceSim/scripts/seed_hosted_demo.py)
- [apps/api/app/main.py](/home/sankarebarri/code/aircore/AirSpaceSim/apps/api/app/main.py)
- [apps/web/src/lib/api.ts](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/lib/api.ts)
- [apps/web/src/pages/RunDetailPage.tsx](/home/sankarebarri/code/aircore/AirSpaceSim/apps/web/src/pages/RunDetailPage.tsx)

## One-Time Setup

From the repository root:

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

## Step 1: Point React To The Backend

The frontend defaults to `http://127.0.0.1:8000`, but make it explicit so there is no confusion.

From the repository root:

```bash
cp apps/web/.env.local.example apps/web/.env.local
```

That creates:

- `apps/web/.env.local`

Its content should be:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If your backend runs on another host or port, change that value.

## Step 2: Start The Backend

Open Terminal 1.

From the repository root:

```bash
source .venv/bin/activate
cd apps/api
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

What this does:

- starts the FastAPI backend
- creates the SQLite schema automatically if needed
- exposes the API on `http://127.0.0.1:8000`

Now check these URLs in a browser:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

Expected:

- `/health` responds
- `/docs` opens the API docs

If this fails, stop here. The frontend will stay empty until the backend works.

## Step 3: Start React

Open Terminal 2.

From the repository root:

```bash
source .venv/bin/activate
cd apps/web
npm run dev -- --host 127.0.0.1 --port 5174
```

Expected output:

- Vite starts
- it prints `http://127.0.0.1:5174`

Open:

- `http://127.0.0.1:5174`

If the page opens but has no useful data yet, that is still normal. The app shell is running, but no demo run exists yet.

## Step 4: Seed A Demo Run With Aircraft

Open Terminal 3.

From the repository root:

```bash
source .venv/bin/activate
python scripts/seed_hosted_demo.py
```

What this script does:

1. creates a durable scenario in the backend
2. creates a run linked to that scenario
3. starts the run
4. adds the demo aircraft
5. prints the exact URL to open

Expected output looks like:

```text
Hosted AirSpaceSim demo created.
Scenario: Hosted Demo Scenario ...
Run: Hosted Demo Run ...
Aircraft loaded: 25

Open these URLs:
- Web run workspace: http://127.0.0.1:5174/runs/<run-id>
- Runs page: http://127.0.0.1:5174/runs
- API docs: http://127.0.0.1:8000/docs
```

Now open the printed run workspace URL.

## Optional: Validate A Template Without Opening The Browser

`--validate-only` only checks the selected airspace and template. It does not create a scenario, run, or browser URL.

Example:

```bash
python3 scripts/seed_hosted_demo.py \
  --validate-only \
  --airspace airspaces/training_alpha/airspace.v1.json \
  --template airspaces/training_alpha/scenarios/beginner_mix.v1.json
```

Expected:

```text
Template validation passed: airspaces/training_alpha/scenarios/beginner_mix.v1.json
Airspace: training_alpha
Aircraft: 8
Routes: 4
```

To see it in the browser, run the same command without `--validate-only`.

## Optional: Start Training Alpha In The Browser

Use Terminal 1 and Terminal 2 exactly as above.

In Terminal 3, from the repository root:

```bash
source .venv/bin/activate
python3 scripts/seed_hosted_demo.py \
  --web-base-url http://127.0.0.1:5174 \
  --airspace airspaces/training_alpha/airspace.v1.json \
  --template airspaces/training_alpha/scenarios/beginner_mix.v1.json
```

The script prints a URL like:

```text
Web run workspace: http://127.0.0.1:5174/runs/<run-id>
```

Open that URL in the browser.

Expected:

- fictional `training_alpha` airspace
- polygon TMA boundary
- 8 aircraft total
- four crossing Alpha routes

If you started React on `5173`, use:

```bash
python3 scripts/seed_hosted_demo.py \
  --web-base-url http://127.0.0.1:5173 \
  --airspace airspaces/training_alpha/airspace.v1.json \
  --template airspaces/training_alpha/scenarios/beginner_mix.v1.json
```

## Step 5: What You Should See

When the hosted stack is working correctly, the run workspace should show:

- a run title
- a live status pill
- a Leaflet map
- route overlays
- airspace overlays
- aircraft on the map
- a visible traffic roster
- a selected aircraft panel
- operator controls

If the seeded run worked, the page should not be empty.

## Step 6: First Manual Test Flow

Use this exact flow:

1. Open the run workspace URL printed by `scripts/seed_hosted_demo.py`
2. Confirm aircraft are visible in the traffic list and on the map
3. Click one aircraft in the roster
4. Click one aircraft on the map
5. Use search with `OPS901`
6. Reset filters
7. Change one aircraft speed
8. Change one aircraft flight level
9. Change simulation rate
10. Export CSV

## Step 7: If You Want To Start From Scratch Without The Script

You can also do it manually.

### 7.1 Create a scenario

From the repository root:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scenarios \
  -H "Content-Type: application/json" \
  -d '{"name":"Manual Hosted Scenario","description":"Manual hosted demo"}'
```

Copy the returned `id`.

### 7.2 Create a run

```bash
curl -X POST http://127.0.0.1:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"name":"Manual Hosted Run","scenario_id":"<scenario-id>"}'
```

Copy the returned `id`.

### 7.3 Start the run

```bash
curl -X POST http://127.0.0.1:8000/api/v1/runs/<run-id>/start
```

### 7.4 Add aircraft

```bash
curl -X POST http://127.0.0.1:8000/api/v1/runs/<run-id>/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type":"ADD_AIRCRAFT",
    "payload":{
      "aircraft_id":"AC901",
      "callsign":"OPS901",
      "route_id":"UA612",
      "speed_kt":420,
      "flight_level":350
    }
  }'
```

Add another:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/runs/<run-id>/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type":"ADD_AIRCRAFT",
    "payload":{
      "aircraft_id":"AC902",
      "callsign":"OPS902",
      "route_id":"UG859",
      "speed_kt":410,
      "flight_level":330
    }
  }'
```

Then open:

- `http://127.0.0.1:5174/runs/<run-id>`

## Step 8: Where The Data Goes

The hosted app stores durable data in SQLite.

Default database file:

- `apps/api/var/airspacesim-api.db`

You can inspect it with:

```bash
sqlite3 apps/api/var/airspacesim-api.db ".tables"
```

Useful tables:

- `scenarios`
- `runs`
- `run_commands`
- `run_checkpoints`

## Step 9: What To Check If React Still Shows No Data

Check these in order.

### Check 1: Is the backend up?

Open:

- `http://127.0.0.1:8000/health`

If it does not respond, fix the backend first.

### Check 2: Is React pointed at the correct API?

Open:

- `apps/web/.env.local`

Confirm it contains:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If you changed this file, stop the React dev server and run `npm run dev` again.

### Check 3: Did you actually create and start a run?

Open:

- `http://127.0.0.1:5174/runs`

If there are no runs, create one or run:

```bash
python scripts/seed_hosted_demo.py
```

### Check 4: Does the run have aircraft?

Open the run workspace.

If the page loads but shows zero aircraft, add one using:

- `Send ADD_AIRCRAFT`

or rerun:

```bash
python scripts/seed_hosted_demo.py
```

### Check 5: Is the connection panel healthy?

Inside the run workspace, check:

- `Connection health`
- `Freshness`

Good states:

- `Open`
- `Live`

If you see:

- `Error`
- `Closed`
- `Stale`

the backend or websocket path is not healthy.

## Step 10: The Simplest Repeatable Demo Workflow

From the repository root:

Terminal 1:

```bash
source .venv/bin/activate
cd apps/api
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2:

```bash
source .venv/bin/activate
cd apps/web
npm run dev
```

Terminal 3:

```bash
source .venv/bin/activate
python scripts/seed_hosted_demo.py
```

Then open the printed run URL.

That is the shortest path from “React page is empty” to “the hosted app is clearly working.”

## Related Files

Developer-oriented testing guide:

- [docs/user/how_to_test.md](/home/sankarebarri/code/aircore/AirSpaceSim/docs/user/how_to_test.md)

End-user app guide:

- [docs/user/how_to_use_app.md](/home/sankarebarri/code/aircore/AirSpaceSim/docs/user/how_to_use_app.md)
