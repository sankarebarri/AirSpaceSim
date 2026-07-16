"""Thread-safe broadcast hub for run-scoped live updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from queue import Empty, Full, Queue
from threading import Lock
from typing import Any
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RunStreamSubscriber:
    """Queue-backed subscriber handle for one run stream."""

    run_id: str
    subscriber_id: str
    queue: Queue[dict[str, Any]]


class BroadcastHub:
    """Manage per-run subscribers and thread-safe event fanout."""

    def __init__(self, queue_size: int = 32) -> None:
        self.queue_size = max(int(queue_size), 1)
        self._subscribers: dict[str, dict[str, Queue[dict[str, Any]]]] = {}
        self._lock = Lock()

    def subscribe(self, run_id: str) -> RunStreamSubscriber:
        subscriber_id = str(uuid4())
        queue: Queue[dict[str, Any]] = Queue(maxsize=self.queue_size)
        with self._lock:
            self._subscribers.setdefault(run_id, {})[subscriber_id] = queue
        return RunStreamSubscriber(
            run_id=run_id,
            subscriber_id=subscriber_id,
            queue=queue,
        )

    def unsubscribe(self, subscriber: RunStreamSubscriber) -> None:
        with self._lock:
            run_subscribers = self._subscribers.get(subscriber.run_id)
            if not run_subscribers:
                return
            run_subscribers.pop(subscriber.subscriber_id, None)
            if not run_subscribers:
                self._subscribers.pop(subscriber.run_id, None)

    def publish(self, run_id: str, event: dict[str, Any]) -> None:
        with self._lock:
            subscribers = list(self._subscribers.get(run_id, {}).values())
        for subscriber_queue in subscribers:
            try:
                subscriber_queue.put_nowait(event)
            except Full:
                try:
                    subscriber_queue.get_nowait()
                except Empty:
                    pass
                subscriber_queue.put_nowait(event)

    def publish_state(self, run_id: str, state_snapshot: dict[str, Any]) -> None:
        self.publish(
            run_id,
            {
                "type": "run_state.updated",
                "run_id": run_id,
                "emitted_at": _utc_now_iso(),
                "data": state_snapshot,
            },
        )

    def publish_command_result(
        self,
        run_id: str,
        command_result: dict[str, Any],
    ) -> None:
        self.publish(
            run_id,
            {
                "type": "run_command.result",
                "run_id": run_id,
                "emitted_at": _utc_now_iso(),
                "data": command_result,
            },
        )
