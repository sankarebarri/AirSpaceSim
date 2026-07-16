#!/usr/bin/env python3
"""Smoke-test a hosted AirSpaceSim API and optional web frontend."""

from __future__ import annotations

import argparse
import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# The API scopes run/scenario listings to a client-generated session id (see
# apps/api/app/session_identity.py). Any valid id works for a read-only smoke
# check since it only needs a session-scoped list to come back successfully.
SESSION_ID = str(uuid.uuid4())


def _request_json(url: str) -> dict:
    request = Request(
        url,
        headers={"Accept": "application/json", "X-Airspacesim-Session": SESSION_ID},
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} while calling {url}\n{body}") from exc
    except URLError as exc:
        raise SystemExit(f"Could not reach {url}: {exc.reason}") from exc


def _request_text(url: str) -> str:
    request = Request(url, headers={"Accept": "text/html,*/*"})
    try:
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} while calling {url}\n{body}") from exc
    except URLError as exc:
        raise SystemExit(f"Could not reach {url}: {exc.reason}") from exc


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test hosted AirSpaceSim.")
    parser.add_argument(
        "--api-base-url",
        default="http://127.0.0.1:8000",
        help="Base URL for the FastAPI service.",
    )
    parser.add_argument(
        "--web-base-url",
        help="Optional base URL for the deployed web frontend.",
    )
    args = parser.parse_args()

    api_base_url = args.api_base_url.rstrip("/")
    health = _request_json(f"{api_base_url}/health")
    _expect(health.get("status") == "ok", "API health status is not ok.")
    _expect(health.get("database") == "ok", "API database readiness is not ok.")

    airspaces = _request_json(f"{api_base_url}/api/v1/airspaces")
    _expect(isinstance(airspaces.get("items"), list), "Airspaces response is invalid.")
    _expect(len(airspaces["items"]) >= 1, "No airspace packages were discovered.")

    runs = _request_json(f"{api_base_url}/api/v1/runs")
    _expect(isinstance(runs.get("items"), list), "Runs response is invalid.")

    if args.web_base_url:
        web_base_url = args.web_base_url.rstrip("/")
        html = _request_text(web_base_url)
        _expect("AirSpaceSim" in html, "Web frontend did not return AirSpaceSim HTML.")

    print("Hosted AirSpaceSim smoke test passed.")
    print(f"API: {api_base_url}")
    print(f"Airspaces: {len(airspaces['items'])}")
    if args.web_base_url:
        print(f"Web: {args.web_base_url.rstrip('/')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
