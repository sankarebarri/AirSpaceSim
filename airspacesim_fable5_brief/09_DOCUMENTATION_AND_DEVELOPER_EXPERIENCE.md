# Developer and User Documentation Contract

AirSpaceSim must include clear, maintained documentation for two different audiences:

1. the developer maintaining or contributing to the project;
2. the general user who may not be technical.

Documentation is part of the product and must be updated whenever commands, architecture, setup, authentication, deployment, or user flows change.

---

# 1. Required repository documentation

The repository should contain a clear documentation structure.

Suggested layout:

```text
airspacesim/
├── README.md
├── CLAUDE.md
├── .env.example
├── .gitignore
├── docs/
│   ├── developer/
│   │   ├── GETTING_STARTED.md
│   │   ├── LOCAL_DEVELOPMENT.md
│   │   ├── TESTING.md
│   │   ├── AUTHENTICATION.md
│   │   ├── DATABASE.md
│   │   ├── DEPLOYMENT.md
│   │   ├── TROUBLESHOOTING.md
│   │   ├── ARCHITECTURE.md
│   │   ├── CONTENT_AUTHORING.md
│   │   └── COMMAND_REFERENCE.md
│   │
│   └── user/
│       ├── USER_GUIDE.md
│       ├── LEARN_GUIDE.md
│       ├── PRACTICE_GUIDE.md
│       ├── SIMULATE_GUIDE.md
│       ├── ACCOUNT_AND_PROGRESS.md
│       └── FAQ.md
```

Adapt the exact paths to the existing repository where appropriate, but preserve the audience separation.

---

# 2. Root README

The root `README.md` should be concise and navigational.

It should explain:

- what AirSpaceSim is;
- the current project status;
- the three product modes;
- the technology stack;
- the quickest way to start locally;
- links to detailed developer documentation;
- links to general user documentation;
- the non-operational-use disclaimer;
- the licence status of the application and core engine where decided.

The root README should not become an enormous setup manual.

It should direct readers to the correct detailed document.

---

# 3. Developer Getting Started Guide

Create:

```text
docs/developer/GETTING_STARTED.md
```

It must tell the developer exactly how to get the project running from a clean machine.

Include:

- required software;
- supported versions;
- repository clone command;
- environment file setup;
- database setup;
- dependency installation;
- migration commands;
- frontend startup;
- backend startup;
- optional Docker startup;
- test commands;
- browser URLs;
- default development ports;
- how to stop services.

Use complete commands, not vague instructions such as “start the app”.

Example categories:

```text
Terminal 1 — Backend
Terminal 2 — Frontend
Terminal 3 — Optional database/logs
```

Explicitly state when commands must run in separate terminal windows.

If one command can start all services, document that as the recommended route and still document individual commands for debugging.

---

# 4. Command Reference

Create:

```text
docs/developer/COMMAND_REFERENCE.md
```

This should be a compact command cheat sheet.

Include commands for:

- installing dependencies;
- starting frontend;
- starting backend;
- starting PostgreSQL;
- running all services;
- stopping services;
- applying migrations;
- creating a migration;
- running backend tests;
- running frontend tests;
- running all tests;
- linting;
- formatting;
- type checking;
- building production frontend;
- validating scenarios;
- loading seed data;
- checking the health endpoint;
- running the core engine tests;
- running a single test;
- cleaning generated development artefacts.

For every command, state:

- the directory from which it must be run;
- whether it needs a separate terminal;
- required environment variables;
- what successful output looks like.

---

# 5. Local Development Guide

Create:

```text
docs/developer/LOCAL_DEVELOPMENT.md
```

Explain:

- project directory structure;
- frontend/backend/core relationship;
- normal developer workflow;
- how hot reload works;
- how to change environment variables;
- how to reset the local database;
- how to add a lesson;
- how to add a scenario;
- how to add an environment pack;
- how to add English and French translations;
- how to inspect logs;
- how to debug API failures;
- how to debug frontend failures.

Clearly distinguish:

- commands run from repository root;
- commands run from `frontend`;
- commands run from `backend`;
- commands run from `packages/airspacesim-core`.

