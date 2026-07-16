# CLAUDE.md

## Project: AirSpaceSim

AirSpaceSim is a reusable air traffic learning and simulation platform.

The hosted web application is one consumer of a reusable simulation engine that is intended to be open sourced and later reused for research, AI, ML, batch simulation, and more sophisticated aviation projects.

Before making architectural changes, read the implementation brief in this order:

1. `README.md`
2. `00_MASTER_PROMPT.md`
3. `01_PRODUCT_AND_GUARDRAILS.md`
4. `02_TARGET_ARCHITECTURE.md`
5. `03_ENGINE_AND_DATA.md`
6. `04_CONTENT_AND_I18N.md`
7. `05_DATABASE_AUTH_DEPLOYMENT.md`
8. `06_IMPLEMENTATION_PLAN_AND_ACCEPTANCE.md`
9. `07_TRAFFIC_RELATIONSHIPS_PROMPT.md`
10. `08_REPOSITORY_AUDIT_PROMPT.md`

If these files are stored under a documentation folder in the repository, follow the equivalent paths.

---

## Core product structure

The user-facing product has three primary experiences:

- **Learn**
- **Practice**
- **Simulate**

### Learn

Guided learning through the simulation itself.

Typical flow:

> Explain → Show → Do → Observe → Understand the result.

### Practice

Apply concepts with progressively less assistance and receive a concise debrief.

### Simulate

Freely control predefined scripted traffic and receive a factual run summary.

Do not merge these experiences into one generic mode.

---

## Non-negotiable architecture

Learn, Practice, and Simulate must use the same simulation engine.

Do not create separate:

- Learn movement logic;
- Practice movement logic;
- Simulate movement logic;
- fake lesson animations that bypass the engine.

The engine must not depend on:

- React;
- FastAPI;
- HTTP;
- PostgreSQL;
- SQLAlchemy;
- authentication;
- translation libraries;
- browser APIs;
- application routing;
- Learn, Practice, or Simulate concepts.

The core engine should remain independently importable, testable, documentable, and packageable.

---

## Engine direction

The reusable engine should own:

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

Application-specific orchestration belongs outside the engine.

### Practice-specific logic

Practice may use scenario-specific criteria, such as:

- establish separation before a crossing point;
- maintain it through the encounter;
- expose only commands relevant to the scenario.

This logic must not become the global engine separation monitor.

### Simulate separation logic

Simulate should use general separation monitoring.

One continuous loss of separation involving the same aircraft pair counts as one event until valid separation is restored.

Do not count one event per simulation tick.

---

## Content and scenarios

Built-in scenarios must be deterministic and reproducible.

Do not generate live conflicts or traffic with AI.

New lessons and scenarios must be data-driven.

Avoid one bespoke React page per lesson.

Prefer generic components such as:

- `ConceptPage`
- `LearnRunner`
- `PracticeRunner`
- `SimulationRunner`
- `ObservationStep`
- `HighlightStep`
- `ClassificationStep`
- `CommandStep`
- `CompletionStep`

Scenario definitions should be versioned and validated.

Do not hard-code scenario-specific values inside unrelated UI or engine code.

Examples of data that should live in scenario or environment definitions:

- callsigns;
- routes;
- fixes;
- coordinates;
- levels;
- aircraft entry times;
- available commands;
- conflict pairs;
- lesson steps;
- completion conditions;
- label placement.

---

## Airspace environments

AirSpaceSim should support one engine with many airport and airspace environments.

Environment data should be loaded through environment packs.

An environment may contain:

- sectors;
- fixes;
- waypoints;
- navaids;
- ATS routes;
- aerodromes;
- runways;
- frequencies;
- airspace boundaries;
- eventually procedures.

External aeronautical data must pass through adapters and be normalised into AirSpaceSim's internal domain model.

Do not directly couple the engine to one data provider or raw external format.

---

## Public environment data

Remove Gao-specific and potentially sensitive operational data from public content.

Use a coherent fictional training environment.

Use realistic fictional aviation-style names.

Avoid user-facing placeholders such as:

