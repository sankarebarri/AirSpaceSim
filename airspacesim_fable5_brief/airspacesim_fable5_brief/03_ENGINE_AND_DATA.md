# Engine, environment data, and scenario schema

## Core engine

The open-source-ready core should own:

- deterministic simulation time;
- aircraft state;
- movement;
- route traversal;
- heading and level changes;
- commands;
- scripted events;
- aircraft entry and exit;
- horizontal and vertical separation;
- loss-of-separation state transitions;
- serialisable snapshots;
- emitted engine events.

Candidate domain objects:

```text
Simulation
SimulationState
Environment
Sector
Aerodrome
Runway
Waypoint
Navaid
Route
RouteSegment
Frequency
Procedure
Aircraft
AircraftState
FlightIntent
Scenario
ScenarioEvent
Command
SeparationStandard
SeparationMonitor
EngineEvent
```

Illustrative API:

```python
environment = EnvironmentLoader.load(environment_definition)
scenario = ScenarioLoader.load(scenario_definition)

simulation = Simulation(environment=environment, scenario=scenario)
simulation.start()
simulation.issue_command("NVR231", DescendTo(flight_level=310))
simulation.step(seconds=1)
snapshot = simulation.snapshot()
events = simulation.drain_events()
```

## Separation events

Emit events such as:

- separation_loss_started;
- separation_loss_ended.

The same pair remaining continuously below the applicable minimum counts as one event until separation is restored.

Practice-specific success criteria do not belong in the general monitor.

## Environment packs

An environment pack defines a reusable aviation world:

```text
content/environments/nerava-fir/
├── environment.yaml
├── sectors.yaml
├── fixes.yaml
├── navaids.yaml
├── routes.yaml
├── aerodromes.yaml
├── runways.yaml
├── frequencies.yaml
└── procedures/
```

Initial public environment:

- fictional;
- coherent;
- clearly for training;
- realistic five-letter pronounceable fixes;
- plausible route identifiers;
- no Gao-specific public operational data.

Example fictional fixes:

- NARVO
- LUMEK
- SAVEN
- TIRGO
- MOKRA
- DEVAN
- RIKOS

Possible route-style identifiers:

- A1
- B12
- T45
- UL602
- UM731

## Real aeronautical data direction

External data must pass through adapters:

```text
External source
      ↓
Source adapter
      ↓
Validation and normalisation
      ↓
Internal AirSpaceSim environment model
      ↓
Core engine
```

Possible future sources include AIXM, CSV, JSON, and open navigation datasets. Do not couple the engine to one provider.

## Canonical scenario format

Example:

```yaml
schema_version: 1
id: crossing-traffic-practice-1
version: 1.0.0
title_key: scenarios.crossing_practice_1.title

mode: practice
service: enroute
family: separation-fundamentals
concept: crossing-traffic
difficulty: beginner

environment: nerava-fir
environment_version: 1.0.0

simulation:
  duration_seconds: 600
  time_scale_default: 1
  deterministic_seed: null

aircraft:
  - id: nvr231
    callsign: NVR231
    route: T45
    entry_fix: NARVO
    entry_time_seconds: 0
    flight_level: 330
    speed_knots: 440
    label_position: left

allowed_commands:
  - maintain
  - climb
  - descend
  - turn_left
  - turn_right
```

Practice-specific metadata may contain the conflict pair, crossing point, separation requirement, and completion conditions.

## User-created simple template

```yaml
scenario:
  name: My First Simulation
  environment: nerava-fir

aircraft:
  NVR231:
    route: T45
    start: NARVO
    level: 330
    speed: 440

  SKL842:
    route: B12
    start: SAVEN
    level: 330
    speed: 430
```

The app may convert this friendly format into the canonical internal schema.

## Validation

Check:

- schema version;
- unique IDs and callsigns;
- environment, route, and fix existence;
- valid levels and speeds;
- event references;
- supported commands;
- translation keys;
- completion references;
- semantic version format.

Errors must be plain English or translated product messages, not raw exceptions.