---

# 6. Testing Guide

Create:

```text
docs/developer/TESTING.md
```

It must explain:

- unit tests;
- integration tests;
- frontend component tests;
- end-to-end browser tests;
- scenario validation tests;
- core engine tests;
- database tests;
- authentication tests;
- manual browser testing.

Document exact commands.

## Browser testing

The guide must include a manual browser test checklist.

At minimum:

### Guest flow

- open homepage;
- switch English/French;
- open Learn;
- complete a public lesson;
- open Practice;
- complete a public scenario;
- open Simulate;
- run a solo scenario;
- confirm guest access works without sign-in.

### Authentication flow

- sign up or use documented local test account;
- sign in;
- sign out;
- refresh the page;
- confirm session persistence;
- confirm protected routes reject guests;
- confirm progress saves;
- confirm language preference saves.

### Learn flow

- Traffic Relationships journey;
- label placement;
- lesson text;
- navigation;
- English/French copy;
- no prediction metrics.

### Practice flow

- scenario loads;
- only relevant controls appear;
- commands affect the real engine;
- debrief uses scenario-specific logic.

### Simulate flow

- full interface loads;
- general separation monitoring works;
- continuous losses are not double-counted;
- factual summary appears.

### Responsive testing

Document target viewport sizes and basic checks for:

- desktop;
- tablet;
- mobile where supported.

## Automated browser tests

Where practical, use an end-to-end framework such as Playwright or the framework already present.

Do not introduce a second E2E framework without a strong reason.

---

# 7. Test Credentials

Create:

```text
docs/developer/AUTHENTICATION.md
```

Document local development authentication clearly.

Include:

- whether local sign-up is enabled;
- how to create a local test account;
- development-only seed users;
- test roles if any;
- how to reset a password locally;
- how to clear sessions;
- how authentication differs in production.

Never commit production credentials.

If development credentials are provided, they must be clearly marked as local/test-only.

Preferred pattern:

```text
Local test account
Email: demo@example.test
Password: configured through development seed or environment setup
```

Avoid hard-coding reusable passwords in public source code when safer seed or setup mechanisms are available.

If credentials are generated at setup time, document how to retrieve them.

---

# 8. Database Documentation

Create:

```text
docs/developer/DATABASE.md
```

Explain:

- PostgreSQL requirement;
- local Docker setup;
- database URL format;
- migrations;
- seed data;
- reset workflow;
- backup and restore basics;
- test database isolation;
- production migration process;
- tables at a high level.

Document destructive commands prominently.

Never suggest resetting a production database as a normal troubleshooting step.

---

# 9. Deployment Documentation

Create:

```text
docs/developer/DEPLOYMENT.md
```

It should explain:

- chosen hosting architecture;
- frontend deployment;
- backend deployment;
- PostgreSQL provisioning;
- environment variables;
- build commands;
- migration execution;
- CORS;
- custom domain;
- health checks;
- rollback;
- logs;
- deployment troubleshooting.

Clearly distinguish:

- local development;
- preview/staging;
- production.

Do not store provider secrets in documentation.

---

# 10. Troubleshooting Guide

Create:

```text
docs/developer/TROUBLESHOOTING.md
```

Include common problems such as:

- frontend cannot reach backend;
- CORS failure;
- database connection failure;
- migration failure;
- authentication callback failure;
- blank page after browser refresh;
- port already in use;
- missing environment variable;
- scenario validation error;
- failed core tests;
- stale frontend build;
- Docker service not starting.

Each issue should include:

- symptom;
- likely cause;
- diagnostic command;
- corrective action.

---

# 11. General User Documentation

Create documentation for non-technical users.

The language should be simple and task-oriented.

Do not expose internal architecture, database commands, or developer jargon in user documentation.

## User Guide

Create:

```text
docs/user/USER_GUIDE.md
```

Explain:

- what AirSpaceSim is;
- Learn, Practice, and Simulate;
- how to change language;
- guest use;
- signing in;
- saving progress;
- starting a scenario;
- using the interface;
- reading a debrief or summary;
- the non-operational-use disclaimer.