- Point A;
- Route Alpha;
- Airspace Alpha;
- Aircraft A.

Do not present fictional data as operationally valid real-world data.

---

## Curriculum

Initial family:

```text
En-route
└── Separation Fundamentals
    ├── Traffic Relationships
    │   ├── Understanding Track
    │   ├── Same-Track Traffic
    │   ├── Reciprocal-Track Traffic
    │   ├── Crossing-Track Traffic
    │   └── Identify the Relationship
    ├── Vertical Separation — Planned
    └── Horizontal Separation — Planned
        ├── Lateral Separation
        └── Longitudinal Separation
            ├── Same Track
            ├── Reciprocal Track
            └── Crossing Track
```

Only Traffic Relationships is implemented in the current content phase.

Vertical and Horizontal Separation should remain visible as planned content, not broken or partially implemented.

Traffic Relationships teaches recognition.

The existing Crossing Traffic lesson teaches management.

---

## Multilingual behaviour

The application supports:

- English;
- French.

Translate:

- homepage;
- navigation;
- curriculum;
- concept pages;
- lesson explanations;
- Practice guidance;
- help;
- account pages;
- general product content.

Keep operational commands in English:

- `MAINTAIN`
- `CLIMB`
- `DESCEND`
- `TURN LEFT`
- `TURN RIGHT`
- `HEADING`
- `FLIGHT LEVEL`
- `SPEED`

Scenario geometry and execution data must remain language-neutral.

Do not duplicate scenarios per language.

Use central translation keys.

---

## Authentication and guest access

Do not force users to sign in before trying AirSpaceSim.

Guests should be able to:

- browse public Learn content;
- run public Practice scenarios;
- launch solo Simulate scenarios;
- receive immediate debriefs and summaries.

Authentication mainly adds:

- persistent progress;
- cross-device continuation;
- run history;
- saved language preference;
- saved user-created scenarios;
- future hosted shared sessions.

Keep authentication minimal:

- sign in;
- sign out;
- current user;
- protected persistence routes;
- optional display name;
- preferred language.

Do not add organisations, billing, advanced roles, or complex RBAC yet.

---

## Database

Use PostgreSQL for hosted persistence.

Use migrations.

Do not rely only on automatic table creation during production startup.

Do not store every simulation frame.

Persist meaningful records such as:

- scenario and environment versions;
- progress;
- run summaries;
- meaningful engine events;
- user-created scenarios.

---

## Deployment

The application must be production-configurable.

Required:

- `.env.example`;
- environment-based API URLs;
- no committed secrets;
- no production dependency on localhost;
- backend health endpoint;
- migrations;
- CORS configuration;
- useful logs;
- correct SPA route handling;
- production frontend build.

The site may be labelled:

> Training and visualisation software. Not for operational use.

---

## Work process

Before major changes:

1. inspect the repository;
2. identify current boundaries;
3. find hard-coded data;
4. preserve reusable code;
5. propose the migration;
6. implement incrementally.

For each task:

- keep the app runnable;
- add or update tests;
- list modified files;
- explain assumptions;
- avoid unrelated refactors;
- do not silently change product behaviour.

Do not perform a full rewrite unless repository evidence clearly justifies it.

---

## Do not add without explicit instruction

- AI-generated live conflicts;
- random traffic generation;
- formal ATCO assessment or certification;
- XP;
- badges;
- leaderboards;
- premature multiplayer;
- a large scenario editor;
- speculative dashboards;
- unrelated visual redesign;
- translated French operational commands;
- duplicate engines;
- provider-specific aeronautical logic inside the core.

---

## Current implementation priority

The current priority is:

1. audit the existing repository;
2. establish the engine boundary;
3. create data-driven environment and scenario models;
4. replace Gao-specific public data;
5. implement the Traffic Relationships learning journey;
6. preserve the existing Crossing Traffic Learn and Practice flows;
7. add English and French content;
8. prepare PostgreSQL and minimal authentication;
9. prepare and deploy the app.

When a request conflicts with these priorities, preserve the architecture and ask for clarification rather than improvising.
