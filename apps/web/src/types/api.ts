export interface ScenarioResponse {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  airspace_payload: Record<string, unknown>;
  aircraft_payload: Record<string, unknown>;
  metadata_payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ScenarioListResponse {
  items: ScenarioResponse[];
}

export interface AirspaceScenarioSummary {
  id: string;
  title: string;
  path: string;
  description: string | null;
  service_type: string | null;
  training_mode: string | null;
  difficulty: string | null;
}

export interface AirspaceLessonSummary {
  id: string;
  title: string;
  path: string;
  scenario_id: string | null;
  service_type: string | null;
  training_mode: string | null;
  level: string | null;
  duration_minutes: number | null;
}

export interface AirspacePackageSummary {
  id: string;
  version?: string | null;
  name: string;
  description: string;
  package_type: string;
  service_types: string[];
  difficulty: string;
  training_modes: string[];
  airspace_file: string;
  default_scenario: string | null;
  map: Record<string, unknown>;
  scenarios: AirspaceScenarioSummary[];
  lessons: AirspaceLessonSummary[];
}

export interface AirspacePackageListResponse {
  items: AirspacePackageSummary[];
}

export interface RunCreateRequest {
  scenario_id?: string | null;
  name?: string | null;
}

export interface PracticeRunCreateRequest {
  airspace_id: string;
  scenario_id?: string | null;
  lesson_id?: string | null;
  name?: string | null;
}

export interface RunResponse {
  id: string;
  scenario_id: string | null;
  name: string | null;
  status: string;
  sim_rate: number;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  ended_at: string | null;
  summary?: Record<string, unknown> | null;
}

export interface RunListResponse {
  items: RunResponse[];
}

export interface RunAircraftStateResponse {
  id: string;
  callsign: string | null;
  aircraft_type: string;
  route_id: string;
  position_dd: [number, number];
  speed_kt: number;
  flight_level: number;
  target_flight_level?: number | null;
  altitude_ft: number;
  vertical_rate_fpm: number;
  heading_deg: number;
  assigned_heading_deg?: number | null;
  assigned_radial_deg?: number | null;
  radial_deviation_deg?: number | null;
  radial_cross_track_nm?: number | null;
  lateral_mode: string;
  direct_to_fix_id?: string | null;
  hold_fix_id?: string | null;
  traffic_flow: string;
  status: string;
  updated_utc: string;
}

export interface RunMetricsResponse {
  aircraft_count: number;
  active_aircraft_count: number;
  finished_aircraft_count: number;
  pending_aircraft_count?: number;
}

export interface RunSeparationViolationResponse {
  pair: string[];
  horizontal_nm: number;
  vertical_ft: number;
  started_at_seconds: number;
}

export interface RunSeparationResponse {
  standard: { horizontal_nm: number; vertical_ft: number };
  active_violations: RunSeparationViolationResponse[];
  loss_of_separation_count: number;
}

export interface RunStateResponse {
  run: RunResponse;
  runtime_status: string;
  sim_rate: number;
  updated_utc: string | null;
  source: string;
  last_error: string | null;
  time_seconds?: number | null;
  aircraft: RunAircraftStateResponse[];
  separation?: RunSeparationResponse | null;
  summary?: Record<string, unknown> | null;
  metrics: RunMetricsResponse;
}

export type RunStateStreamPayload = Omit<RunStateResponse, "run" | "source">;

export interface RunTrajectoryTrackResponse {
  id: string;
  route_id: string;
  position_dd: [number, number];
  status: string;
  updated_utc: string;
  callsign?: string | null;
  speed_kt?: number | null;
  flight_level?: number | null;
  altitude_ft?: number | null;
  vertical_rate_fpm?: number | null;
}

export interface RunTrajectoryResponse {
  run_id: string;
  runtime_status: string;
  updated_utc: string | null;
  tracks: RunTrajectoryTrackResponse[];
}

export interface RunCommandCreateRequest {
  command_type: string;
  payload: Record<string, unknown>;
}

export interface RunCommandResponse {
  id: string;
  run_id: string;
  command_type: string;
  status: string;
  payload: Record<string, unknown>;
  created_at: string;
  applied_at: string | null;
}

export interface CommandResultItem {
  command_id: string;
  reason: string;
}

export interface RunCommandResultResponse {
  state: "queued" | "applied" | "skipped" | "rejected";
  applied: string[];
  skipped: CommandResultItem[];
  rejected: CommandResultItem[];
}

export interface RunCommandSubmissionResponse {
  command: RunCommandResponse;
  result: RunCommandResultResponse;
}

export interface RunStateSnapshotEvent {
  type: "run_state.snapshot";
  run_id: string;
  data: RunStateResponse;
}

export interface RunStateUpdatedEvent {
  type: "run_state.updated";
  run_id: string;
  emitted_at: string;
  data: RunStateStreamPayload;
}

export interface RunCommandResultEvent {
  type: "run_command.result";
  run_id: string;
  emitted_at: string;
  data: RunCommandSubmissionResponse;
}

export type RunStreamEvent =
  | RunStateSnapshotEvent
  | RunStateUpdatedEvent
  | RunCommandResultEvent;
