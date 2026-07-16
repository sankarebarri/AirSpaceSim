import asyncio
import threading
import time
from queue import Empty

import pytest
from fastapi import WebSocketDisconnect

from app.api.v1.routes.runs import create_run_route, stream_run
from app.api.v1.routes.scenarios import create_scenario_route
from app.db.session import get_session_factory
from app.schemas.runs import RunCreateRequest
from app.schemas.scenarios import ScenarioCreateRequest
from app.sessions import SessionRegistry
from app.ws import BroadcastHub

SESSION_ID = "test-session-a"


class FakeWebSocket:
    def __init__(self, *, disconnect_after: int | None = None) -> None:
        self.disconnect_after = disconnect_after
        self.accepted = False
        self.close_code: int | None = None
        self.messages: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int) -> None:
        self.close_code = code

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)
        if (
            self.disconnect_after is not None
            and len(self.messages) >= self.disconnect_after
        ):
            raise WebSocketDisconnect(code=1000)

    async def wait_until_accepted(self) -> None:
        async def _wait() -> None:
            while not self.accepted:
                await asyncio.sleep(0.01)

        await asyncio.wait_for(_wait(), timeout=1.0)

    async def wait_for_message_count(self, count: int) -> None:
        async def _wait() -> None:
            while len(self.messages) < count:
                await asyncio.sleep(0.01)

        await asyncio.wait_for(_wait(), timeout=2.0)


def start_async_in_thread(coro_factory) -> tuple[threading.Thread, dict[str, BaseException | None]]:
    outcome: dict[str, BaseException | None] = {"error": None}

    def target() -> None:
        try:
            asyncio.run(coro_factory())
        except BaseException as exc:  # pragma: no cover - re-raised below
            outcome["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread, outcome


def finish_async_thread(
    thread: threading.Thread,
    outcome: dict[str, BaseException | None],
) -> None:
    thread.join(timeout=5.0)
    assert not thread.is_alive(), "async websocket test timed out"
    if outcome["error"] is not None:
        raise outcome["error"]


def wait_until(predicate, *, timeout_seconds: float = 2.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError("condition did not become true before timeout")
        time.sleep(0.01)


def test_broadcast_hub_publish_delivers_to_run_subscribers():
    hub = BroadcastHub()
    subscriber = hub.subscribe("run-123")

    hub.publish_state("run-123", {"runtime_status": "running"})

    event = subscriber.queue.get_nowait()
    assert event["type"] == "run_state.updated"
    assert event["run_id"] == "run-123"
    assert event["data"]["runtime_status"] == "running"

    hub.unsubscribe(subscriber)
    hub.publish_state("run-123", {"runtime_status": "stopped"})

    with pytest.raises(Empty):
        subscriber.queue.get_nowait()


def test_stream_run_closes_missing_run_with_4404(
    db_session,
    broadcast_hub,
):
    session_registry = SessionRegistry(update_interval_seconds=0.01, broadcast_hub=broadcast_hub)
    websocket = FakeWebSocket()
    session_factory = get_session_factory()

    async def stream_flow() -> None:
        stream_session = session_factory()
        try:
            await stream_run(
                websocket,
                "missing-run",
                stream_session,
                session_registry,
                broadcast_hub,
                SESSION_ID,
            )
        finally:
            stream_session.close()

    thread, outcome = start_async_in_thread(stream_flow)

    try:
        finish_async_thread(thread, outcome)
    finally:
        session_registry.shutdown()

    assert websocket.accepted is False
    assert websocket.close_code == 4404
    assert websocket.messages == []


def test_stream_run_sends_initial_snapshot_and_runtime_update(
    db_session,
    broadcast_hub,
):
    scenario = create_scenario_route(
        ScenarioCreateRequest(name="WebSocket Scenario"),
        db_session,
        SESSION_ID,
    )
    created_run = create_run_route(
        RunCreateRequest(scenario_id=scenario.id, name="WebSocket Run"),
        db_session,
        SESSION_ID,
    )
    session_registry = SessionRegistry(
        update_interval_seconds=0.01,
        broadcast_hub=broadcast_hub,
    )
    websocket = FakeWebSocket(disconnect_after=2)
    session_factory = get_session_factory()

    async def run_stream_flow() -> None:
        stream_session = session_factory()
        try:
            await stream_run(
                websocket,
                created_run.id,
                stream_session,
                session_registry,
                broadcast_hub,
                SESSION_ID,
            )
        finally:
            stream_session.close()

    thread, outcome = start_async_in_thread(run_stream_flow)

    try:
        wait_until(lambda: websocket.accepted)
        wait_until(lambda: len(websocket.messages) >= 1)
        broadcast_hub.publish_state(
            created_run.id,
            {
                "runtime_status": "running",
                "sim_rate": 1.0,
                "updated_utc": "2026-05-11T21:00:00Z",
                "last_error": None,
                "aircraft": [],
                "metrics": {
                    "aircraft_count": 0,
                    "active_aircraft_count": 0,
                    "finished_aircraft_count": 0,
                },
            },
        )
        finish_async_thread(thread, outcome)
    finally:
        session_registry.shutdown()

    assert websocket.accepted is True
    assert len(websocket.messages) == 2
    assert websocket.messages[0]["type"] == "run_state.snapshot"
    assert websocket.messages[0]["data"]["run"]["id"] == created_run.id
    assert websocket.messages[0]["data"]["runtime_status"] == "inactive"
    assert websocket.messages[1]["type"] == "run_state.updated"
    assert websocket.messages[1]["run_id"] == created_run.id
    assert websocket.messages[1]["data"]["runtime_status"] == "running"
    assert websocket.messages[1]["data"]["updated_utc"] == "2026-05-11T21:00:00Z"


def test_stream_run_sends_command_result_events(
    db_session,
    broadcast_hub,
):
    created_run = create_run_route(RunCreateRequest(name="Queued Run"), db_session, SESSION_ID)
    session_registry = SessionRegistry(
        update_interval_seconds=0.01,
        broadcast_hub=broadcast_hub,
    )
    websocket = FakeWebSocket(disconnect_after=2)
    session_factory = get_session_factory()

    async def run_stream_flow() -> None:
        stream_session = session_factory()
        try:
            await stream_run(
                websocket,
                created_run.id,
                stream_session,
                session_registry,
                broadcast_hub,
                SESSION_ID,
            )
        finally:
            stream_session.close()

    thread, outcome = start_async_in_thread(run_stream_flow)

    try:
        wait_until(lambda: websocket.accepted)
        wait_until(lambda: len(websocket.messages) >= 1)
        broadcast_hub.publish_command_result(
            created_run.id,
            {
                "command": {
                    "id": "cmd-123",
                    "run_id": created_run.id,
                    "command_type": "ADD_AIRCRAFT",
                    "status": "queued",
                    "payload": {"id": "AC990", "route": "UA612"},
                    "created_at": "2026-05-11T21:05:00Z",
                    "applied_at": None,
                },
                "result": {
                    "state": "queued",
                    "applied": [],
                    "skipped": [],
                    "rejected": [],
                },
            },
        )
        finish_async_thread(thread, outcome)
    finally:
        session_registry.shutdown()

    assert websocket.accepted is True
    assert len(websocket.messages) == 2
    assert websocket.messages[1]["type"] == "run_command.result"
    assert websocket.messages[1]["data"]["command"]["run_id"] == created_run.id
    assert websocket.messages[1]["data"]["result"]["state"] == "queued"
