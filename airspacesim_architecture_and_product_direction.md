# AirSpaceSim Architecture and Product Direction

## Purpose

AirSpaceSim is evolving from a single air traffic simulation application into a reusable training and simulation platform.

The long-term direction is to support the same simulation engine across different airports, sectors, and airspace environments without rebuilding the application manually for every location.

The core idea is:

> **One simulation engine, many airspace environments, many training scenarios.**

AirSpaceSim should be able to load different aeronautical environments and scenario definitions while keeping the same underlying engine, application structure, and user experience.

This document captures the current product direction, architecture principles, content organisation, data model ideas, scenario format requirements, engine separation strategy, and deployment preparation plan.

---

# 1. Product Structure

The main user-facing structure is:

- **Learn**
- **Practice**
- **Simulate**

These are different experiences built on top of the same simulation engine.

## Learn

Learn teaches a concept through guided simulation.

Typical flow:

> Explain → Show → Do → Observe → Understand the result

Example:

- identify crossing traffic;
- understand the required separation;
- issue a resolution;
- observe the result.

The simulation itself should be the lesson. Learn should not become a slideshow placed beside a simulator.

## Practice

Practice lets the learner apply a concept with progressively less assistance.

Example progression:

1. conflict announced;
2. conflict not announced;
3. more complex scenario;
4. independent attempt.

Practice may use scenario-specific success criteria.

For example:

- required separation established before a known crossing point;
- required separation maintained through the encounter.

## Simulate

Simulate lets the user control predefined traffic more freely.

It should not behave like a hidden Practice stage.

Simulate should:

- use predefined deterministic traffic scenarios;
- provide no teaching guidance;
- allow broader operational control;
- monitor the simulation using general engine logic;
- produce a factual run summary.

---

# 2. Core Architectural Principle

The engine should not know whether it is being used by Learn, Practice, or Simulate.

Conceptually:

```text
                    AirSpaceSim Core
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
      Learn             Practice          Simulate
   orchestration     orchestration      orchestration
```

The engine should handle:

- simulation time;
- aircraft state;
- movement;
- route following;
- commands;
- events;
- separation monitoring;
- scenario state;
- deterministic execution.

The application layers decide:

- what the user sees;
- what controls are available;
- how much assistance is provided;
- what success means;
- what progress is saved.

---

# 3. One Engine, Many Airspace Environments

A major product direction is to allow the same AirSpaceSim engine to work with many airports and airspace environments without rebuilding the simulation manually.

The engine should not contain assumptions about one specific airport, sector, FIR, route structure, or training location.

Instead, an airspace environment should be loaded as data.

Conceptually:

```text
AirSpaceSim Core
      │
      ▼
Environment Loader
      │
      ├── Fictional Training Airspace
      ├── Airport Environment A
      ├── Airport Environment B
      ├── En-route Sector Environment
      └── Future Real Aeronautical Dataset
```

An environment may provide:

- aerodromes;
- runway geometry;
- navigation fixes;
- waypoints;
- navaids;
- ATS routes and airways;
- sectors;
- frequencies;
- controlled airspace;
- altitude and level constraints;
- eventually procedures.

The simulation engine should consume a normalised internal model rather than depend directly on one source format.

---

# 4. Aeronautical Data Layer

AirSpaceSim should eventually support real aeronautical data.

Potential data categories include:

- fixes and waypoints;
- ATS routes;
- airways;
- aerodromes;
- runways;
- frequencies;
- navaids;
- airspace boundaries;
- sectors;
- standard instrument departures;
- standard arrival routes;
- instrument approach procedures.

The important architectural principle is:

> **External aeronautical data formats should be converted into AirSpaceSim's internal domain model.**

The engine should not directly depend on the quirks of one data provider.

Conceptually:

```text
External Aeronautical Data
          │
          ▼
   Import / Adapter Layer
          │
          ▼
   Normalised Domain Model
          │
          ▼
      AirSpaceSim Core
```

Examples of adapters may eventually include:

```text
AIXM adapter
Open-source navigation dataset adapter
Custom CSV/JSON adapter
Manual fictional environment adapter
```

The exact supported formats can evolve later.

The architecture should first establish a stable internal representation.

---

# 5. Environment Packs

A useful long-term abstraction is an **Environment Pack**.

An Environment Pack describes a reusable simulation world.

Example structure:

```text
environments/
  nerava-fir/
    environment.yaml
    aerodromes.yaml
    fixes.yaml
    navaids.yaml
    routes.yaml
    sectors.yaml
    frequencies.yaml
    procedures/
```

