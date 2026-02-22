#!/usr/bin/env python3
"""
dev_server.py - Framework-agnostic dev server for AirSpaceSim.

Serves static files (templates/, static/, data/) and accepts POST /api/events
to write operator commands into data/inbox_events.v1.json for the simulation
loop to consume via run_inbox_events_loop().

Zero external dependencies — uses Python stdlib only.
"""

import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

PORT = int(os.environ.get("AIRSPACESIM_PORT", "8080"))
ROOT = Path.cwd()  # Serve from the directory you run this script in.

def _detect_default_map_path(root: Path) -> str:
    playground_map = root / "airspacesim-playground" / "templates" / "map.html"
    if playground_map.exists():
        return "airspacesim-playground/templates/map.html"
    return "templates/map.html"


DEFAULT_MAP_PATH = _detect_default_map_path(ROOT)


def _workspace_looks_valid(root: Path) -> bool:
    direct_layout = (
        (root / "templates" / "map.html").exists()
        and (root / "static" / "js" / "aircraft_simulation.js").exists()
    )
    playground_layout = (
        (root / "airspacesim-playground" / "templates" / "map.html").exists()
        and (root / "airspacesim-playground" / "static" / "js" / "aircraft_simulation.js").exists()
    )
    return direct_layout or playground_layout


if not _workspace_looks_valid(ROOT):
    print("⚠️  WARNING: Run dev_server.py from a workspace root containing templates/static/data.")
    print(f"   Current working directory: {ROOT}")
    print()

INBOX_EVENTS_PATH = ROOT / "data" / "inbox_events.v1.json"
_write_lock = threading.Lock()

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".airspacesim.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class AirSpaceSimHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: N802
        print(f"  {self.address_string()} {fmt % args}")

    def _send_json(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):  # noqa: N802
        # Strip query string for file resolution.
        path = self.path.split("?")[0].lstrip("/") or DEFAULT_MAP_PATH
        file_path = ROOT / path
        if not file_path.exists() or not file_path.is_file():
            self._send_json(404, {"error": f"Not found: {path}"})
            return
        suffix = file_path.suffix.lower()
        mime = MIME_TYPES.get(suffix, "application/octet-stream")
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):  # noqa: N802
        request_path = self.path.split("?")[0].rstrip("/")
        if not request_path.endswith("/api/events"):
            self._send_json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": f"Invalid JSON: {exc}"})
            return

        # Extract events list from the envelope.
        new_events = payload.get("data", {}).get("events", [])
        if not isinstance(new_events, list):
            self._send_json(400, {"error": "payload.data.events must be a list"})
            return

        print(f"[EVENT SINK] received batch with {len(new_events)} event(s)")
        for event in new_events:
            event_id = event.get("event_id")
            event_type = event.get("type")
            event_payload = event.get("payload")
            print(
                f"[EVENT SINK] event_id={event_id} type={event_type} payload={event_payload}"
            )

        with _write_lock:
            inbox_path = self._resolve_inbox_path(request_path)
            try:
                existing = json.loads(inbox_path.read_text(encoding="utf-8"))
                current_events = existing.get("data", {}).get("events", [])
            except (FileNotFoundError, json.JSONDecodeError):
                current_events = []

            merged = {
                **payload,
                "data": {"events": current_events + new_events},
            }
            _atomic_write_json(inbox_path, merged)

        print(f"[EVENT SINK] wrote to {inbox_path}")
        self._send_json(200, {"accepted": len(new_events), "target": str(inbox_path)})

    def _resolve_inbox_path(self, request_path: str) -> Path:
        """Resolve target inbox path using request context to avoid root/playground leaks."""
        if request_path.startswith("/airspacesim-playground/"):
            if ROOT.name == "airspacesim-playground":
                return ROOT / "data" / "inbox_events.v1.json"
            candidate = ROOT / "airspacesim-playground" / "data" / "inbox_events.v1.json"
            if candidate.parent.exists():
                return candidate

        referer = self.headers.get("Referer", "")
        referer_path = urlparse(referer).path

        # Case 1: serving from repo root but UI page under /airspacesim-playground/...
        if "/airspacesim-playground/" in referer_path:
            candidate = ROOT / "airspacesim-playground" / "data" / "inbox_events.v1.json"
            if candidate.parent.exists():
                return candidate

        # Case 2: running server directly from airspacesim-playground directory.
        if ROOT.name == "airspacesim-playground":
            candidate = ROOT / "data" / "inbox_events.v1.json"
            if candidate.parent.exists():
                return candidate

        # Default: root data directory.
        return INBOX_EVENTS_PATH


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), AirSpaceSimHandler)
    print("\n🛫  AirSpaceSim dev server")
    print(f"    Map  →  http://127.0.0.1:{PORT}/{DEFAULT_MAP_PATH}")
    if DEFAULT_MAP_PATH != "templates/map.html" and (ROOT / "templates" / "map.html").exists():
        print(f"    Alt  →  http://127.0.0.1:{PORT}/templates/map.html")
    print(f"    POST →  http://127.0.0.1:{PORT}/api/events")
    print(f"    POST →  http://127.0.0.1:{PORT}/airspacesim-playground/api/events")
    print("    Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
