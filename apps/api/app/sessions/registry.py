"""Registry for in-memory simulation runtime sessions."""

from __future__ import annotations

import logging
import threading
import time

from sqlalchemy.orm import Session, sessionmaker

from ..db.models import RunCheckpointRecord, RunRecord, ScenarioRecord
from ..db.repositories import RunCheckpointRepository
from ..db.session import get_session_factory
from ..services.scenarios import resolve_scenario_contracts
from ..ws import BroadcastHub
from .runtime import SimulationRuntimeSession


logger = logging.getLogger(__name__)


class SessionRegistry:
    """Track and manage runtime sessions keyed by run id."""

    def __init__(
        self,
        update_interval_seconds: float = 0.25,
        checkpoint_interval_seconds: float = 1.0,
        checkpoint_retention_per_run: int = 25,
        broadcast_hub: BroadcastHub | None = None,
        session_factory: sessionmaker[Session] | None = None,
    ) -> None:
        self.update_interval_seconds = max(float(update_interval_seconds), 0.05)
        self.checkpoint_interval_seconds = max(
            float(checkpoint_interval_seconds),
            0.25,
        )
        self.checkpoint_retention_per_run = max(int(checkpoint_retention_per_run), 1)
        self.broadcast_hub = broadcast_hub
        self.session_factory = session_factory or get_session_factory()
        self._sessions: dict[str, SimulationRuntimeSession] = {}
        self._lock = threading.Lock()
        self._checkpoint_lock = threading.Lock()
        self._last_checkpoint_at: dict[str, float] = {}

    def get(self, run_id: str) -> SimulationRuntimeSession | None:
        with self._lock:
            return self._sessions.get(run_id)

    def list_sessions(self) -> list[SimulationRuntimeSession]:
        with self._lock:
            return list(self._sessions.values())

    def start(
        self,
        *,
        run: RunRecord,
        scenario: ScenarioRecord | None,
    ) -> SimulationRuntimeSession:
        with self._lock:
            session = self._sessions.get(run.id)
            if session is None:
                scenario_airspace, scenario_aircraft = resolve_scenario_contracts(
                    scenario
                )
                session = SimulationRuntimeSession(
                    run_id=run.id,
                    scenario_airspace=scenario_airspace,
                    scenario_aircraft=scenario_aircraft,
                    sim_rate=run.sim_rate,
                    update_interval_seconds=self.update_interval_seconds,
                    state_publisher=self._publish_state,
                    metadata_payload=(
                        scenario.metadata_payload if scenario is not None else None
                    ),
                )
                self._sessions[run.id] = session
        session.start()
        return session

    def pause(self, run_id: str) -> SimulationRuntimeSession | None:
        session = self.get(run_id)
        if session is not None:
            session.pause()
        return session

    def resume(self, run_id: str) -> SimulationRuntimeSession | None:
        session = self.get(run_id)
        if session is not None:
            session.resume()
        return session

    def stop(self, run_id: str) -> SimulationRuntimeSession | None:
        session = self.get(run_id)
        if session is not None:
            session.stop()
            self._discard_session(run_id)
        return session

    def shutdown(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
        for session in sessions:
            session.stop()
            self._discard_session(session.run_id)

    def _publish_state(
        self,
        run_id: str,
        snapshot: dict,
        checkpoint_type: str,
    ) -> None:
        if self.broadcast_hub is not None:
            self.broadcast_hub.publish_state(run_id, snapshot)
        if checkpoint_type in {"stopped", "completed", "error"}:
            try:
                self._persist_run_summary(run_id, snapshot)
            except Exception:
                logger.exception(
                    "Failed to persist run summary",
                    extra={"run_id": run_id, "checkpoint_type": checkpoint_type},
                )
        if not self._should_persist_checkpoint(run_id, checkpoint_type):
            if checkpoint_type in {"completed", "error"}:
                self._discard_session(run_id)
            return
        try:
            self._persist_checkpoint(run_id, snapshot, checkpoint_type)
        except Exception:
            logger.exception(
                "Failed to persist run checkpoint",
                extra={
                    "run_id": run_id,
                    "checkpoint_type": checkpoint_type,
                },
            )
        finally:
            if checkpoint_type in {"completed", "error"}:
                self._discard_session(run_id)

    def _should_persist_checkpoint(self, run_id: str, checkpoint_type: str) -> bool:
        now = time.monotonic()
        with self._checkpoint_lock:
            if checkpoint_type in {
                "started",
                "paused",
                "resumed",
                "stopped",
                "command",
                "completed",
                "error",
            }:
                self._last_checkpoint_at[run_id] = now
                return True

            last_checkpoint_at = self._last_checkpoint_at.get(run_id)
            if last_checkpoint_at is None:
                self._last_checkpoint_at[run_id] = now
                return True
            if (now - last_checkpoint_at) >= self.checkpoint_interval_seconds:
                self._last_checkpoint_at[run_id] = now
                return True
            return False

    def _persist_checkpoint(
        self,
        run_id: str,
        snapshot: dict,
        checkpoint_type: str,
    ) -> None:
        session = self.session_factory()
        try:
            checkpoint = RunCheckpointRecord(
                run_id=run_id,
                checkpoint_type=checkpoint_type,
                runtime_status=str(snapshot["runtime_status"]),
                sim_rate=float(snapshot["sim_rate"]),
                snapshot=snapshot,
            )
            repository = RunCheckpointRepository(session)
            repository.create(checkpoint)
            repository.prune_for_run(
                run_id,
                keep_latest=self.checkpoint_retention_per_run,
            )
        finally:
            session.close()

    def _persist_run_summary(self, run_id: str, snapshot: dict) -> None:
        """Store the factual run summary on the durable run at terminal states."""
        summary = snapshot.get("summary")
        if not isinstance(summary, dict):
            return
        session = self.session_factory()
        try:
            run = session.get(RunRecord, run_id)
            if run is None:
                return
            run.summary_json = summary
            session.add(run)
            session.commit()
        finally:
            session.close()

    def _discard_session(self, run_id: str) -> None:
        with self._lock:
            self._sessions.pop(run_id, None)
        with self._checkpoint_lock:
            self._last_checkpoint_at.pop(run_id, None)