An environment pack should have:

```yaml
id: nerava-fir
version: 1.0.0
name: Nerava FIR
type: fictional
```

A scenario then references the environment:

```yaml
environment: nerava-fir
```

The scenario should not redefine every waypoint, airway, sector, or frequency.

This allows many scenarios to reuse the same environment.

---

# 6. Fictional Public Training Airspace

Before public deployment, sensitive or operationally specific real-world data should be removed.

This includes:

- Gao-specific routes;
- real local points;
- operational sector details;
- sensitive frequencies;
- operational procedures;
- any data that should not be publicly reproduced.

AirSpaceSim should initially ship with a fictional but realistic training environment.

The fictional environment should use realistic aviation naming conventions.

Examples:

## Fictional FIR or region

- Nerava FIR
- Kantara FIR
- Valera FIR

## Five-letter pronounceable fixes

- NARVO
- LUMEK
- SAVEN
- TIRGO
- MOKRA
- DEVAN
- RIKOS

## ATS route names

Use realistic route-style identifiers such as:

- A1
- B12
- T45
- UL602
- UM731

Care must be taken not to present fictional data as real operational data.

The fictional world should be coherent and reusable throughout:

- Learn;
- Practice;
- Simulate;
- user-created scenarios.

---

# 7. Lesson Families

Lessons should not be stored as one flat list.

A scalable structure is:

```text
Service
  → Topic Family
    → Concept
      → Learn
      → Practice stages
      → Related simulations
```

Possible service types:

- Aerodrome
- Approach
- En-route

Possible topic families:

- Separation
- Conflict Management
- Navigation
- Aircraft Requests
- Traffic Sequencing
- Coordination

Example:

```text
En-route
└── Separation
    ├── Crossing Traffic
    │   ├── Learn
    │   ├── Practice 1 — Conflict announced
    │   └── Practice 2 — No conflict announcement
    │
    ├── Opposite-Direction Traffic
    ├── Climbing Through Traffic
    └── Descent Into Occupied Level
```

Another family:

```text
Aircraft Requests
├── Request Descent
├── Request Climb
├── Direct Routing Request
└── Weather Deviation Request
```

---

# 8. Difficulty and User Organisation

AirSpaceSim should avoid assigning one permanent global skill level to a user.

A person may be:

- advanced in en-route control;
- beginner in aerodrome control;
- intermediate in conflict management;
- new to navigation exercises.

Content should therefore carry its own metadata.

Example:

```yaml
service: enroute
topic: separation
difficulty: beginner
```

Possible difficulty values:

- beginner;
- intermediate;
- advanced.

The UI may allow filtering by:

- service;
- topic;
- difficulty.

The interface should remain simple and should not expose the full internal taxonomy unless useful.

---

# 9. Content-Driven Lessons

Adding a new lesson should not require creating a new React page.

Avoid:

```text
CrossingTrafficPage.tsx
OppositeTrafficPage.tsx
ClimbingTrafficPage.tsx
```

Prefer generic runners:

```text
ConceptPage
LearnRunner
PracticeRunner
SimulationRunner
```

These runners receive content definitions.

Example concept definition:

```yaml
id: crossing-traffic
title: Crossing Traffic
service: enroute
topic: separation
difficulty: beginner

learn:
  scenario: crossing-traffic-learn

practice:
  - scenario: crossing-traffic-practice-1
    assistance: announced

  - scenario: crossing-traffic-practice-2
    assistance: none
```

The frontend should render the experience from data.

---

# 10. Scenario Content Location

Scenario and lesson definitions should not be buried inside frontend components.

The recommended direction is:

> **Scenario and lesson definitions live in backend-controlled or shared content files.**

The backend should be the authority for:

- available content;
- scenario definitions;
- scenario versions;
- validation;
- user-created scenarios;
- progress relationships.

The frontend should primarily:

- request content;
- render the experience;
- send user commands;
- display engine state.

The exact simulation runtime location may evolve separately.

A practical intermediate architecture is:

```text
Backend
- scenario storage
- scenario validation
- environment loading
- metadata
- progress
- persistence

Frontend
- interactive rendering
- simulation controls
- lesson presentation
```

A later architecture may move authoritative simulation execution fully to the backend.

---

# 11. Canonical Scenario Format

A canonical scenario format is one of the most important future design decisions.

It should support:

- Learn;
- Practice;
- Simulate;
- user-created scenarios;
- validation;
- versioning;
- replay;
- research.

A possible structure:

