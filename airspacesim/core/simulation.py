"""Deterministic simulation façade.

`Simulation` owns simulated time, scheduled aircraft entry, command
application, general separation monitoring, serialisable snapshots, and the
emitted engine-event stream. It never sleeps, never spawns threads, and
never writes files — embedding applications decide pacing and persistence.

Typical use::

    simulation = Simulation.from_contracts(scenario_airspace, scenario_aircraft)
    simulation.issue_command({"event_id": "c1", "type": "SET_FL",
                              "payload": {"aircraft_id": "NVR231", "flight_level": 310}})
    simulation.step(seconds=1.0)          # simulated seconds
    snapshot = simulation.snapshot()
    events = simulation.drain_events()
"""

import threading
from datetime import datetime, timezone

from airspacesim.core.clock import SimulationClock
from airspacesim.core.engine_events import (
    AIRCRAFT_ENTERED,
    AIRCRAFT_EXITED,
    COMMAND_APPLIED,
    SIMULATION_COMPLETED,
    EngineEvent,
)
from airspacesim.core.separation import SeparationMonitor, SeparationStandard
from airspacesim.simulation.aircraft_manager import AircraftManager
from airspacesim.simulation.events import apply_events_idempotent


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _entry_time_seconds(item):
    value = item.get("entry_time_seconds", item.get("appear_after_seconds", 0))
    return float(value or 0)


