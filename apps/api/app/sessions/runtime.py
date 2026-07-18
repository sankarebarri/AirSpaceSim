"""In-memory runtime session orchestration for simulation runs.

The session owns pacing (wall-clock ticks, sim_rate) and run lifecycle; the
engine's `Simulation` façade owns simulated time, movement, commands,
scheduled aircraft entry, separation monitoring, and engine events.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any

from airspacesim.core import Simulation, SeparationStandard
from airspacesim.core.models import TrajectoryTrack

from .practice import PracticeTracker


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _standard_from_metadata(
    metadata_payload: dict[str, Any] | None,
) -> SeparationStandard:
    """Resolve applicable minima from scenario metadata (practice or simulate)."""
    metadata = metadata_payload or {}
    for section_name in ("practice", "simulate"):
        section = metadata.get(section_name)
        if isinstance(section, dict):
            horizontal = section.get("required_horizontal_separation_nm")
            vertical = section.get("required_vertical_separation_ft")
            if isinstance(horizontal, (int, float)) or isinstance(
                vertical, (int, float)
            ):
                return SeparationStandard(
                    horizontal_nm=(
                        float(horizontal)
                        if isinstance(horizontal, (int, float))
                        else SeparationStandard.horizontal_nm
                    ),
                    vertical_ft=(
                        float(vertical)
                        if isinstance(vertical, (int, float))
                        else SeparationStandard.vertical_ft
                    ),
                )
    return SeparationStandard()


class SimulationRuntimeSession:
    """Manage one in-memory simulation session for a persisted run."""

    def __init__(
        self,
        *,
        run_id: str,
        scenario_airspace: dict[str, Any],
        scenario_aircraft: dict[str, Any],
        sim_rate: float,
        update_interval_seconds: float = 0.25,
        state_publisher=None,
        metadata_payload: dict[str, Any] | None = None,
    ) -> None:
        self.run_id = run_id
        self.sim_rate = float(sim_rate)
        self.update_interval_seconds = max(float(update_interval_seconds), 0.05)
        self.runtime_status = "draft"
        self.last_updated_utc = _utc_now_iso()
        self.last_error: str | None = None
        self._state_publisher = state_publisher

        self._state_lock = threading.Lock()
        self._tick_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self.simulation = Simulation.from_contracts(
            scenario_airspace,
            scenario_aircraft,
            standard=_standard_from_metadata(metadata_payload),
        )
        # Kept for embedding compatibility; the manager is engine-internal.
        self.manager = self.simulation.manager
        self.practice_tracker = PracticeTracker.from_metadata(metadata_payload)
        self._summary_kind = (
            "practice" if self.practice_tracker is not None else "simulate"
        )
        content_versions = (metadata_payload or {}).get("content_versions")
        self.content_versions = (
            dict(content_versions) if isinstance(content_versions, dict) else None
        )

    def start(self) -> None:
        with self._state_lock:
            if self.runtime_status not in {"draft", "paused"}:
                raise ValueError(
                    f"Cannot start runtime session in state {self.runtime_status}."
                )
            self.runtime_status = "running"
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(
                    target=self._run_loop,
                    name=f"airspacesim-run-{self.run_id}",
                    daemon=True,
                )
                self._thread.start()
            self.last_updated_utc = _utc_now_iso()
        self._emit_state("started")

    def pause(self) -> None:
        with self._state_lock:
            if self.runtime_status != "running":
                raise ValueError(
                    f"Cannot pause runtime session in state {self.runtime_status}."
                )
            self.runtime_status = "paused"
            self.last_updated_utc = _utc_now_iso()
        self._emit_state("paused")

    def resume(self) -> None:
        with self._state_lock:
            if self.runtime_status != "paused":
                raise ValueError(
                    f"Cannot resume runtime session in state {self.runtime_status}."
                )
            self.runtime_status = "running"
            self.last_updated_utc = _utc_now_iso()
        self._emit_state("resumed")

    def stop(self) -> None:
        with self._state_lock:
            if self.runtime_status == "stopped":
                return
            self.runtime_status = "stopped"
            self.last_updated_utc = _utc_now_iso()
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self.manager.request_shutdown()
        self.manager.terminate_simulations(timeout_seconds=1.0)
        self._observe_practice(stopping=True)
        self._emit_state("stopped")

    def apply_command(
        self,
        *,
        command_id: str,
        command_type: str,
        payload: dict[str, Any],
    ) -> dict[str, list[Any]]:
        """Apply a command to the live simulation."""

        with self._state_lock:
            runtime_status = self.runtime_status

        if runtime_status in {"stopped", "completed", "error"}:
            return {
                "applied": [],
                "skipped": [],
                "rejected": [
                    (
                        command_id,
                        f"runtime session is {runtime_status}",
                    )
                ],
            }

        if command_type == "SET_SIMULATION_SPEED":
            sim_rate = payload.get("sim_rate")
            if not isinstance(sim_rate, (int, float)) or sim_rate <= 0:
                return {
                    "applied": [],
                    "skipped": [],
                    "rejected": [(command_id, "invalid sim_rate")],
                }
            with self._state_lock:
                self.sim_rate = float(sim_rate)
                self.last_updated_utc = _utc_now_iso()
            self._emit_state("command")
            return {"applied": [command_id], "skipped": [], "rejected": []}

        normalized_event = {
            "event_id": command_id,
            "type": command_type,
            "payload": self._normalize_command_payload(command_type, payload),
        }
        with self._tick_lock:
            result = self.simulation.issue_command(normalized_event)
        self.last_updated_utc = _utc_now_iso()
        self._emit_state("command")
        return result

    def state_snapshot(self) -> dict[str, Any]:
        """Return the current live runtime state for API serialization."""

        with self._state_lock:
            runtime_status = self.runtime_status
            sim_rate = self.sim_rate
            updated_utc = self.last_updated_utc
            last_error = self.last_error

        simulation_snapshot = self.simulation.snapshot(updated_utc=updated_utc)
        aircraft_items = simulation_snapshot["aircraft"]
        active_count = sum(
            1 for item in aircraft_items if item["status"] == "active"
        )
        finished_count = len(aircraft_items) - active_count

        return {
            "runtime_status": runtime_status,
            "sim_rate": sim_rate,
            "updated_utc": updated_utc,
            "last_error": last_error,
            "time_seconds": simulation_snapshot["time_seconds"],
            "aircraft": aircraft_items,
            "separation": simulation_snapshot["separation"],
            "summary": self.run_summary(),
            "metrics": {
                "aircraft_count": len(aircraft_items),
                "active_aircraft_count": active_count,
                "finished_aircraft_count": finished_count,
                "pending_aircraft_count": simulation_snapshot[
                    "pending_aircraft_count"
                ],
            },
        }

    def run_summary(self) -> dict[str, Any]:
        """Factual run summary (persisted at terminal checkpoints)."""

        summary = self.simulation.summary()
        summary["kind"] = self._summary_kind
        if self.content_versions is not None:
            summary["content_versions"] = dict(self.content_versions)
        if self.practice_tracker is not None:
            summary["practice_outcome"] = self.practice_tracker.outcome
        return summary

    def trajectory_snapshot(self) -> dict[str, Any]:
        """Return trajectory-style live track records for the API."""

        snapshot = self.state_snapshot()
        tracks = [
            TrajectoryTrack(
                id=item["id"],
                callsign=item["callsign"],
                route_id=item["route_id"],
                position_dd=(item["position_dd"][0], item["position_dd"][1]),
                speed_kt=item["speed_kt"],
                flight_level=item["flight_level"],
                altitude_ft=item["altitude_ft"],
                vertical_rate_fpm=item["vertical_rate_fpm"],
                status=item["status"],
                updated_utc=item["updated_utc"],
            ).as_contract_dict()
            for item in snapshot["aircraft"]
        ]
        return {
            "runtime_status": snapshot["runtime_status"],
            "updated_utc": snapshot["updated_utc"],
            "tracks": tracks,
        }

    def _observe_practice(self, *, stopping: bool = False) -> None:
        if self.practice_tracker is None:
            return
        states = self.simulation.snapshot()["aircraft"]
        self.practice_tracker.observe(
            states,
            stopping=stopping,
            commands_issued=self.simulation.commands_applied,
        )

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._state_lock:
                runtime_status = self.runtime_status
                sim_rate = self.sim_rate

            if runtime_status != "running":
                time.sleep(0.05)
                continue

            try:
                with self._tick_lock:
                    self.simulation.step(self.update_interval_seconds * sim_rate)
                self._observe_practice()
                self.last_updated_utc = _utc_now_iso()
                self._emit_state("tick")
                if self.simulation.status == Simulation.STATUS_COMPLETED:
                    with self._state_lock:
                        if self.runtime_status == "running":
                            self.runtime_status = "completed"
                    self._emit_state("completed")
                    break
            except Exception as exc:
                with self._state_lock:
                    self.last_error = str(exc)
                    self.runtime_status = "error"
                self._emit_state("error")
                break
            time.sleep(self.update_interval_seconds)

    def _normalize_command_payload(
        self, command_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        normalized = dict(payload)
        if command_type == "ADD_AIRCRAFT" and "route_id" not in normalized:
            route_value = normalized.get("route") or normalized.get("route_name")
            if route_value is not None:
                normalized["route_id"] = route_value
        if command_type == "SET_SPEED" and "speed_kt" not in normalized:
            speed_value = normalized.get("speed")
            if speed_value is not None:
                normalized["speed_kt"] = speed_value
        return normalized

    def _emit_state(self, checkpoint_type: str) -> None:
        if self._state_publisher is not None:
            self._state_publisher(
                self.run_id,
                self.state_snapshot(),
                checkpoint_type,
            )
