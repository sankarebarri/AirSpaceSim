// Practice debrief state for the run workspace.
//
// Since Phase 2/5 the authoritative evaluation runs SERVER-side
// (apps/api/app/sessions/practice.py): the API observes every tick, freezes
// the outcome, and persists it with the run summary. This module now only
// parses the scenario-metadata practice config for panel display and adapts
// the server summary to the panel's shape — the frontend no longer computes
// separation outcomes.

import type { RunStateResponse } from "../types/api";

export interface PracticeConfig {
  title: string;
  objective: string;
  assistance: string;
  conflictPair: [string, string];
  requiredHorizontalNm: number;
  requiredVerticalFt: number;
  crossingPoint: [number, number] | null;
  visibleRouteIds: string[] | null;
  activeCommands: Set<string> | null;
  next: { label: string; path: string } | null;
}

export type ApplicableSeparationForm = "horizontal" | "vertical";
export type PracticeOutcomeReason =
  | "resolved"
  | "loss_of_separation"
  | "manual_terminate"
  | "scenario_complete";
export type PracticeOutcomeRating = "safe_effective" | "loss_of_separation";

export interface PracticeOutcomeState {
  ready: boolean;
  reason: PracticeOutcomeReason | null;
  separationMaintained: boolean | null;
  conflictResolvedBeforeCrossing: boolean | null;
  closestHorizontalNm: number | null;
  closestVerticalFt: number | null;
  applicableForm: ApplicableSeparationForm | null;
  rating: PracticeOutcomeRating | null;
  explanation: string | null;
  commandCount: number;
}

const PAST_MARGIN_NM = 0.5;

const EMPTY_OUTCOME: PracticeOutcomeState = {
  ready: false,
  reason: null,
  separationMaintained: null,
  conflictResolvedBeforeCrossing: null,
  closestHorizontalNm: null,
  closestVerticalFt: null,
  applicableForm: null,
  rating: null,
  explanation: null,
  commandCount: 0,
};

function readNumberPair(value: unknown): [number, number] | null {
  if (!Array.isArray(value) || value.length !== 2) {
    return null;
  }
  const [a, b] = value;
  return typeof a === "number" && typeof b === "number" ? [a, b] : null;
}

export function parsePracticeConfig(
  metadataPayload: Record<string, unknown> | undefined,
): PracticeConfig | null {
  const practice = metadataPayload?.practice;
  if (!practice || typeof practice !== "object") {
    return null;
  }
  const record = practice as Record<string, unknown>;
  const pair = record.conflict_pair;
  if (
    !Array.isArray(pair) ||
    pair.length !== 2 ||
    typeof pair[0] !== "string" ||
    typeof pair[1] !== "string"
  ) {
    return null;
  }
  const visibleRouteIds = Array.isArray(record.visible_route_ids)
    ? record.visible_route_ids.filter((item): item is string => typeof item === "string")
    : null;
  const activeCommands = Array.isArray(record.active_commands)
    ? new Set(record.active_commands.filter((item): item is string => typeof item === "string"))
    : null;
  const nextRecord =
    record.next && typeof record.next === "object" ? (record.next as Record<string, unknown>) : null;
  const next =
    nextRecord && typeof nextRecord.label === "string" && typeof nextRecord.path === "string"
      ? { label: nextRecord.label, path: nextRecord.path }
      : null;
  return {
    title: typeof record.title === "string" ? record.title : "Practice",
    objective:
      typeof record.objective === "string"
        ? record.objective
        : "Maintain the required separation between all aircraft.",
    assistance: typeof record.assistance === "string" ? record.assistance : "",
    conflictPair: [pair[0], pair[1]],
    requiredHorizontalNm:
      typeof record.required_horizontal_separation_nm === "number"
        ? record.required_horizontal_separation_nm
        : 10,
    requiredVerticalFt:
      typeof record.required_vertical_separation_ft === "number"
        ? record.required_vertical_separation_ft
        : 1000,
    crossingPoint: readNumberPair(record.crossing_point),
    visibleRouteIds,
    activeCommands,
    next,
  };
}

/**
 * Adapt the server-computed practice outcome (run summary) to the panel
 * shape. `ready` becomes true once the server tracker has frozen an outcome.
 */
export function practiceOutcomeFromRunState(
  state: RunStateResponse | null | undefined,
): PracticeOutcomeState {
  const summary = (state?.summary ?? null) as Record<string, unknown> | null;
  const outcome = (summary?.practice_outcome ?? null) as Record<string, unknown> | null;
  const instructionsIssued =
    typeof summary?.instructions_issued === "number" ? summary.instructions_issued : 0;
  if (!outcome) {
    return { ...EMPTY_OUTCOME, commandCount: instructionsIssued };
  }
  return {
    ready: true,
    reason: (outcome.reason as PracticeOutcomeReason | null) ?? null,
    separationMaintained:
      typeof outcome.separation_maintained === "boolean"
        ? outcome.separation_maintained
        : null,
    conflictResolvedBeforeCrossing:
      typeof outcome.conflict_resolved_before_crossing === "boolean"
        ? outcome.conflict_resolved_before_crossing
        : null,
    closestHorizontalNm:
      typeof outcome.closest_horizontal_nm === "number"
        ? outcome.closest_horizontal_nm
        : null,
    closestVerticalFt:
      typeof outcome.closest_vertical_ft === "number"
        ? outcome.closest_vertical_ft
        : null,
    applicableForm:
      (outcome.applicable_form as ApplicableSeparationForm | null) ?? null,
    rating: (outcome.rating as PracticeOutcomeRating | null) ?? null,
    explanation:
      typeof outcome.explanation === "string" ? outcome.explanation : null,
    commandCount:
      typeof outcome.commands_issued === "number"
        ? outcome.commands_issued
        : instructionsIssued,
  };
}
