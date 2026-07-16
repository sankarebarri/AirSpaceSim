"""Contract validation and adapter primitives for AirSpaceSim."""

from airspacesim.io.contracts import (
    CANONICAL_DATA_DOMAINS,
    ValidationError,
    build_envelope,
    contract_domain,
    validate_aircraft_data,
    validate_aircraft_state,
    validate_inbox_events,
    validate_map_config,
    validate_render_profile,
    validate_scenario_v01,
    validate_scenario_aircraft,
    validate_scenario_airspace,
    validate_trajectory_v01,
)
from airspacesim.io.adapters import (
    EventIngestionAdapter,
    FileEventAdapter,
    FileSnapshotAdapter,
    StdinEventAdapter,
)
from airspacesim.io.airspaces import normalize_scenario_airspace_payload
from airspacesim.io.exporters import (
    export_trajectory_json_to_csv,
    export_trajectory_payload_to_csv,
    serialize_trajectory_payload_to_csv,
)

__all__ = [
    "ValidationError",
    "CANONICAL_DATA_DOMAINS",
    "build_envelope",
    "contract_domain",
    "validate_aircraft_data",
    "validate_aircraft_state",
    "validate_inbox_events",
    "validate_map_config",
    "validate_render_profile",
    "validate_scenario_v01",
    "validate_scenario_aircraft",
    "validate_scenario_airspace",
    "validate_trajectory_v01",
    "EventIngestionAdapter",
    "FileEventAdapter",
    "FileSnapshotAdapter",
    "StdinEventAdapter",
    "normalize_scenario_airspace_payload",
    "export_trajectory_json_to_csv",
    "export_trajectory_payload_to_csv",
    "serialize_trajectory_payload_to_csv",
]