```yaml
id: crossing-traffic-practice-1
version: 1.0.0
title: Crossing Traffic Practice 1

mode: practice
service: enroute
difficulty: beginner
topic: separation

environment: nerava-fir

aircraft:
  - callsign: SKY123
    route: T45
    entry_fix: NARVO
    level: 330
    speed: 450

  - callsign: JET456
    route: B12
    entry_fix: SAVEN
    level: 330
    speed: 440

commands:
  - maintain
  - climb
  - descend
  - turn_left
  - turn_right
```

The canonical format should remain human-readable.

---

# 12. User-Created Scenario Scripts

A user should eventually be able to create and run a simulation script.

The script format should be simple enough that a non-technical user can edit a template.

Example:

```yaml
scenario:
  name: My First Simulation
  environment: nerava-fir

aircraft:
  SKY123:
    route: T45
    start: NARVO
    level: 330
    speed: 450

  JET456:
    route: B12
    start: SAVEN
    level: 330
    speed: 440
```

Optional events:

```yaml
events:
  - at: 2m
    aircraft: SKY123
    request: descend 310
```

The application should eventually provide:

- templates;
- examples;
- plain-English validation errors;
- a form-based builder;
- import and export.

The script should remain the portable canonical representation even if the user creates it through a form.

---

# 13. Scenario Validation

Scenario validation is essential.

Before a scenario runs, the validator should check:

- aircraft callsigns are unique;
- routes exist;
- waypoints exist;
- referenced environments exist;
- event times are valid;
- referenced aircraft exist;
- flight levels are valid;
- supported commands exist;
- entry points are valid;
- scenario metadata is complete.

Errors should be understandable.

Good:

```text
Aircraft SKY123 references route T99, but T99 does not exist in the selected environment.
```

Bad:

```text
KeyError: route_42
```

A dedicated component such as:

```text
ScenarioValidator
```

should validate both built-in and user-created scenarios.

---

# 14. Scenario Versioning

Scenario definitions should be versioned from the beginning.

Example:

```text
crossing-traffic-practice-1
version 1.0.0
```

If the scenario later changes, existing run records should still identify the exact scenario version used.

This is important for:

- progress;
- debugging;
- reproducibility;
- research;
- comparison between runs.

---

# 15. Scenario Manifest

Each scenario should have metadata separate from or embedded within its execution definition.

Example:

```yaml
id: crossing-traffic-practice-1
version: 1.0.0
title: Crossing Traffic Practice 1

mode: practice
service: enroute
difficulty: beginner
topic: separation

environment: nerava-fir

commands:
  - maintain
  - climb
  - descend
  - turn_left
  - turn_right
```

This allows the application to discover scenarios dynamically.

---

# 16. Content Registry

Content should be discoverable without manually wiring every scenario into the application.

Example:

```text
content/
  concepts/
    crossing-traffic/
      concept.yaml
      learn.yaml
      practice-1.yaml
      practice-2.yaml

  simulations/
    sector-familiarisation/
      simulation.yaml
```

The application loads the registry and builds the UI from metadata.

---

# 17. Real Separation of the Engine from the App

The AirSpaceSim engine should become a standalone Python package.

Example:

```text
airspacesim-core/
```

It should know nothing about:

- React;
- FastAPI;
- PostgreSQL;
- authentication;
- HTTP;
- Learn;
- Practice;
- Simulate.

The core package should expose domain concepts such as:

```text
Simulation
Aircraft
Route
Waypoint
Command
Event
Scenario
Environment
SeparationMonitor
```

Possible API:

```python
simulation = Simulation.from_scenario(scenario)

simulation.step(delta_time)

simulation.issue_command(
    aircraft_id="SKY123",
    command=DescendTo(level=310),
)
```

The application package then uses the engine:

```text
React
  ↓
FastAPI
  ↓
Application Services
  ↓
AirSpaceSim Core
```

This separation supports:

- multiple frontends;
- research use;
- testing;
- open-source publication;
- future batch simulation;
- future CLI tools;
- reuse across airports and sectors.

---

# 18. Internal Domain Model

The engine should consume a stable internal model.

Possible entities:

```text
Environment
Aerodrome
Runway
Waypoint
Navaid
Route
RouteSegment
Sector
Frequency
Procedure
Aircraft
FlightIntent
Command
Event
Scenario
Simulation
```

External datasets should be converted into these entities.

The engine should not depend directly on raw source files.

---

# 19. Database Structure

A practical initial PostgreSQL structure may include:

```text
users
concepts
scenarios
scenario_versions
environments
environment_versions
learning_progress
simulation_runs
run_events
user_scenarios
```

## concepts

