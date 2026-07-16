# Master prompt for the implementation model

Work on the existing AirSpaceSim repository. Read every document in this folder before changing code.

## Objective

Refactor and extend the current prototype into a content-driven, hostable platform with:

- one reusable simulation engine;
- loadable airspace environments;
- deterministic scenario definitions;
- Learn, Practice, and Simulate;
- English and French application content;
- English-only operational commands;
- PostgreSQL persistence;
- minimal authentication with useful guest access;
- scenario and environment versioning;
- deployment-ready frontend and backend;
- an open-source-ready core engine.

## Work method

Before implementation:

1. inspect the whole repository;
2. identify current engine, scenario, content, frontend, backend, and evaluation code;
3. locate hard-coded data and Gao-specific content;
4. identify reusable code;
5. create a phased migration plan;
6. then implement incrementally.

Do not rewrite the application from scratch unless repository evidence makes that unavoidable.

For every phase:

- preserve working behaviour;
- add or update tests;
- list changed files;
- explain assumptions;
- avoid unrelated redesigns;
- keep the app runnable.

## Product structure

- **Learn:** explain, show, let the learner act, explain the result.
- **Practice:** apply concepts with progressively less assistance and receive a debrief.
- **Simulate:** freely control predefined scripted traffic and receive a factual run summary.

Established loop:

> Learn a concept → practise a similar situation → attempt it with less assistance → receive a debrief.

## Engine rule

The engine must not know about React, FastAPI, HTTP, PostgreSQL, authentication, translations, user accounts, pages, Learn, Practice, or Simulate.

Modes may have different orchestration, controls, guidance, and evaluation, but must use the same engine.

## Scope guardrails

Do not add:

- AI-generated conflicts during a run;
- random live traffic generation;
- formal ATCO certification or grading;
- XP, badges, or leaderboards;
- premature multiplayer;
- a large scenario editor before the scenario schema is stable;
- decorative dashboards unrelated to the core workflow.
