# PostgreSQL, authentication, and deployment

## PostgreSQL

Use PostgreSQL for hosted persistence.

Initial models:

### users

- id
- email
- display_name nullable
- preferred_language
- created_at
- updated_at

### concepts

- id
- slug
- service
- family
- difficulty
- status
- metadata_json

### environments

- id
- slug
- name
- environment_type
- current_version_id

### environment_versions

- id
- environment_id
- version
- definition_json
- created_at

### scenarios

- id
- slug
- mode
- concept_id nullable
- current_version_id
- is_public
- owner_user_id nullable

### scenario_versions

- id
- scenario_id
- version
- definition_json
- created_at

### learning_progress

- id
- user_id
- concept_id
- stage_key
- status
- updated_at

### simulation_runs

- id
- user_id nullable
- scenario_version_id
- environment_version_id
- started_at
- completed_at nullable
- status
- summary_json
- deterministic_seed nullable

### run_events

Store only meaningful events when needed, not every frame.

## Authentication

Implement only:

- sign in;
- sign out;
- current user;
- protected persistence routes;
- optional display name;
- preferred language;
- safe token or session handling.

Do not implement organisations, billing, instructor roles, or complex RBAC yet.

Guests may use public Learn, Practice, and solo Simulate and receive immediate debriefs. Signed-in users receive persistent progress, history, preferences, and saved scenarios.

## Deployment preparation

Provide `.env.example` with:

```text
ENVIRONMENT=
DATABASE_URL=
SECRET_KEY=
ALLOWED_ORIGINS=
FRONTEND_URL=
API_BASE_URL=
AUTH_REDIRECT_URL=
LOG_LEVEL=
```

Backend requirements:

- `/health`;
- database migrations;
- production error handling;
- structured logging;
- CORS configuration;
- failure on missing required production secrets.

Frontend requirements:

- API URL from environment;
- no production dependency on localhost;
- correct SPA route fallback;
- production build;
- useful loading, empty, and error states.

The public site may state:

> Training and visualisation software. Not for operational use.
