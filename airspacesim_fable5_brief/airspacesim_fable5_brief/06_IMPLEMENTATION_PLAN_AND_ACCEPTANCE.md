# Implementation plan and acceptance criteria

## Phase 0 — Audit

- map repository;
- locate simulation logic;
- locate scenarios and lesson content;
- locate separation and evaluation logic;
- find Gao-specific data;
- find hard-coded callsigns, routes, levels, coordinates, commands, and text;
- inspect tests, database, auth, i18n, and deployment;
- propose migration.

## Phase 1 — Engine boundary

- establish the core package;
- remove application dependencies from core logic;
- preserve current Learn, Practice, and Simulate;
- add core tests.

## Phase 2 — Data-driven environments and scenarios

- create fictional environment;
- define schemas;
- add validation;
- add content registry;
- convert existing scenarios from hard-coded definitions.

## Phase 3 — Traffic Relationships

- add Separation Fundamentals;
- implement all five Traffic Relationships lessons;
- show Vertical and Horizontal Separation as planned;
- add English and French;
- reuse generic lesson activities.

## Phase 4 — Persistence and auth

- add PostgreSQL and migrations;
- add versions, progress, and run summaries;
- add minimal auth;
- preserve guest access.

## Phase 5 — Deployment

- production configuration;
- health checks;
- logs;
- deploy frontend and backend;
- provision PostgreSQL;
- verify CORS, migrations, routing, auth, and language preference.

## Phase 6 — User-created scenarios

Only after schema and validation are stable:

- editable template;
- validation;
- save and run;
- later add a form-based builder.

## Acceptance criteria

### Product

- Learn, Practice, and Simulate still work.
- Existing Crossing Traffic flow still works.
- Traffic Relationships is complete.
- Vertical and Horizontal Separation appear as planned.
- English and French work.
- Operational commands remain English.

### Engine

- Core imports no FastAPI, database, auth, React, or browser code.
- All modes use the same engine.
- Scenarios are deterministic.
- Core tests pass.
- Continuous losses are not counted once per tick.
- Practice-specific logic stays outside the general monitor.

### Content

- New content is data-driven.
- Fictional environment replaces Gao-specific public data.
- Labels are configurable.
- No foundational lesson exposes predicted minimum separation or time-to-minimum-separation.

### Persistence and auth

- PostgreSQL migrations work.
- Signed-in users can save progress and run summaries.
- Guests retain useful access.
- Protected routes reject unauthenticated writes.

### Deployment

- frontend production build succeeds;
- backend starts from environment configuration;
- `/health` succeeds;
- no secrets are committed;
- production does not require localhost;
- migrations are runnable;
- browser refresh works on frontend routes.
