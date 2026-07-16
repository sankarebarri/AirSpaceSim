// Generalizes the separation-tracking pattern already proven in
// CrossingTrafficLearnPage.tsx (encounterMin) so a Practice scenario can
// carry its own conflict pair, crossing point, and minima via scenario
// metadata instead of hardcoding aircraft IDs in a page component.
//
// The evaluation question this answers: was valid required separation
// (horizontal OR vertical) established before the conflicting aircraft
// reached their crossing point, and maintained through the encounter?

import { useEffect, useRef, useState } from "react";

import {
  REQUIRED_HORIZONTAL_SEPARATION_NM,
  REQUIRED_VERTICAL_SEPARATION_FT,
  distanceNm,
  isSeparated,
} from "./conflict";
import type { RunAircraftStateResponse } from "../types/api";

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
        : REQUIRED_HORIZONTAL_SEPARATION_NM,
    requiredVerticalFt:
      typeof record.required_vertical_separation_ft === "number"
        ? record.required_vertical_separation_ft
        : REQUIRED_VERTICAL_SEPARATION_FT,
    crossingPoint: readNumberPair(record.crossing_point),
    visibleRouteIds,
    activeCommands,
    next,
  };
}

function buildExplanation(
  separationMaintained: boolean,
  applicableForm: ApplicableSeparationForm,
  requiredHorizontalNm: number,
): string {
  if (!separationMaintained) {
    return "Neither horizontal nor vertical separation was maintained when it was required.";
  }
  if (applicableForm === "vertical") {
    return `Horizontal separation fell below ${requiredHorizontalNm.toFixed(0)} NM, but vertical separation was already established before the crossing.`;
  }
  return "Horizontal separation was maintained throughout the encounter.";
}

/**
 * Tracks live separation between a scenario's configured conflict pair
 * relative to a fixed crossing point, and derives a final Practice outcome
 * once the encounter can be confirmed — either resolved before crossing,
 * lost, the scenario naturally completes, or the trainee terminates the
 * run. Only running minimums are kept in memory; no per-tick history.
 */
export function usePracticeOutcome(params: {
  config: PracticeConfig | null;
  aircraft: RunAircraftStateResponse[];
  runStatus: string | undefined;
  commandCount: number;
}): PracticeOutcomeState {
  const { config, aircraft, runStatus, commandCount } = params;

  const [encounterMin, setEncounterMin] = useState<{
    horizontalNm: number;
    verticalFt: number;
  } | null>(null);
  const [crossingMin, setCrossingMin] = useState<{ first: number; second: number } | null>(null);
  const [outcome, setOutcome] = useState<PracticeOutcomeState>(EMPTY_OUTCOME);
  const isFrozen = useRef(false);

  const configKey = config ? config.conflictPair.join("|") : null;

  useEffect(() => {
    isFrozen.current = false;
    setEncounterMin(null);
    setCrossingMin(null);
    setOutcome(EMPTY_OUTCOME);
    // Reset tracking whenever the active practice scenario changes (new run).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configKey]);

  useEffect(() => {
    if (!config || isFrozen.current) {
      return;
    }
    const activeConfig = config;

    const first = aircraft.find((item) => item.id === activeConfig.conflictPair[0]) ?? null;
    const second = aircraft.find((item) => item.id === activeConfig.conflictPair[1]) ?? null;

    function finish(
      reason: PracticeOutcomeReason,
      current: { horizontalNm: number; verticalFt: number } | null,
      resolutionConfirmed: boolean,
    ) {
      isFrozen.current = true;
      if (!current) {
        setOutcome({ ...EMPTY_OUTCOME, ready: true, reason, commandCount });
        return;
      }
      const separationMaintained = isSeparated(
        current.horizontalNm,
        current.verticalFt,
        activeConfig.requiredHorizontalNm,
        activeConfig.requiredVerticalFt,
      );
      const applicableForm: ApplicableSeparationForm =
        current.verticalFt >= activeConfig.requiredVerticalFt ? "vertical" : "horizontal";
      const rating: PracticeOutcomeRating = separationMaintained
        ? "safe_effective"
        : "loss_of_separation";
      setOutcome({
        ready: true,
        reason,
        separationMaintained,
        conflictResolvedBeforeCrossing:
          reason !== "loss_of_separation" && separationMaintained && resolutionConfirmed,
        closestHorizontalNm: current.horizontalNm,
        closestVerticalFt: current.verticalFt,
        applicableForm,
        rating,
        explanation: buildExplanation(separationMaintained, applicableForm, activeConfig.requiredHorizontalNm),
        commandCount,
      });
    }

    if (!first || !second) {
      if (runStatus === "stopped") {
        finish("manual_terminate", encounterMin, false);
      }
      return;
    }

    const horizontalNm = distanceNm(first.position_dd, second.position_dd);
    const verticalFt = Math.abs(first.flight_level - second.flight_level) * 100;
    const current =
      !encounterMin || horizontalNm < encounterMin.horizontalNm
        ? { horizontalNm, verticalFt }
        : encounterMin;
    if (current !== encounterMin) {
      setEncounterMin(current);
    }

    let pastCrossing: boolean;
    if (activeConfig.crossingPoint) {
      const distFirst = distanceNm(first.position_dd, activeConfig.crossingPoint);
      const distSecond = distanceNm(second.position_dd, activeConfig.crossingPoint);
      const nextFirstMin = crossingMin ? Math.min(crossingMin.first, distFirst) : distFirst;
      const nextSecondMin = crossingMin ? Math.min(crossingMin.second, distSecond) : distSecond;
      if (!crossingMin || nextFirstMin !== crossingMin.first || nextSecondMin !== crossingMin.second) {
        setCrossingMin({ first: nextFirstMin, second: nextSecondMin });
      }
      const firstPastCrossing = distFirst > nextFirstMin + PAST_MARGIN_NM;
      const secondPastCrossing = distSecond > nextSecondMin + PAST_MARGIN_NM;
      pastCrossing = firstPastCrossing && secondPastCrossing;
    } else {
      // No crossing point configured for this scenario: fall back to mutual
      // closest-approach as a reasonable proxy for "the encounter has passed".
      pastCrossing = horizontalNm > current.horizontalNm + PAST_MARGIN_NM;
    }

    if (runStatus === "stopped") {
      finish("manual_terminate", current, pastCrossing);
      return;
    }

    const separationMaintainedSoFar = isSeparated(
      current.horizontalNm,
      current.verticalFt,
      activeConfig.requiredHorizontalNm,
      activeConfig.requiredVerticalFt,
    );
    if (!separationMaintainedSoFar) {
      finish("loss_of_separation", current, false);
      return;
    }

    if (pastCrossing) {
      finish("resolved", current, true);
      return;
    }

    if (first.status === "finished" && second.status === "finished") {
      finish("scenario_complete", current, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config, aircraft, runStatus, encounterMin, crossingMin, commandCount]);

  return outcome;
}
