# AirSpaceSim Tutorial

This is a practical walkthrough for running a simulation, visualizing it, and changing aircraft behavior while the simulation is running.

## 1) Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

## 2) Initialize a project workspace

From the folder where you want runtime files:

```bash
airspacesim init --force
```

This creates `templates/`, `static/`, `data/`, and `examples/`.

## 3) Start simulation and map

Terminal 1:

```bash
python3 examples/example_simulation.py
```

Terminal 2:

```bash
python3 dev_server.py
```

Open:

`http://127.0.0.1:8080/templates/map.html`

If your simulation is running from `airspacesim-playground`, open:

`http://127.0.0.1:8080/airspacesim-playground/templates/map.html`

Important:
- `dev_server.py` serves files and accepts:
  - `POST /api/events`
  - `POST /airspacesim-playground/api/events`
- If you accidentally open `/airspacesim/templates/map.html` from repo root, `dev_server.py` now serves playground assets/data behind that path so events still land in `airspacesim-playground/data/inbox_events.v1.json`.
- If you use `python3 -m http.server` instead, controls can only queue payloads unless you add another POST-capable endpoint.
- If the page is opened from another static server (for example `:5500`) and that server rejects POST (`405`), UI now automatically retries `http://127.0.0.1:8080/.../api/events`.

Use the **Operator Controls** panel in the right sidebar to generate:
- `ADD_AIRCRAFT`
- `SET_SPEED`
- `SET_FL`
- `SET_SIMULATION_SPEED`

Operator payload rules:
- `SET_SPEED.payload.aircraft_id` must be aircraft ID (for example `AC800`), not callsign (for example `OPS800`).
- `ADD_AIRCRAFT` with an existing `aircraft_id` is skipped to avoid duplicate runtime aircraft entries.

Aircraft map presentation:
- Aircraft use an SVG aircraft icon marker (not circle marker).
- Color semantics:
  - outbound from Gao center: green
  - inbound to Gao center: red
  - transit/unknown: amber/gray
- Flow colors are also shown in the **Flow Legend** card on the right panel.
- Permanent label shows flight level (`FLxxx`) instead of speed.
- FL display uses explicit `flight_level` when provided; otherwise it falls back to `altitude_ft / 100`.
- Click an aircraft icon to open metadata popup (`id`, `callsign`, `route`, `FL`, `vertical_rate_fpm`, `status`, `updated_utc`).
- Click a marker or aircraft table row to select aircraft:
  - selected aircraft is highlighted in map and table
  - `SET_SPEED` and `SET_FL` aircraft ID fields auto-fill
  - `Set Flight Level` panel shows `Current FL`
  - aircraft ID inputs (`SET_SPEED`, `SET_FL`) no longer overwrite manual edits while you are typing
  - FL input suggestion no longer overwrites manual edits while you are typing

If no command API sink is configured, the panel builds a canonical JSON payload you can paste into `data/inbox_events.v1.json`.
In that mode, button labels start with `Queue ...` (queued only, not yet applied).
When a sink is connected, labels switch to `Send ...` and changes apply live.
While sending commands, submit buttons are temporarily disabled (`Sending...`) to prevent accidental duplicate clicks.
If you try to add an existing `aircraft_id`, the UI warns and does not submit.

For the playground setup, start the simulation with:

```bash
python3 airspacesim-playground/examples/example_simulation.py
```
and serve from the playground root so `data/` paths align:

```bash
cd airspacesim-playground
python3 ../dev_server.py
```

In the map, the controls status should show:
- `Command sink target: /airspacesim-playground/api/events`

If it shows `/api/events` while simulation runs in `airspacesim-playground/`, you are on a mismatched page/workspace.

## 4) Add aircraft while simulation is running
You can use the Operator Controls panel or edit `data/inbox_events.v1.json` manually with an `ADD_AIRCRAFT` event:

```json
{
  "schema": { "name": "airspacesim.inbox_events", "version": "1.0" },
  "metadata": { "source": "tutorial", "generated_utc": "2026-02-20T00:00:00Z" },
  "data": {
    "events": [
      {
        "event_id": "evt-add-001",
        "type": "ADD_AIRCRAFT",
        "created_utc": "2026-02-20T00:00:01Z",
        "payload": {
          "aircraft_id": "AC900",
          "route_id": "UA612",
          "callsign": "TUT900",
          "speed_kt": 420
        }
      }
    ]
  }
}
```

The manager applies this idempotently by `event_id`.

## 5) Change speed of one aircraft

Add another event to the same file:

```json
{
  "event_id": "evt-speed-001",
  "type": "SET_SPEED",
  "created_utc": "2026-02-20T00:00:02Z",
  "payload": {
    "aircraft_id": "AC900",
    "speed_kt": 240
  }
}
```

## 5.1) Set flight level metadata

`SET_FL` changes displayed FL only. It does not alter movement physics.

```json
{
  "event_id": "evt-fl-001",
  "type": "SET_FL",
  "created_utc": "2026-02-20T00:00:02Z",
  "payload": {
    "aircraft_id": "AC900",
    "flight_level": 330
  }
}
```

## 6) Understand simulation speed multiplier

- Per-aircraft speed uses knots (`NM/hour`).
- Motion each tick uses:
  - `distance_nm = (speed_kt / 3600) * dt_seconds * SIMULATION_SPEED`
- `SIMULATION_SPEED=2.0` means all aircraft progress 2x faster in simulated time.

Current state:
- `SIMULATION_SPEED` exists and is applied globally in motion updates.
- Runtime change is supported via `SET_SIMULATION_SPEED` event:

```json
{
  "event_id": "evt-simrate-001",
  "type": "SET_SIMULATION_SPEED",
  "created_utc": "2026-02-20T00:00:03Z",
  "payload": { "sim_rate": 2.0 }
}
```

## 7) Key runtime files to inspect

- `data/aircraft_state.v1.json`: canonical UI/runtime state
- `data/trajectory.v0.1.json`: trajectory output
- `data/inbox_events.v1.json`: command/event input

## 8) Optional live command sink

If you run a backend endpoint that accepts canonical inbox event envelopes via HTTP POST, add this to `data/ui_runtime.v1.json`:

```json
{
  "data": {
    "sinks": {
      "aircraft_events": {
        "url": "http://127.0.0.1:9000/events"
      }
    }
  }
}
```

Then Operator Controls will POST events directly instead of requiring manual file copy.

## 9) Confirm events in console

When commands are working, you will see terminal traces like:

- `dev_server.py`:
  - `[EVENT SINK] received batch with N event(s)`
  - `[EVENT SINK] event_id=... type=... payload=...`
  - `[EVENT SINK] wrote to .../data/inbox_events.v1.json`
- simulation process:
  - `[EVENT LOOP] polled N new event(s)`
  - `[EVENT] applied id=... action=...`
  - `[EVENT] batch summary applied=X skipped=Y rejected=Z`

## 10) Clean restart behavior (important)

`FileEventAdapter` dedupes by `event_id` only during the current process lifetime.
If you restart simulation without clearing `data/inbox_events.v1.json`, old events can replay.

Before a clean restart, reset inbox:

```json
{
  "schema": { "name": "airspacesim.inbox_events", "version": "1.0" },
  "metadata": { "source": "airspacesim.seed", "generated_utc": "2026-02-20T00:00:00Z" },
  "data": { "events": [] }
}
```
