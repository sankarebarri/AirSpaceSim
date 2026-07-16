# Quick Test Guide — Hosted App (dashboard/cockpit against a live sim)

The other doc (`how_to_start_hosted_app.md`) covers every option. This is the
short path: one command to start everything, one command if it's already
running from a previous session, and how to see the run in your browser.

## 1. Start the stack (API + web + a seeded demo run)

From the repo root, with your venv active:

```bash
python3 scripts/start_hosted_dev.py --seed
```

This starts the FastAPI backend on `http://127.0.0.1:8000`, the Vite dev
server on `http://127.0.0.1:5174`, waits for the API to become healthy, then
creates one demo scenario + one demo run so there's something to look at.
Leave this terminal open — it streams `[api]`/`[web]` logs. `Ctrl-C` stops
both.

## 2. Open the browser

```
http://127.0.0.1:5174/runs
```

The seed script always uses the same fixed session id
(`airspacesim-local-dev-demo`), so your browser needs to "adopt" it once.
Open devtools console on that page and run:

```js
localStorage.setItem('airspacesim.session-id', 'airspacesim-local-dev-demo')
```

Reload the page. You'll now see every run this script has ever created for
you, and re-running the seed script later stays visible in the same list —
no need to repeat this step unless you clear localStorage.

Click into a run to land on the new cockpit (`/runs/<id>`).

## 3. Re-seeding (make a fresh run without restarting the stack)

Leave the terminal from step 1 running and, in a **second** terminal:

```bash
python3 scripts/seed_hosted_demo.py
```

This talks to the already-running API and adds another scenario + run under
the same session id.

---

## Troubleshooting

### `ERROR: [Errno 98] Address already in use`

A previous `start_hosted_dev.py` process (yours or an earlier one of mine)
is still holding port 8000 and/or 5174. Find and stop it:

```bash
lsof -i :8000 -sTCP:LISTEN
lsof -i :5174 -sTCP:LISTEN
```

That prints the PID(s) holding those ports. Kill the parent
`start_hosted_dev.py` PID (not just the uvicorn/vite children) so both
servers and the reload-watcher shut down cleanly:

```bash
ps -o pid,ppid,cmd -p <PID>          # confirm it's start_hosted_dev.py / uvicorn / vite before killing
kill <PID>
```

Then re-run step 1.

If you'd rather not hunt for stray processes, run on different ports
instead of killing anything:

```bash
python3 scripts/start_hosted_dev.py --seed --api-port 8010 --web-port 5190
```

(Web dev server auto-proxies to whatever `--api-port` you pass.)

### `HTTP 429 ... "You already have 3 active runs (limit: 3)"`

Each session is capped at 3 concurrently *active* (running/paused) runs —
this is a real product guardrail, not a bug. Old test runs from earlier
sessions pile up against that cap. Two ways to clear it:

**A. Stop old runs from the UI** — open `/runs`, open each active run, hit
**TERMINATE**.

**B. Stop them from the API directly**, once you know their IDs from
`/runs`:

```bash
curl -s -X POST "http://127.0.0.1:8000/api/v1/runs/<run_id>/stop" \
  -H "X-Airspacesim-Session: airspacesim-local-dev-demo"
```

Repeat for each active run until you're back under 3, then re-run the seed
script.

### Database schema errors (`HTTP 500` on scenario/run creation)

Only relevant if you're pointing at an old `apps/api/var/airspacesim-api.db`
that predates a migration. Bring it up to date without losing data:

```bash
cd apps/api
export AIRSPACESIM_API_DATABASE_URL="sqlite:///$(pwd)/var/airspacesim-api.db"
../../.venv/bin/python -m alembic upgrade head
```

### WebSocket `403 Forbidden` / run pages 404ing on load

Your browser's `airspacesim.session-id` in localStorage doesn't match the
session the run was created under. Re-run the `localStorage.setItem(...)`
line from step 2 with the session id printed by whichever seed invocation
created the run you're trying to view, then reload.
