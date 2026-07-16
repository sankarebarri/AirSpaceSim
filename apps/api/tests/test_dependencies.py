from fastapi import WebSocket
from starlette.requests import HTTPConnection, Request

from app.dependencies import (
    get_broadcast_hub_dependency,
    get_session_registry_dependency,
)
from app.main import create_app


async def _no_receive():
    return {"type": "http.request", "body": b"", "more_body": False}


async def _no_send(_message):
    return None


def test_shared_connection_dependencies_accept_request_objects():
    app = create_app()
    request = Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/v1/runs",
            "raw_path": b"/api/v1/runs",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 8000),
            "state": {},
            "app": app,
            "path_params": {},
        }
    )

    assert isinstance(request, HTTPConnection)
    assert get_session_registry_dependency(request) is app.state.session_registry
    assert get_broadcast_hub_dependency(request) is app.state.broadcast_hub


def test_shared_connection_dependencies_accept_websocket_objects():
    app = create_app()
    websocket = WebSocket(
        {
            "type": "websocket",
            "asgi": {"version": "3.0"},
            "scheme": "ws",
            "path": "/api/v1/runs/test-run/stream",
            "raw_path": b"/api/v1/runs/test-run/stream",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 8000),
            "subprotocols": [],
            "state": {},
            "app": app,
            "path_params": {"run_id": "test-run"},
        },
        receive=_no_receive,
        send=_no_send,
    )

    assert isinstance(websocket, HTTPConnection)
    assert get_session_registry_dependency(websocket) is app.state.session_registry
    assert get_broadcast_hub_dependency(websocket) is app.state.broadcast_hub
