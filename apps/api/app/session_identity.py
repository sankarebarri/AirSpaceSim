"""Anonymous session identity for scoping durable data per browser client.

There is no login/accounts model yet. Each client generates its own id
(a UUID created client-side) and sends it back on every request; the server
never issues or tracks session state itself, it only validates shape and
uses the value as a scoping key for runs/scenarios.
"""

from __future__ import annotations

import re

from fastapi import HTTPException, status
from starlette.requests import HTTPConnection

SESSION_HEADER_NAME = "X-Airspacesim-Session"
SESSION_QUERY_PARAM = "sid"

_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def get_session_id(connection: HTTPConnection) -> str:
    """Resolve and validate the caller's client-generated session id.

    Works for both HTTP requests and WebSocket connections since both
    share the Starlette `HTTPConnection` base (same pattern used by
    `get_session_registry_dependency` in `dependencies.py`).
    """

    candidate = connection.headers.get(SESSION_HEADER_NAME) or connection.query_params.get(
        SESSION_QUERY_PARAM
    )
    if not candidate or not _SESSION_ID_PATTERN.match(candidate):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Missing or invalid {SESSION_HEADER_NAME} header "
                f"(or '{SESSION_QUERY_PARAM}' query parameter)."
            ),
        )
    return candidate
