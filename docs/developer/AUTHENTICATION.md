# Authentication (Developer Guide)

AirSpaceSim uses **email + password with secure server-side sessions**
(decision Q7 in `docs/repository-audit/08_OPEN_QUESTIONS.md`). Guests keep
full access to public Learn, Practice, and solo Simulate; signing in adds
persistence only.

## How it works

- Passwords are hashed with stdlib **scrypt** (salted, parameters stored per
  hash) — see `apps/api/app/security.py`.
- On login/register the API creates an `auth_sessions` row and sets an
  **opaque token** in an `HttpOnly`, `SameSite=Lax` cookie
  (`airspacesim_session`). Only the SHA-256 hash of the token is stored.
  In production (`AIRSPACESIM_API_ENVIRONMENT=production`) the cookie is
  also `Secure`.
- Sessions expire after `AIRSPACESIM_API_AUTH_SESSION_TTL_DAYS` (default 30).
- **Guest adoption**: when a signed-out browser session (identified by the
  `X-Airspacesim-Session` header) logs in or registers, its anonymous runs
  and scenarios are attached to the account, so nothing is lost.
- Protected persistence routes (`/api/v1/progress`, `PATCH /api/v1/auth/me`)
  reject guests with 401. Run/scenario routes stay guest-accessible and
  additionally show account-owned records when signed in.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Create account + sign in (min 8-char password) |
| POST | `/api/v1/auth/login` | Sign in |
| POST | `/api/v1/auth/logout` | Revoke session, clear cookie |
| GET | `/api/v1/auth/me` | Current user (401 for guests) |
| PATCH | `/api/v1/auth/me` | Update display name / preferred language |
| GET/PUT | `/api/v1/progress` | Lesson progress (signed-in only) |

## Local test account

Create a development-only account (local/test use only — never run against
production):

```bash
# from the repository root, with the API venv active
python3 scripts/seed_dev_user.py
# -> prints: demo@example.test + a generated password
```

Pass `--email` / `--password` to control the values. To "reset a password"
locally, delete the row from `users` (or the SQLite file under
`apps/api/var/`) and re-seed. Clearing all sessions: delete rows from
`auth_sessions`.

## CORS and cookies

Cookie auth requires credentialed CORS: `cors_allow_credentials=true` and
**explicit origins** (the `*` wildcard is impossible with credentials).
Development defaults cover the local Vite ports; production startup fails
unless `AIRSPACESIM_API_CORS_ALLOWED_ORIGINS` is set to explicit
non-localhost origins. The frontend sends `credentials: "include"` on all
API requests.

## Retention of anonymous data (decision Q10)

Anonymous (guest) runs that have been stopped for more than
`AIRSPACESIM_API_ANONYMOUS_RUN_RETENTION_DAYS` (default **14**) are deleted
by a background sweep (`apps/api/app/services/retention.py`), together with
orphaned practice scenarios. Account-owned history is never pruned.
