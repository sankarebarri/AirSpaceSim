# Target architecture

A monorepo is acceptable.

Suggested direction:

```text
airspacesim/
├── packages/
│   └── airspacesim-core/
├── backend/
├── frontend/
├── content/
│   ├── environments/
│   ├── concepts/
│   ├── scenarios/
│   └── locales/
├── docs/
├── tests/
├── docker-compose.yml
└── .env.example
```

Adapt this to the existing repository rather than forcing exact paths.

## Layers

```text
React frontend
      │
      ▼
FastAPI API
      │
      ▼
Application services
      ├── content service
      ├── scenario validation
      ├── progress service
      ├── run service
      └── authentication
      │
      ▼
AirSpaceSim Core
      ├── domain model
      ├── simulation clock
      ├── aircraft movement
      ├── route following
      ├── commands
      ├── events
      └── separation monitoring
```

## Mode orchestration

### Learn orchestrator

Owns:

- teaching step;
- explanation;
- highlights;
- expected interaction;
- progression;
- completion.

### Practice orchestrator

Owns:

- assistance level;
- available commands;
- scenario-specific objective;
- completion condition;
- debrief.

### Simulate orchestrator

Owns:

- launch;
- broader controls;
- general separation monitoring;
- scenario completion;
- factual summary.

None of these may reimplement aircraft movement or general separation calculations.

## Frontend responsibilities

- render maps, tracks, labels, panels, and controls;
- handle user interaction;
- display engine snapshots;
- manage navigation and language selection;
- optionally store guest-local progress.

## Backend responsibilities

- provide catalogue, scenarios, and environments;
- validate scenarios;
- authenticate users;
- persist progress and runs;
- manage versions;
- save user-created scenarios;
- expose health and production APIs.

The repository audit should decide whether the simulation runtime remains local initially or becomes server-authoritative later. Do not force a premature migration, but extract engine logic from UI components now.
