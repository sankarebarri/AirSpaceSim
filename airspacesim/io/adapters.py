"""Snapshot and event adapters for ingestion/runtime I/O."""

import json
import os
import sys
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime

from airspacesim.io.contracts import validate_inbox_events


def _sort_event_key(event):
    created = event.get("created_utc", "")
    sequence = event.get("sequence", 0)
    try:
        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
    except ValueError:
        created_dt = datetime.min
    return (sequence, created_dt, event.get("event_id", ""))


def _atomic_write(path, payload):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".airspacesim.", suffix=".tmp", dir=directory or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(payload, tmp, indent=4)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


class FileSnapshotAdapter:
    """Load/save a JSON snapshot file, with optional validation callback."""

    def __init__(self, path, validator=None):
        self.path = path
        self.validator = validator

    def load(self):
        with open(self.path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        if self.validator:
            self.validator(payload)
        return payload

    def save(self, payload):
        if self.validator:
            self.validator(payload)
        _atomic_write(self.path, payload)


class EventIngestionAdapter(ABC):
    """Common adapter interface for event ingestion sources."""

    @abstractmethod
    def poll(self):
        """Return a deterministically ordered list of fresh events."""

    def ack(self, event_ids=None):
        """Optional acknowledgment hook for adapters with checkpoints."""
        return None


def _extract_events(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("events"), list):
        return payload["data"]["events"]
    if isinstance(payload.get("events"), list):
        return payload["events"]
    if "event_id" in payload and "type" in payload:
        return [payload]
    return []


class FileEventAdapter(EventIngestionAdapter):
    """Read canonical event files and return idempotent ordered events."""

    def __init__(self, path, validator=validate_inbox_events, auto_ack=True):
        self.path = path
        self.validator = validator
        self.auto_ack = auto_ack
        self._seen_event_ids = set()
        self._pending_events = []

    def poll(self):
        with open(self.path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        if self.validator:
            self.validator(payload)

        events = _extract_events(payload)
        fresh_events = []
        for event in sorted(events, key=_sort_event_key):
            event_id = event["event_id"]
            if event_id in self._seen_event_ids:
                continue
            fresh_events.append(event)
        self._pending_events = fresh_events
        if self.auto_ack:
            self.ack([event.get("event_id") for event in fresh_events])
        return fresh_events

    def ack(self, event_ids=None):
        if event_ids is None:
            event_ids = [event.get("event_id") for event in self._pending_events]
        for event_id in event_ids:
            if isinstance(event_id, str) and event_id:
                self._seen_event_ids.add(event_id)
        self._pending_events = []


class StdinEventAdapter(EventIngestionAdapter):
    """
    Consume newline-delimited JSON events from stdin-like streams.

    Accepted line payloads:
    - canonical envelope with data.events
    - {"events":[...]}
    - single event object
    """

    def __init__(self, stream=None):
        self.stream = stream if stream is not None else sys.stdin
        self._seen_event_ids = set()
        self._pending_events = []

    def poll(self):
        events = []
        while True:
            line = self.stream.readline()
            if line == "":
                break
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            events.extend(_extract_events(payload))

        fresh_events = []
        for event in sorted(events, key=_sort_event_key):
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id:
                continue
            if event_id in self._seen_event_ids:
                continue
            fresh_events.append(event)

        self._pending_events = fresh_events
        return fresh_events

    def ack(self, event_ids=None):
        if event_ids is None:
            event_ids = [event.get("event_id") for event in self._pending_events]
        for event_id in event_ids:
            if isinstance(event_id, str) and event_id:
                self._seen_event_ids.add(event_id)
        self._pending_events = []
