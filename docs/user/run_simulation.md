# Run The Hosted Simulation

## One-Command Dev Start

From the repository root:

```bash
python3 scripts/start_hosted_dev.py --seed
```

Expected URLs:

```text
API: http://127.0.0.1:8000/health
Web: http://127.0.0.1:5174
```

The script starts both dev servers and creates a Nerava demo run. Press `Ctrl-C` to stop both servers.

For all demo aircraft quickly:

```bash
python3 scripts/start_hosted_dev.py --seed --seed-stagger-seconds 0
```

For Training Alpha:

```bash
python3 scripts/start_hosted_dev.py \
  --seed \
  --seed-airspace airspaces/training_alpha/airspace.v1.json \
  --seed-template airspaces/training_alpha/scenarios/beginner_mix.v1.json
```

## Manual Start

Use **3 terminals**.

## Terminal 1: API

```bash
cd /home/sankarebarri/code/aircore/AirSpaceSim/apps/api
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Leave this running.

Expected API URL:

```text
http://127.0.0.1:8000/health
```

## Terminal 2: Web App

```bash
cd /home/sankarebarri/code/aircore/AirSpaceSim/apps/web
npm run dev -- --host 127.0.0.1 --port 5174
```

Leave this running.

Expected web URL:

```text
http://127.0.0.1:5174
```

## Terminal 3: Seed Demo Run

```bash
cd /home/sankarebarri/code/aircore/AirSpaceSim
python3 scripts/seed_hosted_demo.py --web-base-url http://127.0.0.1:5174
```

The script prints a run URL like:

```text
Web run workspace: http://127.0.0.1:5174/runs/<run-id>
```

Open that URL.

## What To Expect

- The map opens with aircraft already visible.
- The demo has **25 aircraft total**.
- It starts with **7 aircraft**.
- More aircraft appear later in batches.
- Traffic includes departures, arrivals, and overflights.

For a faster demo:

```bash
python3 scripts/seed_hosted_demo.py --web-base-url http://127.0.0.1:5174 --stagger-seconds 2
```

For all aircraft immediately:

```bash
python3 scripts/seed_hosted_demo.py --web-base-url http://127.0.0.1:5174 --stagger-seconds 0
```

## Optional Airspace Package

The default airspace is the fictional Nerava FIR:

```text
airspaces/nerava_fir/airspace.v1.json
```

You can also pass it explicitly:

```bash
python3 scripts/seed_hosted_demo.py \
  --web-base-url http://127.0.0.1:5174 \
  --airspace airspaces/nerava_fir/airspace.v1.json
```

Custom airspaces can use the same `airspaces/<airspace_id>/airspace.v1.json` pattern. The seed script validates points, routes, boundaries, aircraft types, speeds, and flight levels before it creates a run.

Validate an airspace package without starting the API:

```bash
python3 scripts/validate_airspace_package.py airspaces/nerava_fir
```

For Training Alpha:

```bash
python3 scripts/validate_airspace_package.py airspaces/training_alpha
```

## Fictional Training Alpha Run

You can run the fictional Training Alpha airspace:

```bash
python3 scripts/seed_hosted_demo.py \
  --validate-only \
  --airspace airspaces/training_alpha/airspace.v1.json \
  --template airspaces/training_alpha/scenarios/beginner_mix.v1.json
```

Then create the run:

```bash
python3 scripts/seed_hosted_demo.py \
  --web-base-url http://127.0.0.1:5174 \
  --airspace airspaces/training_alpha/airspace.v1.json \
  --template airspaces/training_alpha/scenarios/beginner_mix.v1.json
```

Expected:

- 8 aircraft total
- fictional `ALP_VOR` center point
- four crossing routes
- polygon TMA boundary

## Optional Template Run

You can also run from a reusable template:

First validate the template:

```bash
python3 scripts/seed_hosted_demo.py \
  --validate-only \
  --template airspaces/nerava_fir/scenarios/mixed_traffic.v1.json
```

Expected result:

```text
Template validation passed: airspaces/nerava_fir/scenarios/mixed_traffic.v1.json
```

Then create the run:

```bash
python3 scripts/seed_hosted_demo.py \
  --web-base-url http://127.0.0.1:5174 \
  --airspace airspaces/nerava_fir/airspace.v1.json \
  --template airspaces/nerava_fir/scenarios/mixed_traffic.v1.json
```

The template can define:

- extra routes
- aircraft ID and callsign
- route, speed, and flight level
- when each aircraft appears with `appear_after_seconds`
- optional metadata

The seed script validates templates before it creates a run. It checks:

- duplicate aircraft IDs and callsigns
- unknown routes
- unknown aircraft types
- speed and flight level outside aircraft performance limits
- invalid appearance timing
- selected template `airspace_id` mismatch

Templates are optional. The normal seed command still works without one.