```text
id
slug
title
description
service_type
topic
difficulty
status
```

## environments

```text
id
slug
name
type
current_version_id
created_at
```

## environment_versions

```text
id
environment_id
version
definition_json
created_at
```

## scenarios

```text
id
concept_id nullable
slug
title
mode
difficulty
current_version_id
is_public
created_at
```

Possible modes:

```text
learn
practice
simulate
user
```

## scenario_versions

```text
id
scenario_id
version
definition_json
created_at
```

## learning_progress

```text
id
user_id
concept_id
stage
status
updated_at
```

## simulation_runs

```text
id
user_id nullable
scenario_version_id
environment_version_id
started_at
completed_at
status
summary_json
seed nullable
```

## run_events

Only meaningful events should be stored.

Examples:

```text
instruction_issued
aircraft_entered
aircraft_exited
request_received
loss_of_separation_started
loss_of_separation_ended
```

Do not store every rendering frame or simulation tick unless a future research requirement explicitly needs it.

---

# 20. Replay and Reproducibility

The architecture should leave room for replay.

A run may later be reproduced from:

- scenario version;
- environment version;
- initial state;
- deterministic seed;
- user commands;
- scripted events;
- timestamps.

Replay would be valuable for:

- debriefing;
- instructor review;
- debugging;
- research.

The replay UI does not need to be built now.

---

# 21. Deterministic Simulation

Built-in scenarios should remain deterministic unless controlled variation is intentionally introduced.

If randomness is later used, store a seed.

Example:

```text
seed: 184205
```

This allows exact reproduction.

---

# 22. Hardcoded Data Removal

Hardcoded scenario-specific values should be removed from unrelated UI and engine code.

Search for hardcoded:

- callsigns;
- route names;
- waypoint names;
- coordinates;
- scenario IDs;
- levels;
- available commands;
- lesson text;
- conflict pairs;
- evaluation rules.

Bad:

```python
if callsign == "AFR612":
    ...
```

Better:

```yaml
conflict_pair:
  - SKY123
  - JET456
```

Not every constant is bad.

Domain constants may remain when appropriate and configurable.

Example:

```python
DEFAULT_HORIZONTAL_SEPARATION_NM = 10
```

The important distinction is between:

- domain constants;
- scenario configuration;
- accidental hardcoding.

---

# 23. Hosting Preparation

Before deployment, prepare:

- production environment configuration;
- PostgreSQL;
- migrations;
- CORS;
- API URL configuration;
- logging;
- error handling;
- health checks;
- secret handling;
- production frontend build.

Provide:

```text
.env.example
```

Example:

```text
DATABASE_URL=
SECRET_KEY=
ALLOWED_ORIGINS=
ENVIRONMENT=
```

Add a simple endpoint:

```text
GET /health
```

The repository should contain no production secrets.

---


# 24. Multilingual Product Experience

AirSpaceSim should support a multilingual application experience while keeping the operational simulation interface in English.

The distinction is:

## Multilingual application content

The following parts of the product should support multiple languages:

- homepage;
- Learn catalogue and lesson descriptions;
- lesson explanations and guidance;
- Practice instructions;
- concept pages;
- simulation selection pages;
- account and profile pages;
- progress and history pages;
- general navigation;
- help and explanatory content.

For the first implementation, support:

- English;
- French.

The language should be switchable by the user.

Example:

```text
EN | FR
```

The selected language should apply consistently across the application shell and training content.

## English-only operational simulation interface

The operational simulation panel and ATC command interface should remain in English.

This includes, where applicable:

- aircraft state labels;
- clearance commands;
- climb;
- descend;
- maintain;
- turn left;
- turn right;
- heading;
- flight level;
- speed;
- route;
- command history;
- simulation status;
- operational controls;
- aircraft-related interface terminology.

The reason is that English is the standard international language of aviation and the simulation interface should teach and preserve standard operational terminology.

The application should therefore support two language layers:

```text
Application and training content
→ multilingual

Operational simulation interface and commands
→ English only
```

## Example

A user may browse AirSpaceSim in French:

```text
Apprendre
Pratiquer
Simuler
```

A lesson explanation may also be shown in French.

However, once the user enters the operational simulation interface, commands remain:

```text
MAINTAIN
CLIMB
DESCEND
TURN LEFT
TURN RIGHT
```

Do not translate operational commands into:

```text
MONTER
DESCENDRE
TOURNER À GAUCHE
```

The user should become familiar with the English terminology used in aviation operations.

## Translation architecture

Do not hardcode translated strings directly inside individual React components.

Use a central internationalisation system.