class Simulation:
    """One deterministic simulation over a batched AircraftManager fleet."""

    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"

    def __init__(self, manager, *, pending_entries=None, standard=None, clock=None):
        if manager.execution_mode != "batched":
            raise ValueError(
                "Simulation requires an AircraftManager in 'batched' execution mode"
            )
        self._lock = threading.RLock()
        self.manager = manager
        self.clock = clock or SimulationClock()
        self.monitor = SeparationMonitor(standard or SeparationStandard())
        self.status = self.STATUS_ACTIVE
        self.commands_applied = 0
        self._pending_entries = sorted(
            list(pending_entries or []), key=_entry_time_seconds
        )
        self._events = []
        self._known_finished = set()
        for aircraft in manager.aircraft_list:
            self._emit(
                AIRCRAFT_ENTERED,
                {"aircraft_id": aircraft.id, "callsign": aircraft.callsign},
            )

    @classmethod
    def from_contracts(cls, scenario_airspace, scenario_aircraft, *, standard=None):
        """Build a simulation from canonical scenario contracts.

        Aircraft with `entry_time_seconds` (alias `appear_after_seconds`) > 0
        are scheduled by the simulation clock instead of entering at t=0.
        """
        from airspacesim.simulation.scenario_runner import (
            _build_routes_from_scenario_airspace,
            derive_airspace_center,
        )

        routes = _build_routes_from_scenario_airspace(scenario_airspace)
        manager = AircraftManager(
            routes,
            execution_mode="batched",
            enable_file_output=False,
            airspace_center=derive_airspace_center(scenario_airspace),
        )
        pending = []
        for item in scenario_aircraft["data"]["aircraft"]:
            if _entry_time_seconds(item) > 0:
                pending.append(dict(item))
                continue
            cls._add_aircraft_from_item(manager, item)
        return cls(manager, pending_entries=pending, standard=standard)

    @staticmethod
    def _add_aircraft_from_item(manager, item):
        manager.add_aircraft(
            id=item["id"],
            route_name=item["route_id"],
            callsign=item.get("callsign", item["id"]),
            speed=item["speed_kt"],
            flight_level=item.get("flight_level"),
            altitude_ft=item.get("altitude_ft", 0.0),
            vertical_rate_fpm=item.get("vertical_rate_fpm", 0.0),
            aircraft_type=item.get("aircraft_type", "UNKNOWN"),
        )

    def _emit(self, event_type, payload):
        self._events.append(
            EngineEvent(event_type, self.clock.now_seconds, payload)
        )

    def step(self, seconds):
        """Advance the simulation by `seconds` simulated seconds."""
        with self._lock:
            if self.status == self.STATUS_COMPLETED:
                return
            now = self.clock.advance(seconds)

            while self._pending_entries and (
                _entry_time_seconds(self._pending_entries[0]) <= now
            ):
                item = self._pending_entries.pop(0)
                self._add_aircraft_from_item(self.manager, item)
                self._emit(
                    AIRCRAFT_ENTERED,
                    {
                        "aircraft_id": item["id"],
                        "callsign": item.get("callsign", item["id"]),
                    },
                )

            self.manager.step_aircraft(seconds)

            for aircraft in self.manager.aircraft_list:
                finished = aircraft.current_index >= len(aircraft.waypoints) - 1
                if finished and aircraft.id not in self._known_finished:
                    self._known_finished.add(aircraft.id)
                    self._emit(
                        AIRCRAFT_EXITED,
                        {"aircraft_id": aircraft.id, "callsign": aircraft.callsign},
                    )

            self._events.extend(
                self.monitor.update(self._aircraft_states(), now)
            )

            if not self._pending_entries and self._all_aircraft_finished():
                self.status = self.STATUS_COMPLETED
                self._emit(SIMULATION_COMPLETED, {})

    def issue_command(self, command):
        """Apply one canonical command event to the live fleet.

        `command` is a dict with `event_id`, `type`, and `payload` — the same
        shape as inbox events. Returns the applied/skipped/rejected result.
        """
        with self._lock:
            result = apply_events_idempotent(self.manager, [command])
            for event_id in result["applied"]:
                self.commands_applied += 1
                self._emit(
                    COMMAND_APPLIED,
                    {
                        "command_id": event_id,
                        "command_type": command["type"],
                        "payload": dict(command.get("payload", {})),
                    },
                )
            return result

    def drain_events(self):
        """Return and clear the emitted engine events, oldest first."""
        with self._lock:
            events = self._events
            self._events = []
            return events

    def _all_aircraft_finished(self):
        with self.manager.lock:
            return all(
                aircraft.current_index >= len(aircraft.waypoints) - 1
                for aircraft in self.manager.aircraft_list
            )

    def _aircraft_states(self):
        states = []
        with self.manager.lock:
            aircraft_list = list(self.manager.aircraft_list)
        for aircraft in aircraft_list:
            finished = aircraft.current_index >= len(aircraft.waypoints) - 1
            raw_flight_level = getattr(aircraft, "flight_level", None)
            flight_level = (
                int(round(float(raw_flight_level)))
                if raw_flight_level is not None
                else int(round(float(aircraft.altitude_ft) / 100.0))
            )
            states.append(
                {
                    "id": aircraft.id,
                    "position_dd": [
                        float(aircraft.position[0]),
                        float(aircraft.position[1]),
                    ],
                    "flight_level": flight_level,
                    "status": "finished" if finished else "active",
                }
            )
        return states

    def snapshot(self, updated_utc=None):
        """Serialisable full state: clock, aircraft, separation, counters."""
        with self._lock:
            timestamp = updated_utc or _utc_now_iso()
            aircraft_items = []
            with self.manager.lock:
                aircraft_list = list(self.manager.aircraft_list)
            for aircraft in aircraft_list:
                status = (
                    "finished" if hasattr(aircraft, "finished_time") else "active"
                )
                raw_flight_level = getattr(aircraft, "flight_level", None)
                flight_level = (
                    int(round(float(raw_flight_level)))
                    if raw_flight_level is not None
                    else int(round(float(aircraft.altitude_ft) / 100.0))
                )
                aircraft_items.append(
                    {
                        "id": aircraft.id,
                        "callsign": aircraft.callsign,
                        "aircraft_type": getattr(aircraft, "aircraft_type", "UNKNOWN"),
                        "route_id": aircraft.route,
                        "position_dd": [
                            float(aircraft.position[0]),
                            float(aircraft.position[1]),
                        ],
                        "speed_kt": float(aircraft.speed),
                        "flight_level": flight_level,
                        "target_flight_level": getattr(
                            aircraft, "target_flight_level", flight_level
                        ),
                        "altitude_ft": float(aircraft.altitude_ft),
                        "vertical_rate_fpm": float(aircraft.vertical_rate_fpm),
                        "heading_deg": float(getattr(aircraft, "heading_deg", 0.0)),
                        "assigned_heading_deg": getattr(
                            aircraft, "assigned_heading_deg", None
                        ),
                        "assigned_radial_deg": getattr(
                            aircraft, "assigned_radial_deg", None
                        ),
                        "radial_deviation_deg": getattr(
                            aircraft, "radial_deviation_deg", None
                        ),
                        "radial_cross_track_nm": getattr(
                            aircraft, "radial_cross_track_nm", None
                        ),
                        "lateral_mode": getattr(aircraft, "lateral_mode", "route"),
                        "direct_to_fix_id": getattr(
                            aircraft, "direct_to_fix_id", None
                        ),
                        "hold_fix_id": getattr(aircraft, "hold_fix_id", None),
                        "traffic_flow": getattr(aircraft, "traffic_flow", "unknown"),
                        "status": status,
                        "updated_utc": timestamp,
                    }
                )
            return {
                "time_seconds": self.clock.now_seconds,
                "status": self.status,
                "pending_aircraft_count": len(self._pending_entries),
                "aircraft": aircraft_items,
                "separation": self.monitor.as_dict(),
            }

    def summary(self):
        """Factual run counters — not a competency assessment."""
        with self._lock:
            with self.manager.lock:
                current_count = len(self.manager.aircraft_list)
            return {
                "simulated_seconds": self.clock.now_seconds,
                "aircraft_total": current_count + len(self._pending_entries),
                "instructions_issued": self.commands_applied,
                "loss_of_separation_count": self.monitor.loss_event_count,
            }
