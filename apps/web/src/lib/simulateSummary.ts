// Simulate mode has no conflict pair, no crossing point, and no pass/fail
// evaluation — it's free traffic control. This only tracks the small set of
// facts the end-of-run summary needs: how long the run lasted, how many
// aircraft were in the scenario, how many real instructions were issued, and
// how many discrete loss-of-separation events occurred between any two
// aircraft (a generalization of the pairwise distance check already used by
// Practice, applied across all active pairs instead of one fixed pair).

import { useEffect, useRef, useState } from "react";

import {
  REQUIRED_HORIZONTAL_SEPARATION_NM,
  REQUIRED_VERTICAL_SEPARATION_FT,
  distanceNm,
  isSeparated,
} from "./conflict";
import type { RunAircraftStateResponse } from "../types/api";

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
        : REQUIRED_HORIZONTAL_SEPARATION_NM,
    requiredVerticalFt:
      typeof record.required_vertical_separation_ft === "number"
        ? record.required_vertical_separation_ft
        : REQUIRED_VERTICAL_SEPARATION_FT,
  };
}

function pairKey(firstId: string, secondId: string): string {
  return [firstId, secondId].sort().join("|");
}

/**
 * Tracks discrete loss-of-separation events across every pair of active
 * aircraft (not just a single configured pair), and reports a final summary
 * once the run ends — naturally (all aircraft finished) or manually
 * (terminated). No per-tick history is kept, only running counters.
 */
export function useSimulateSummary(params: {
  config: SimulateConfig | null;
  aircraft: RunAircraftStateResponse[];
  runStatus: string | undefined;
  runStartedAt: string | null | undefined;
  commandCount: number;
}): SimulateSummaryState {
  const { config, aircraft, runStatus, runStartedAt, commandCount } = params;

  const [summary, setSummary] = useState<SimulateSummaryState>(EMPTY_SUMMARY);
  const [losCount, setLosCount] = useState(0);
  const violatingPairs = useRef(new Set<string>());
  const isFrozen = useRef(false);

  useEffect(() => {
    isFrozen.current = false;
    violatingPairs.current = new Set();
    setLosCount(0);
    setSummary(EMPTY_SUMMARY);
    // Reset whenever the active simulate scenario changes (new run).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config?.title]);

  useEffect(() => {
    if (!config || isFrozen.current) {
      return;
    }

    const trackable = aircraft.filter((item) => item.status !== "finished");
    let newLosCount = losCount;
    for (let i = 0; i < trackable.length; i += 1) {
      for (let j = i + 1; j < trackable.length; j += 1) {
        const first = trackable[i];
        const second = trackable[j];
        const horizontalNm = distanceNm(first.position_dd, second.position_dd);
        const verticalFt = Math.abs(first.flight_level - second.flight_level) * 100;
        const violated = !isSeparated(
          horizontalNm,
          verticalFt,
          config.requiredHorizontalNm,
          config.requiredVerticalFt,
        );
        const key = pairKey(first.id, second.id);
        if (violated && !violatingPairs.current.has(key)) {
          violatingPairs.current.add(key);
          newLosCount += 1;
        } else if (!violated && violatingPairs.current.has(key)) {
          violatingPairs.current.delete(key);
        }
      }
    }
    if (newLosCount !== losCount) {
      setLosCount(newLosCount);
    }

    const allFinished = aircraft.length > 0 && aircraft.every((item) => item.status === "finished");
    const manuallyStopped = runStatus === "stopped";
    if (!allFinished && !manuallyStopped) {
      return;
    }

    isFrozen.current = true;
    const startedAtMs = runStartedAt ? Date.parse(runStartedAt) : NaN;
    const durationSeconds = Number.isFinite(startedAtMs)
      ? Math.max(Math.floor((Date.now() - startedAtMs) / 1000), 0)
      : 0;
    setSummary({
      ready: true,
      durationSeconds,
      aircraftInSimulation: aircraft.length,
      instructionsIssued: commandCount,
      lossOfSeparationCount: newLosCount,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config, aircraft, runStatus, runStartedAt, commandCount, losCount]);

  return summary;
}