Conceptually:

```text
Frontend
├── locales/
│   ├── en/
│   └── fr/
```

or an equivalent structure supported by the chosen i18n library.

Application text should use stable translation keys.

Example:

```text
home.learn.title
home.practice.title
home.simulate.title
crossing_traffic.description
practice.begin
```

The English and French content then provide translations for those keys.

The operational simulation interface should use its own non-translated English terminology layer.

## Lesson content

Lesson and concept definitions should be designed for multilingual content.

Avoid storing only one final display string when content needs translation.

A lesson may use either translation keys:

```yaml
title_key: concepts.crossing_traffic.title
description_key: concepts.crossing_traffic.description
```

or structured multilingual content:

```yaml
title:
  en: Crossing Traffic
  fr: Trafic convergent
```

The final approach should be consistent across the content system.

For larger and reusable lesson catalogues, translation keys or dedicated locale content files are generally preferable to duplicating complete scenario definitions per language.

The scenario execution data itself should remain language-neutral.

For example:

```yaml
scenario:
  id: crossing-traffic-practice-1
  conflict_pair:
    - SKY123
    - JET456
```

Only the explanatory and user-facing content should be translated.

## User preference

For authenticated users, the selected language may later be stored in the user profile.

For guests, the language may be stored locally in the browser.

The application may initially default to:

- browser language when supported;
- otherwise English.

The user should always be able to switch manually.

## Future languages

The architecture should not assume that only English and French will ever exist.

English and French are the initial supported languages, but the translation system should allow additional languages later without changing the simulation engine or scenario architecture.

Potential future languages may include other languages used by AirSpaceSim's target learners and institutions.

The multilingual architecture should therefore be designed once, while the initial content implementation remains limited to English and French.

---

# 25. Recommended Build Order

## Phase 1 — Architecture Cleanup

1. Define the fictional training environment.
2. Remove Gao-specific and sensitive data.
3. Define the canonical internal aeronautical domain model.
4. Extract scenario definitions from hardcoded UI and application code.
5. Define the canonical scenario format.
6. Create the lesson-family structure.
7. Create scenario validation.
8. Create scenario and environment versioning.

## Phase 2 — Engine Separation

9. Define the public AirSpaceSim Core API.
10. Remove application-specific dependencies from the engine.
11. Add environment loading.
12. Make Learn, Practice, and Simulate consume the same engine and scenario model.
13. Add adapter boundaries for future aeronautical data sources.

## Phase 3 — Content Scalability

14. Create a content registry.
15. Convert Crossing Traffic Learn and Practice into data-driven content.
16. Convert Gao Sector Traffic into a fictional environment simulation.
17. Prove that adding a new scenario does not require creating a new React page.

## Phase 4 — Persistence

18. Set up PostgreSQL.
19. Create environment, scenario, version, run, and progress models.
20. Add minimal authentication.
21. Save Learn and Practice progress.
22. Save factual simulation run summaries.

## Phase 5 — Deployment

23. Add production configuration.
24. Add health checks and logging.
25. Configure frontend and backend deployment.
26. Deploy a development or public preview.

---

# 26. What Not to Build Yet

Avoid expanding scope into:

- many new lessons before the content system is data-driven;
- advanced assessment;
- complicated scoring;
- multiplayer before the single-user architecture is stable;
- AI-generated scenarios;
- a large visual scenario editor;
- broad real-world aeronautical data ingestion before the internal model is stable.

The immediate goal is not maximum feature count.

The goal is:

> **Make AirSpaceSim easy to extend without rebuilding the application every time.**

---

# 27. Long-Term Direction

The long-term vision is:

```text
                    AirSpaceSim Core
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       Training         Simulation       Research
          │                │                │
     Learn/Practice    Free scenarios   Batch experiments
          │                │                │
          └────────────────┼────────────────┘
                           │
                    Environment Layer
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
 Fictional Airspace   Airport Environment  En-route Sector
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                 Aeronautical Data Adapters
```

The same core engine should eventually be able to run:

- a fictional training sector;
- a different airport environment;
- an approach control environment;
- an en-route sector;
- a user-created scenario;
- a research experiment.

The simulation logic should remain reusable.

The environment and scenario data should change.

---

# Final Principle

AirSpaceSim should not become a collection of manually coded simulation screens.

It should become:

> **A reusable air traffic simulation engine, driven by environment data and scenario definitions, with Learn, Practice, and Simulate as different experiences built on top of the same core.**

That is the architectural direction that will make AirSpaceSim scalable, realistic, maintainable, and useful beyond a single airport or training scenario.