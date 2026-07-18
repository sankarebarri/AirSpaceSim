// Simulate debrief for the run workspace.
//
// Since Phase 2/5 the general separation monitoring runs in the ENGINE
// (airspacesim SeparationMonitor: one event per continuous loss) and the
// factual summary is computed and persisted server-side. This module only
// parses the scenario-metadata simulate config for display and adapts the
// server summary — no client-side separation math remains here.

import type { RunResponse, RunStateResponse } from "../types/api";

export interface SimulateConfig {
  title: string;
  visibleRouteIds: string[] | null;
  requiredHorizontalNm: number;
  requiredVerticalFt: number;
}

export interface SimulateSummaryState {
  ready: boolean;
  durationSeconds: number;
  aircraftInSimulation: number;
  instructionsIssued: number;
  lossOfSeparationCount: number;
}

const EMPTY_SUMMARY: SimulateSummaryState = {
  ready: false,
  durationSeconds: 0,
  aircraftInSimulation: 0,
  instructionsIssued: 0,
  lossOfSeparationCount: 0,
};

export function parseSimulateConfig(
  metadataPayload: Record<string, unknown> | undefined,
): SimulateConfig | null {
  const simulate = metadataPayload?.simulate;
  if (!simulate || typeof simulate !== "object") {
    return null;
  }
  const record = simulate as Record<string, unknown>;
  const visibleRouteIds = Array.isArray(record.visible_route_ids)
    ? record.visible_route_ids.filter((item): item is string => typeof item === "string")
    : null;
  return {
    title: typeof record.title === "string" ? record.title : "Simulation",
    visibleRouteIds,
    requiredHorizontalNm:
      typeof record.required_horizontal_separation_nm === "number"
        ? record.required_horizontal_separation_nm
        : 10,
    requiredVerticalFt:
      typeof record.required_vertical_separation_ft === "number"
        ? record.required_vertical_separation_ft
        : 1000,
  };
}

/**
 * Adapt the server-computed run summary to the Simulate debrief shape.
 * Ready once the run has ended (stopped by the trainee or completed
 * naturally); the loss-of-separation count comes from the engine monitor
 * (one event per continuous violation, never per tick).
 */
export function simulateSummaryFromRunState(
  state: RunStateResponse | null | undefined,
  run: RunResponse | null | undefined,
): SimulateSummaryState {
  const summary = (state?.summary ?? null) as Record<string, unknown> | null;
  const runtimeStatus = state?.runtime_status;
  const isTerminal =
    runtimeStatus === "stopped" ||
    runtimeStatus === "completed" ||
    run?.status === "stopped";
  if (!summary || !isTerminal) {
    return EMPTY_SUMMARY;
  }
  const startedAtMs = run?.started_at ? Date.parse(run.started_at) : NaN;
  const endedAtMs = run?.ended_at ? Date.parse(run.ended_at) : NaN;
  const wallDurationSeconds =
    Number.isFinite(startedAtMs) && Number.isFinite(endedAtMs)
      ? Math.max(Math.floor((endedAtMs - startedAtMs) / 1000), 0)
      : null;
  const simulatedSeconds =
    typeof summary.simulated_seconds === "number"
      ? Math.floor(summary.simulated_seconds)
      : 0;
  return {
    ready: true,
    durationSeconds: wallDurationSeconds ?? simulatedSeconds,
    aircraftInSimulation:
      typeof summary.aircraft_total === "number" ? summary.aircraft_total : 0,
    instructionsIssued:
      typeof summary.instructions_issued === "number"
        ? summary.instructions_issued
        : 0,
    lossOfSeparationCount:
      typeof summary.loss_of_separation_count === "number"
        ? summary.loss_of_separation_count
        : 0,
  };
}