## Mode guides

Create separate concise guides:

- `LEARN_GUIDE.md`
- `PRACTICE_GUIDE.md`
- `SIMULATE_GUIDE.md`

Explain each mode in plain language.

## Account and Progress

Create:

```text
docs/user/ACCOUNT_AND_PROGRESS.md
```

Explain:

- what works without an account;
- what signing in adds;
- how progress is saved;
- how language preference is saved;
- how to sign out;
- how to request deletion later if supported.

## FAQ

Create:

```text
docs/user/FAQ.md
```

Include questions such as:

- Is AirSpaceSim an operational ATC system?
- Do I need an account?
- Why are simulation commands in English?
- Can I use the application in French?
- Are the airports and routes real?
- Can I create my own scenario?
- Does AirSpaceSim grade real ATCO competence?
- What browsers are supported?

---

# 12. Navigation and Discoverability

Documentation should be easy to navigate.

Every developer document should link back to the developer documentation index or root README.

Every user document should link back to the User Guide.

Use clear headings and relative links.

Avoid orphaned documentation files.

---

# 13. Documentation Maintenance

Documentation must be updated in the same change when any of these change:

- commands;
- ports;
- environment variables;
- authentication;
- database schema;
- migrations;
- test setup;
- deployment;
- directory structure;
- lesson authoring;
- scenario schema;
- language handling;
- user flows.

A feature is not complete if its required documentation is missing or inaccurate.

---

# 14. .gitignore Requirements

Create and maintain an appropriate root `.gitignore`.

Where useful, add package-specific `.gitignore` files, but avoid unnecessary duplication.

Ignore at minimum, where applicable:

## Python

```text
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.venv/
venv/
```

## Node and frontend

```text
node_modules/
dist/
build/
coverage/
.vite/
.next/
```

## Environment and secrets

```text
.env
.env.*
!.env.example
```

Take care not to ignore required example environment files.

## IDE and OS

```text
.vscode/
.idea/
.DS_Store
Thumbs.db
```

If selected IDE configuration is intentionally shared, whitelist only the required files.

## Logs and temporary files

```text
*.log
logs/
tmp/
temp/
```

## Database and local services

```text
*.sqlite
*.sqlite3
postgres-data/
```

Do not ignore migration files.

## Test and browser artefacts

```text
playwright-report/
test-results/
screenshots/
videos/
```

Keep deliberately committed test fixtures.

## Generated content

Ignore generated caches, exports, and local artefacts, but do not ignore canonical scenario, environment, translation, migration, or documentation files.

Review `.gitignore` whenever new tools are introduced.

---

# 15. Repository Cleanliness

Do not commit:

- production secrets;
- personal credentials;
- local database files;
- generated logs;
- test videos;
- coverage output;
- dependency folders;
- editor caches;
- build artefacts;
- temporary exports;
- machine-specific paths.

Do commit:

- `.env.example`;
- migration files;
- canonical scenarios;
- canonical environment packs;
- translation resources;
- test fixtures;
- documentation;
- lock files where appropriate;
- scripts required to reproduce setup.

---

# 16. Developer Experience Acceptance Criteria

A developer unfamiliar with the repository should be able to:

1. clone the repository;
2. read the root README;
3. identify required software;
4. create environment files;
5. start PostgreSQL;
6. apply migrations;
7. start backend and frontend;
8. know which commands require separate terminals;
9. open the correct browser URL;
10. sign in using a documented local test process;
11. run automated tests;
12. perform the browser test checklist;
13. understand where the engine, app, content, and documentation live;
14. stop and restart the system;
15. troubleshoot common failures.

They should not need to infer missing commands from source code.

---

# 17. General User Documentation Acceptance Criteria

A non-technical user should be able to understand:

- what the product does;
- the difference between Learn, Practice, and Simulate;
- how to use guest mode;
- how to sign in;
- why operational commands are English;
- how to switch the rest of the interface to French;
- how to start and finish a lesson or scenario;
- what a debrief means;
- that the product is not for operational control.

The user guide should not require command-line knowledge.
