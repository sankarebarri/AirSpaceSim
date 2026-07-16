"""Framework-agnostic dev server for AirSpaceSim workspaces."""

import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

PORT = int(os.environ.get("AIRSPACESIM_PORT", "8080"))
PLAYGROUND_SUBDIR = "airspacesim-playground"
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def _playground_inbox_path(root: Path) -> Path:
    if root.name == PLAYGROUND_SUBDIR:
        return root / "data" / "inbox_events.v1.json"
    return root / PLAYGROUND_SUBDIR / "data" / "inbox_events.v1.json"


def _playground_available(root: Path) -> bool:
    return _playground_inbox_path(root).parent.exists()


def _detect_default_map_path(root: Path) -> str:
    playground_map = root / PLAYGROUND_SUBDIR / "templates" / "map.html"
    if playground_map.exists():
        return f"{PLAYGROUND_SUBDIR}/templates/map.html"
    return "templates/map.html"


def _workspace_looks_valid(root: Path) -> bool:
    direct_layout = (
        (root / "templates" / "map.html").exists()
        and (root / "static" / "js" / "aircraft_simulation.js").exists()
    )
    playground_layout = (
        (root / PLAYGROUND_SUBDIR / "templates" / "map.html").exists()
        and (
            root / PLAYGROUND_SUBDIR / "static" / "js" / "aircraft_simulation.js"
        ).exists()
    )
    return direct_layout or playground_layout


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".airspacesim.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def create_handler(root: Path):
    default_map_path = _detect_default_map_path(root)
    inbox_events_path = root / "data" / "inbox_events.v1.json"
    write_lock = threading.Lock()

    def resolve_get_target(path: str) -> str:
        """
        Resolve request path with workspace-safe aliases.

        If this repository has an `airspacesim-playground/` workspace, force
        `/airspacesim/{templates,static,data}/...` to serve from playground files.
        This prevents UI/runtime leaks to package seed files.
        """
        normalized = path.lstrip("/")
        if not normalized:
            return default_map_path
        if not _playground_available(root):
            return normalized
        if not normalized.startswith("airspacesim/"):
            return normalized
        relative = normalized.removeprefix("airspacesim/")
        if not (
            relative.startswith("templates/")
            or relative.startswith("static/")
            or relative.startswith("data/")
        ):
            return normalized
        candidate = f"{PLAYGROUND_SUBDIR}/{relative}"
        if (root / candidate).exists():
            return candidate
        return normalized

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
            raw_path = self.path.split("?")[0]
            path = resolve_get_target(raw_path)
            file_path = root / path
            if not file_path.exists() or not file_path.is_file():
                self._send_json(404, {"error": f"Not found: {path}"})
                return
            mime = MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream")
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

            new_events = payload.get("data", {}).get("events", [])
            if not isinstance(new_events, list):
                self._send_json(400, {"error": "payload.data.events must be a list"})
                return

            print(f"[EVENT SINK] received batch with {len(new_events)} event(s)")
            for event in new_events:
                print(
                    "[EVENT SINK] event_id=%s type=%s payload=%s"
                    % (
                        event.get("event_id"),
                        event.get("type"),
                        event.get("payload"),
                    )
                )

            with write_lock:
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
            self._send_json(
                200, {"accepted": len(new_events), "target": str(inbox_path)}
            )

        def _resolve_inbox_path(self, request_path: str) -> Path:
            """Resolve the inbox target without leaking repo-root paths into workspaces."""
            if request_path.startswith(f"/{PLAYGROUND_SUBDIR}/"):
                candidate = _playground_inbox_path(root)
                if candidate.parent.exists():
                    return candidate

            if request_path.startswith("/airspacesim/"):
                candidate = _playground_inbox_path(root)
                if candidate.parent.exists():
                    return candidate

            referer_path = urlparse(self.headers.get("Referer", "")).path
            if f"/{PLAYGROUND_SUBDIR}/" in referer_path or "/airspacesim/" in referer_path:
                candidate = _playground_inbox_path(root)
                if candidate.parent.exists():
                    return candidate

            if root.name == PLAYGROUND_SUBDIR:
                candidate = _playground_inbox_path(root)
                if candidate.parent.exists():
                    return candidate

            return inbox_events_path

    return AirSpaceSimHandler, default_map_path


def main():
    root = Path.cwd()
    if not _workspace_looks_valid(root):
        print(
            "WARNING: Run dev_server.py from a workspace root containing templates/static/data."
        )
        print(f"Current working directory: {root}")
        print()

    handler, default_map_path = create_handler(root)
    server = HTTPServer(("127.0.0.1", PORT), handler)
    print("\nAirSpaceSim dev server")
    print(f"  Map  ->  http://127.0.0.1:{PORT}/{default_map_path}")
    if (
        default_map_path != "templates/map.html"
        and (root / "templates" / "map.html").exists()
    ):
        print(f"  Alt  ->  http://127.0.0.1:{PORT}/templates/map.html")
    print(f"  POST ->  http://127.0.0.1:{PORT}/api/events")
    print(f"  POST ->  http://127.0.0.1:{PORT}/{PLAYGROUND_SUBDIR}/api/events")
    print("  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
