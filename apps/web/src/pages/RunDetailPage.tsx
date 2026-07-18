import {
  useDeferredValue,
  useEffect,
  useState,
  type FormEvent,
} from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  TrafficMap,
  type AircraftLabelDirection,
  type MapInspectTarget,
  type MeasurementPoint,
} from "../components/TrafficMap";
import { PracticePanel } from "../components/PracticePanel";
import { SimulatePanel } from "../components/SimulatePanel";
import {
  buildRunExportUrl,
  buildRunStreamUrl,
  getScenario,
  getRun,
  getRunState,
  pauseRun,
  resumeRun,
  startRun,
  stopRun,
  submitRunCommand,
} from "../lib/api";
import { describeError, formatLabel, formatTimestamp } from "../lib/format";
import { parsePracticeConfig, practiceOutcomeFromRunState } from "../lib/practiceOutcome";
import { parseSimulateConfig, simulateSummaryFromRunState } from "../lib/simulateSummary";
import { filterOverlayByRouteIds, parseScenarioMapOverlay } from "../lib/scenario-map";
import type {
  RunAircraftStateResponse,
  RunCommandSubmissionResponse,
  RunResponse,
  RunStateResponse,
  RunStateStreamPayload,
  RunStreamEvent,
} from "../types/api";
import "./RunDetailPage.css";

type StreamConnectionState = "idle" | "connecting" | "open" | "closed" | "error";
type FreshnessTone = "live" | "delayed" | "stale";
type DetailTab = "state" | "clearances" | "despatch";

const LIVE_WINDOW_MS = 5_000;
const DELAYED_WINDOW_MS = 15_000;
const DEFAULT_REFERENCE_FIX_POSITION_DD: [number, number] = [16.25, -0.03];
const EARTH_RADIUS_NM = 3440.065;
const COMMAND_HISTORY_LIMIT = 8;
const TOAST_DURATION_MS = 2_800;

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}

function calculateDistanceNm(
  fromPosition: [number, number],
  toPosition: [number, number],
): number {
  const [fromLat, fromLon] = fromPosition;
  const [toLat, toLon] = toPosition;
  const deltaLat = toRadians(toLat - fromLat);
  const deltaLon = toRadians(toLon - fromLon);
  const fromLatRadians = toRadians(fromLat);
  const toLatRadians = toRadians(toLat);
  const halfChord =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(fromLatRadians) *
      Math.cos(toLatRadians) *
      Math.sin(deltaLon / 2) ** 2;

  return (
    2 *
    EARTH_RADIUS_NM *
    Math.atan2(Math.sqrt(halfChord), Math.sqrt(1 - halfChord))
  );
}

function toIsoNow(): string {
  return new Date().toISOString();
}

function isRunNotFoundError(error: unknown): boolean {
  return error instanceof Error && error.message.startsWith("Run not found:");
}

function buildFreshnessState(referenceUtc: string | null): {
  label: string;
  tone: FreshnessTone;
} {
  if (!referenceUtc) {
    return {
      label: "No snapshot",
      tone: "stale",
    };
  }

  const ageMs = Math.max(Date.now() - Date.parse(referenceUtc), 0);
  if (ageMs <= LIVE_WINDOW_MS) {
    return {
      label: "Live",
      tone: "live",
    };
  }
  if (ageMs <= DELAYED_WINDOW_MS) {
    return {
      label: "Delayed",
      tone: "delayed",
    };
  }
  return {
    label: "Stale",
    tone: "stale",
  };
}

function uniqueValues(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean))).sort((left, right) =>
    left.localeCompare(right),
  );
}

function matchesSearch(
  aircraft: RunAircraftStateResponse,
  searchQuery: string,
): boolean {
  if (!searchQuery) {
    return true;
  }

  return [
    aircraft.id,
    aircraft.callsign ?? "",
    aircraft.route_id,
    aircraft.traffic_flow,
    aircraft.status,
  ]
    .join(" ")
    .toLowerCase()
    .includes(searchQuery);
}

function mergeStreamState(
  currentState: RunStateResponse | undefined,
  currentRun: RunResponse | undefined,
  payload: RunStateStreamPayload,
): RunStateResponse | undefined {
  const resolvedRun = currentState?.run ?? currentRun;
  if (!resolvedRun) {
    return currentState;
  }

  return {
    run: resolvedRun,
    runtime_status: payload.runtime_status,
    sim_rate: payload.sim_rate,
    updated_utc: payload.updated_utc,
    source: "runtime_session",
    last_error: payload.last_error,
    aircraft: payload.aircraft,
    metrics: payload.metrics,
  };
}

function countAircraftWithStatus(
  aircraft: RunAircraftStateResponse[],
  status: string,
): number {
  return aircraft.filter((item) => item.status === status).length;
}

function resolveFlightLevelTrend(aircraft: RunAircraftStateResponse) {
  const targetFlightLevel = aircraft.target_flight_level;
  if (
    targetFlightLevel === null ||
    targetFlightLevel === undefined ||
    targetFlightLevel === aircraft.flight_level ||
    Math.abs(aircraft.vertical_rate_fpm) < 1
  ) {
    return {
      label: `FL ${aircraft.flight_level}`,
      status: "Maintaining",
      rate: "0 fpm",
    };
  }

  const climbing = aircraft.vertical_rate_fpm > 0;
  return {
    label: `FL ${aircraft.flight_level} ${climbing ? "↑" : "↓"} FL ${targetFlightLevel}`,
    status: climbing ? "Climbing" : "Descending",
    rate: `${Math.abs(aircraft.vertical_rate_fpm).toFixed(0)} fpm`,
  };
}

function formatCommandAction(commandType: string): string {
  switch (commandType) {
    case "SET_SPEED":
      return "Speed assigned";
    case "SET_FL":
      return "Flight level assigned";
    case "ADD_AIRCRAFT":
      return "Track added";
    case "ASSIGN_HEADING":
      return "Heading assigned";
    case "ASSIGN_RADIAL":
      return "Radial assigned";
    case "ASSIGN_RADIAL_DEVIATION":
      return "Radial deviation assigned";
    case "RESUME_ROUTE":
      return "Normal navigation resumed";
    case "INTERCEPT_ROUTE":
      return "Route intercept assigned";
    case "DIRECT_TO":
      return "Direct-to assigned";
    case "HOLD_AT_FIX":
      return "Hold assigned";
    case "EXIT_HOLD":
      return "Hold exited";
    case "SET_SIMULATION_SPEED":
      return "Run rate changed";
    default:
      return formatLabel(commandType);
  }
}

function resolveFlightLevelActionLabel(
  selectedAircraft: RunAircraftStateResponse | null,
  targetFlightLevelValue: string,
): string {
  if (!selectedAircraft) {
    return "Assign Level";
  }
  const targetFlightLevel = Number(targetFlightLevelValue);
  if (!Number.isFinite(targetFlightLevel)) {
    return "Assign Level";
  }
  if (targetFlightLevel > selectedAircraft.flight_level) {
    return "Climb";
  }
  if (targetFlightLevel < selectedAircraft.flight_level) {
    return "Descend";
  }
  return "Maintain";
}

function formatHeading(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "---";
  }
  return `${Math.round(value).toString().padStart(3, "0")}°`;
}

function formatRadial(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "---";
  }
  return `R${Math.round(value).toString().padStart(3, "0")}`;
}

function formatRadialDeviation(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "---";
  }
  if (Math.abs(value) < 0.5) {
    return "On radial";
  }
  return `${value > 0 ? "R" : "L"}${Math.abs(Math.round(value))}°`;
}

function resolveCommandReason(result: RunCommandSubmissionResponse): string | null {
  return (
    result.result.rejected[0]?.reason ??
    result.result.skipped[0]?.reason ??
    null
  );
}

function resolveCommandTarget(
  result: RunCommandSubmissionResponse,
  aircraft: RunAircraftStateResponse[],
): string {
  const aircraftId = result.command.payload.aircraft_id;
  if (typeof aircraftId !== "string" || !aircraftId) {
    return "Run";
  }
  const matchingAircraft = aircraft.find((item) => item.id === aircraftId);
  return matchingAircraft?.callsign ?? aircraftId;
}

function formatPosition(position: [number, number]): string {
  return `${position[0].toFixed(3)}, ${position[1].toFixed(3)}`;
}

function formatElapsed(startedAtIso: string | null, nowMs: number): string {
  if (!startedAtIso) {
    return "00:00:00";
  }
  const startedAtMs = Date.parse(startedAtIso);
  if (!Number.isFinite(startedAtMs)) {
    return "00:00:00";
  }
  const elapsedSec = Math.max(Math.floor((nowMs - startedAtMs) / 1000), 0);
  const hours = String(Math.floor(elapsedSec / 3600)).padStart(2, "0");
  const minutes = String(Math.floor((elapsedSec % 3600) / 60)).padStart(2, "0");
  const seconds = String(elapsedSec % 60).padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

export function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const queryClient = useQueryClient();
  const [streamStatus, setStreamStatus] = useState<StreamConnectionState>("idle");
  const [lastStreamEventAt, setLastStreamEventAt] = useState<string | null>(null);
  const [selectedAircraftId, setSelectedAircraftId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [routeFilter, setRouteFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [trafficFlowFilter, setTrafficFlowFilter] = useState("all");
  const [addAircraftId, setAddAircraftId] = useState("AC900");
  const [addCallsign, setAddCallsign] = useState("OPS900");
  const [addAircraftType, setAddAircraftType] = useState("B737");
  const [addRouteId, setAddRouteId] = useState("UL602");
  const [addSpeedKt, setAddSpeedKt] = useState("420");
  const [addFlightLevel, setAddFlightLevel] = useState("350");
  const [setSpeedValue, setSetSpeedValue] = useState("240");
  const [setFlightLevelValue, setSetFlightLevelValue] = useState("300");
  const [setHeadingValue, setSetHeadingValue] = useState("090");
  const [turnAmountValue, setTurnAmountValue] = useState("30");
  const [setRadialValue, setSetRadialValue] = useState("265");
  const [directToFixValue, setDirectToFixValue] = useState("NRV_VOR");
  const [holdFixValue, setHoldFixValue] = useState("NRV_VOR");
  const [setSimRateValue, setSetSimRateValue] = useState("1.0");
  const [aircraftLabelDirections, setAircraftLabelDirections] = useState<
    Record<string, AircraftLabelDirection>
  >({});
  const [lastCommandResult, setLastCommandResult] =
    useState<RunCommandSubmissionResponse | null>(null);
  const [commandHistory, setCommandHistory] = useState<
    RunCommandSubmissionResponse[]
  >([]);
  const [totalCommandCount, setTotalCommandCount] = useState(0);
  const [inspectTarget, setInspectTarget] = useState<MapInspectTarget | null>(null);
  const [isMeasureMode, setIsMeasureMode] = useState(false);
  const [measurementPoints, setMeasurementPoints] = useState<MeasurementPoint[]>([]);
  const [activeTab, setActiveTab] = useState<DetailTab>("state");
  const [isRateEditing, setIsRateEditing] = useState(false);
  const [toast, setToast] = useState<{ message: string; isError: boolean } | null>(
    null,
  );
  const [nowMs, setNowMs] = useState(() => Date.now());
  const deferredSearchQuery = useDeferredValue(searchQuery.trim().toLowerCase());

  const runQuery = useQuery({
    queryKey: ["run", runId],
    queryFn: () => getRun(runId ?? ""),
    enabled: Boolean(runId),
    refetchInterval: (query) =>
      isRunNotFoundError(query.state.error)
        ? false
        : streamStatus === "open"
          ? 15_000
          : 5_000,
  });
  const runNotFound = isRunNotFoundError(runQuery.error);
  const stateQuery = useQuery({
    queryKey: ["run", runId, "state"],
    queryFn: () => getRunState(runId ?? ""),
    enabled: Boolean(runId) && !runNotFound && Boolean(runQuery.data),
    refetchInterval:
      streamStatus === "open" || runNotFound ? false : 1_500,
  });
  const scenarioQuery = useQuery({
    queryKey: ["scenario", runQuery.data?.scenario_id],
    queryFn: () => getScenario(runQuery.data?.scenario_id ?? ""),
    enabled: Boolean(runQuery.data?.scenario_id),
  });

  const lifecycleMutation = useMutation({
    mutationFn: async (action: "start" | "pause" | "resume" | "stop") => {
      if (!runId) {
        throw new Error("Run id is missing.");
      }

      switch (action) {
        case "start":
          return startRun(runId);
        case "pause":
          return pauseRun(runId);
        case "resume":
          return resumeRun(runId);
        case "stop":
          return stopRun(runId);
      }
    },
    onSuccess: async (_data, action) => {
      showToast(`Run ${action}d`, false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["runs"] }),
        queryClient.invalidateQueries({ queryKey: ["run", runId] }),
        queryClient.invalidateQueries({ queryKey: ["run", runId, "state"] }),
      ]);
    },
    onError: (error) => {
      showToast(describeError(error), true);
    },
  });
  const commandMutation = useMutation({
    mutationFn: async (payload: {
      command_type: string;
      payload: Record<string, unknown>;
    }) => {
      if (!runId) {
        throw new Error("Run id is missing.");
      }
      return submitRunCommand(runId, payload);
    },
    onSuccess: async (response) => {
      setLastCommandResult(response);
      setCommandHistory((currentHistory) => [
        response,
        ...currentHistory.filter((item) => item.command.id !== response.command.id),
      ].slice(0, COMMAND_HISTORY_LIMIT));
      if (response.command.command_type !== "SET_SIMULATION_SPEED") {
        setTotalCommandCount((currentCount) => currentCount + 1);
      }
      const reason = resolveCommandReason(response);
      if (response.result.state === "rejected" || response.result.state === "skipped") {
        showToast(reason ?? formatCommandAction(response.command.command_type), true);
      } else {
        showToast(formatCommandAction(response.command.command_type), false);
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["runs"] }),
        queryClient.invalidateQueries({ queryKey: ["run", runId] }),
        queryClient.invalidateQueries({ queryKey: ["run", runId, "state"] }),
      ]);
    },
    onError: (error) => {
      showToast(describeError(error), true);
    },
  });

  function showToast(message: string, isError: boolean) {
    setToast({ message, isError });
  }

  useEffect(() => {
    if (!toast) {
      return;
    }
    const timer = window.setTimeout(() => setToast(null), TOAST_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    const timer = window.setInterval(() => setNowMs(Date.now()), 1_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!runId) {
      setStreamStatus("idle");
      setLastStreamEventAt(null);
      setLastCommandResult(null);
      setCommandHistory([]);
      return;
    }
    if (runNotFound) {
      setStreamStatus("error");
      setLastStreamEventAt(null);
      setLastCommandResult(null);
      setCommandHistory([]);
      return;
    }
    if (!runQuery.data) {
      setStreamStatus("idle");
      return;
    }

    let isActive = true;
    let reconnectAttempt = 0;
    let reconnectTimer: number | null = null;
    let socket: WebSocket | null = null;

    setLastStreamEventAt(null);
    setLastCommandResult(null);
    setCommandHistory([]);

    function clearReconnectTimer() {
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    }

    function scheduleReconnect() {
      if (!isActive) {
        return;
      }

      const delayMs = Math.min(1_000 * Math.max(reconnectAttempt, 1), 5_000);
      reconnectTimer = window.setTimeout(connect, delayMs);
    }

    function handleStreamEvent(event: RunStreamEvent) {
      const eventTimestamp =
        "emitted_at" in event
          ? event.emitted_at
          : event.data.updated_utc ?? toIsoNow();
      setLastStreamEventAt(eventTimestamp);

      if (event.type === "run_state.snapshot") {
        queryClient.setQueryData(["run", runId], event.data.run);
        queryClient.setQueryData(["run", runId, "state"], event.data);
        return;
      }

      if (event.type === "run_state.updated") {
        queryClient.setQueryData<RunStateResponse | undefined>(
          ["run", runId, "state"],
          (currentState) =>
            mergeStreamState(
              currentState,
              queryClient.getQueryData<RunResponse>(["run", runId]),
              event.data,
            ),
        );
        return;
      }

      setLastCommandResult(event.data);
      setCommandHistory((currentHistory) => [
        event.data,
        ...currentHistory.filter((item) => item.command.id !== event.data.command.id),
      ].slice(0, COMMAND_HISTORY_LIMIT));
    }

    function connect() {
      if (!isActive) {
        return;
      }

      clearReconnectTimer();
      setStreamStatus("connecting");
      socket = new WebSocket(buildRunStreamUrl(runId));

      socket.onopen = () => {
        if (!isActive) {
          return;
        }
        reconnectAttempt = 0;
        setStreamStatus("open");
      };

      socket.onmessage = (messageEvent) => {
        if (!isActive) {
          return;
        }

        try {
          handleStreamEvent(JSON.parse(messageEvent.data) as RunStreamEvent);
        } catch {
          setStreamStatus("error");
        }
      };

      socket.onerror = () => {
        if (!isActive) {
          return;
        }
        setStreamStatus("error");
      };

      socket.onclose = (closeEvent) => {
        if (!isActive) {
          return;
        }
        if (closeEvent.code === 4404) {
          setStreamStatus("error");
          return;
        }

        reconnectAttempt += 1;
        setStreamStatus((currentStatus) =>
          currentStatus === "error" ? "error" : "closed",
        );
        scheduleReconnect();
      };
    }

    connect();

    return () => {
      isActive = false;
      clearReconnectTimer();
      if (
        socket &&
        (socket.readyState === WebSocket.OPEN ||
          socket.readyState === WebSocket.CONNECTING)
      ) {
        socket.close();
      }
    };
  }, [queryClient, runId, runNotFound, runQuery.data]);

  const state = stateQuery.data;
  const run = runQuery.data ?? state?.run;
  const practiceConfig = parsePracticeConfig(scenarioQuery.data?.metadata_payload);
  const simulateConfig = parseSimulateConfig(scenarioQuery.data?.metadata_payload);
  const metadataAirspaceId =
    typeof scenarioQuery.data?.metadata_payload?.airspace_id === "string"
      ? (scenarioQuery.data.metadata_payload.airspace_id as string)
      : null;
  const metadataScenarioTemplateId =
    typeof scenarioQuery.data?.metadata_payload?.scenario_template_id === "string"
      ? (scenarioQuery.data.metadata_payload.scenario_template_id as string)
      : null;
  const parsedScenarioOverlay = parseScenarioMapOverlay(scenarioQuery.data);
  const visibleRouteIds = practiceConfig?.visibleRouteIds ?? simulateConfig?.visibleRouteIds ?? null;
  const scenarioOverlay = visibleRouteIds
    ? filterOverlayByRouteIds(parsedScenarioOverlay, visibleRouteIds)
    : parsedScenarioOverlay;
  const activeCommands = practiceConfig?.activeCommands ?? null;
  const showSpeedForm = !activeCommands || activeCommands.has("SET_SPEED");
  const showFlightLevelForm = !activeCommands || activeCommands.has("SET_FL");
  const showTurnControls = Boolean(practiceConfig) && Boolean(activeCommands?.has("ASSIGN_HEADING"));
  const showHeadingForm = !showTurnControls && (!activeCommands || activeCommands.has("ASSIGN_HEADING"));
  const showRadialForm = !activeCommands || activeCommands.has("ASSIGN_RADIAL");
  const showDirectToForm = !activeCommands || activeCommands.has("DIRECT_TO");
  const showHoldForm = !activeCommands || activeCommands.has("HOLD_AT_FIX");
  const showRouteSection =
    !activeCommands || activeCommands.has("RESUME_ROUTE") || activeCommands.has("EXIT_HOLD");
  const showDespatchTab = !activeCommands || activeCommands.has("ADD_AIRCRAFT");
  const aircraft = state?.aircraft ?? [];
  const routeOptions = uniqueValues(aircraft.map((item) => item.route_id));
  const statusOptions = uniqueValues(aircraft.map((item) => item.status));
  const trafficFlowOptions = uniqueValues(aircraft.map((item) => item.traffic_flow));
  const filteredAircraft = aircraft.filter((item) => {
    if (routeFilter !== "all" && item.route_id !== routeFilter) {
      return false;
    }
    if (statusFilter !== "all" && item.status !== statusFilter) {
      return false;
    }
    if (trafficFlowFilter !== "all" && item.traffic_flow !== trafficFlowFilter) {
      return false;
    }
    return matchesSearch(item, deferredSearchQuery);
  });
  const selectedAircraft =
    filteredAircraft.find((item) => item.id === selectedAircraftId) ??
    filteredAircraft[0] ??
    null;
  const freshness = buildFreshnessState(lastStreamEventAt ?? state?.updated_utc ?? null);
  const trackedAircraftSummary = `Showing ${filteredAircraft.length} of ${aircraft.length} tracked aircraft`;
  const selectedAircraftLabel =
    selectedAircraft?.callsign ?? selectedAircraft?.id ?? "None";
  const referenceFixPosition =
    scenarioOverlay.airspaces.find((airspace) => airspace.type === "circle")?.center ??
    scenarioOverlay.points[0]?.position ??
    DEFAULT_REFERENCE_FIX_POSITION_DD;
  const selectedAircraftReferenceDme = selectedAircraft
    ? calculateDistanceNm(referenceFixPosition, selectedAircraft.position_dd)
    : null;
  const selectedAircraftLevelTrend = selectedAircraft
    ? resolveFlightLevelTrend(selectedAircraft)
    : null;
  const flightLevelActionLabel = resolveFlightLevelActionLabel(
    selectedAircraft,
    setFlightLevelValue,
  );
  const visibleActiveCount = countAircraftWithStatus(filteredAircraft, "active");
  const visibleHoldingCount = countAircraftWithStatus(filteredAircraft, "holding");
  const measurementDistanceNm =
    measurementPoints.length === 2
      ? calculateDistanceNm(
          measurementPoints[0].position,
          measurementPoints[1].position,
        )
      : null;
  const activeAircraftList = filteredAircraft.filter((item) => item.status !== "finished");
  const finishedAircraftList = filteredAircraft.filter((item) => item.status === "finished");

  // Debrief data is server-authoritative: the engine monitor and the
  // API practice tracker compute and persist it with the run.
  const practiceOutcome = practiceOutcomeFromRunState(state);
  const simulateSummary = simulateSummaryFromRunState(state, run);

  useEffect(() => {
    if (filteredAircraft.length === 0) {
      if (selectedAircraftId !== null) {
        setSelectedAircraftId(null);
      }
      return;
    }

    if (!selectedAircraftId) {
      setSelectedAircraftId(filteredAircraft[0].id);
      return;
    }

    if (!filteredAircraft.some((item) => item.id === selectedAircraftId)) {
      setSelectedAircraftId(filteredAircraft[0].id);
    }
  }, [filteredAircraft, selectedAircraftId]);

  useEffect(() => {
    if (selectedAircraft) {
      setSetSpeedValue(selectedAircraft.speed_kt.toFixed(0));
      setSetFlightLevelValue(selectedAircraft.flight_level.toString());
      setSetHeadingValue(Math.round(selectedAircraft.heading_deg).toString().padStart(3, "0"));
      setSetRadialValue(
        Math.round(
          selectedAircraft.assigned_radial_deg ?? selectedAircraft.heading_deg,
        )
          .toString()
          .padStart(3, "0"),
      );
      setAddRouteId(selectedAircraft.route_id);
    }
  }, [selectedAircraft?.id]);

  useEffect(() => {
    if (state) {
      setSetSimRateValue(state.sim_rate.toFixed(1));
    }
  }, [state?.sim_rate]);

  function handleAddAircraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const speedKt = Number(addSpeedKt);
    const flightLevel = addFlightLevel.trim() ? Number(addFlightLevel) : null;
    if (
      !addAircraftId.trim() ||
      !addRouteId.trim() ||
      !Number.isFinite(speedKt) ||
      speedKt <= 0
    ) {
      return;
    }
    if (
      addFlightLevel.trim() &&
      (!Number.isFinite(flightLevel) || Number(flightLevel) < 0)
    ) {
      return;
    }
    commandMutation.mutate({
      command_type: "ADD_AIRCRAFT",
      payload: {
        aircraft_id: addAircraftId.trim(),
        callsign: addCallsign.trim() || addAircraftId.trim(),
        aircraft_type: addAircraftType.trim().toUpperCase() || "B737",
        route_id: addRouteId.trim(),
        speed_kt: speedKt,
        ...(flightLevel !== null ? { flight_level: Math.round(flightLevel) } : {}),
      },
    });
  }

  function handleSetSpeed(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAircraft) {
      return;
    }
    const speedKt = Number(setSpeedValue);
    if (!Number.isFinite(speedKt) || speedKt <= 0) {
      return;
    }
    commandMutation.mutate({
      command_type: "SET_SPEED",
      payload: {
        aircraft_id: selectedAircraft.id,
        speed_kt: speedKt,
      },
    });
  }

  function handleSetFlightLevel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAircraft) {
      return;
    }
    const flightLevel = Number(setFlightLevelValue);
    if (!Number.isFinite(flightLevel) || flightLevel < 0) {
      return;
    }
    commandMutation.mutate({
      command_type: "SET_FL",
      payload: {
        aircraft_id: selectedAircraft.id,
        flight_level: Math.round(flightLevel),
      },
    });
  }

  function handleAssignHeading(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAircraft) {
      return;
    }
    const heading = Number(setHeadingValue);
    if (!Number.isFinite(heading)) {
      return;
    }
    commandMutation.mutate({
      command_type: "ASSIGN_HEADING",
      payload: {
        aircraft_id: selectedAircraft.id,
        heading_deg: ((Math.round(heading) % 360) + 360) % 360,
      },
    });
  }

  function handleTurn(direction: "left" | "right") {
    if (!selectedAircraft) {
      return;
    }
    const turnAmount = Number(turnAmountValue);
    if (!Number.isFinite(turnAmount) || turnAmount <= 0) {
      return;
    }
    const currentHeading = selectedAircraft.assigned_heading_deg ?? selectedAircraft.heading_deg;
    const delta = direction === "left" ? -turnAmount : turnAmount;
    const nextHeading = ((Math.round(currentHeading + delta) % 360) + 360) % 360;
    commandMutation.mutate({
      command_type: "ASSIGN_HEADING",
      payload: {
        aircraft_id: selectedAircraft.id,
        heading_deg: nextHeading,
      },
    });
  }

  function handleAssignRadial(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAircraft) {
      return;
    }
    const radial = Number(setRadialValue);
    if (!Number.isFinite(radial)) {
      return;
    }
    commandMutation.mutate({
      command_type: "ASSIGN_RADIAL",
      payload: {
        aircraft_id: selectedAircraft.id,
        radial_deg: ((Math.round(radial) % 360) + 360) % 360,
      },
    });
  }

  function handleResumeRoute() {
    if (!selectedAircraft) {
      return;
    }
    commandMutation.mutate({
      command_type: "RESUME_ROUTE",
      payload: {
        aircraft_id: selectedAircraft.id,
      },
    });
  }

  function handleDirectTo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAircraft || !directToFixValue.trim()) {
      return;
    }
    commandMutation.mutate({
      command_type: "DIRECT_TO",
      payload: {
        aircraft_id: selectedAircraft.id,
        fix_id: directToFixValue.trim().toUpperCase(),
      },
    });
  }

  function handleHoldAtFix(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAircraft || !holdFixValue.trim()) {
      return;
    }
    commandMutation.mutate({
      command_type: "HOLD_AT_FIX",
      payload: {
        aircraft_id: selectedAircraft.id,
        fix_id: holdFixValue.trim().toUpperCase(),
        turn_direction: "right",
      },
    });
  }

  function handleExitHold() {
    if (!selectedAircraft) {
      return;
    }
    commandMutation.mutate({
      command_type: "EXIT_HOLD",
      payload: {
        aircraft_id: selectedAircraft.id,
      },
    });
  }

  function commitSimRate(nextValue: string) {
    const simRate = Number(nextValue);
    if (!Number.isFinite(simRate) || simRate <= 0) {
      setIsRateEditing(false);
      return;
    }
    commandMutation.mutate({
      command_type: "SET_SIMULATION_SPEED",
      payload: {
        sim_rate: simRate,
      },
    });
    setIsRateEditing(false);
  }

  function resetFilters() {
    setSearchQuery("");
    setRouteFilter("all");
    setStatusFilter("all");
    setTrafficFlowFilter("all");
  }

  function setSelectedAircraftLabelDirection(direction: AircraftLabelDirection) {
    if (!selectedAircraft) {
      return;
    }
    setAircraftLabelDirections((currentDirections) => ({
      ...currentDirections,
      [selectedAircraft.id]: direction,
    }));
  }

  function handleMapInspect(target: MapInspectTarget) {
    setInspectTarget(target);
  }

  function handleMeasurementPick(point: MeasurementPoint) {
    setMeasurementPoints((currentPoints) => {
      if (currentPoints.length >= 2) {
        return [point];
      }
      if (currentPoints.some((item) => item.id === point.id && item.type === point.type)) {
        return currentPoints;
      }
      return [...currentPoints, point];
    });
  }

  function clearMeasurement() {
    setMeasurementPoints([]);
  }

  function handleTerminate() {
    if (window.confirm("Terminate this run? This cannot be undone.")) {
      lifecycleMutation.mutate("stop");
    }
  }

  if (!runId) {
    return (
      <div className="console-page">
        <p className="cq-note" style={{ padding: 24 }}>
          Run id is missing from the current route.
        </p>
      </div>
    );
  }

  if (runNotFound) {
    return (
      <div className="console-page">
        <p className="cq-error" style={{ padding: 24 }}>
          {describeError(runQuery.error)}
        </p>
        <p className="cq-note" style={{ padding: "0 24px 24px" }}>
          Open the latest seeded run URL from the terminal output, including
          the sid query parameter.
        </p>
      </div>
    );
  }

  if (runQuery.isError || stateQuery.isError) {
    return (
      <div className="console-page">
        <p className="cq-error" style={{ padding: 24 }}>
          {describeError(runQuery.error ?? stateQuery.error)}
        </p>
      </div>
    );
  }

  if (!run || !state) {
    return (
      <div className="console-page">
        <p className="cq-note" style={{ padding: 24 }}>
          Loading simulator console…
        </p>
      </div>
    );
  }

  const runtimeIsRunning = run.status === "running";
  const runtimeIsPaused = run.status === "paused";
  const statusDotClass =
    runtimeIsRunning ? "cq-dot cq-dot-g" : runtimeIsPaused ? "cq-dot cq-dot-a" : "cq-dot cq-dot-x";
  const datalinkDotClass =
    streamStatus === "open"
      ? "cq-dl-dot cq-dot-g"
      : streamStatus === "connecting"
        ? "cq-dl-dot cq-dot-a"
        : "cq-dl-dot cq-dot-x";

  return (
    <div className="console-page">
      <nav className="cq-topbar">
        <Link to="/" className="cq-brand">
          AirSpaceSim
        </Link>
        <div className="cq-sep" />
        <div className="cq-run">
          RUN <h1 className="cq-run-heading">{run.name ?? run.id}</h1>
          {scenarioQuery.data ? ` · ${scenarioQuery.data.name}` : ""}
        </div>
        <div className="cq-status">
          <div className={statusDotClass} />
          <span className="cq-status-label">{formatLabel(state.runtime_status)}</span>
        </div>
        <div className="cq-dl">
          <div className={datalinkDotClass} />
          <span className="cq-dl-label">{formatLabel(streamStatus)}</span>
        </div>
        <div className="cq-sep" />
        {isRateEditing ? (
          <input
            className="cq-rate-input"
            defaultValue={setSimRateValue}
            autoFocus
            onBlur={(event) => commitSimRate(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                commitSimRate(event.currentTarget.value);
              }
              if (event.key === "Escape") {
                setIsRateEditing(false);
              }
            }}
          />
        ) : (
          <button
            type="button"
            className="cq-rate"
            title="Click to change sim rate"
            onClick={() => setIsRateEditing(true)}
          >
            {state.sim_rate.toFixed(1)}x
          </button>
        )}
        <div className="cq-sep" />
        <span className="cq-timer">{formatElapsed(run.started_at, nowMs)}</span>
        <div className="cq-sep" />
        {runtimeIsRunning ? (
          <button
            type="button"
            className="cq-btn"
            disabled={lifecycleMutation.isPending}
            onClick={() => lifecycleMutation.mutate("pause")}
          >
            ⏸ Hold
          </button>
        ) : runtimeIsPaused ? (
          <button
            type="button"
            className="cq-btn primary"
            disabled={lifecycleMutation.isPending}
            onClick={() => lifecycleMutation.mutate("resume")}
          >
            ▶ Resume
          </button>
        ) : run.status === "draft" ? (
          <button
            type="button"
            className="cq-btn primary"
            disabled={lifecycleMutation.isPending}
            onClick={() => lifecycleMutation.mutate("start")}
          >
            ▶ Launch
          </button>
        ) : null}
        <button
          type="button"
          className="cq-btn danger"
          disabled={lifecycleMutation.isPending || run.status === "stopped"}
          onClick={handleTerminate}
        >
          ■ Terminate
        </button>
        <a href={buildRunExportUrl(run.id)} className="cq-btn">
          ↓ Debrief
        </a>
        <Link to="/runs" className="cq-btn">
          ← Runs
        </Link>
      </nav>

      <div className="cq-body">
        <aside className="cq-traffic">
          <div className="cq-panel-head">
            <div className="cq-panel-head-row">
              <h2 className="cq-panel-head-title">Tracks</h2>
              <span className="cq-ph-count">
                {filteredAircraft.length}/{aircraft.length}
              </span>
            </div>
            {/*
            <input
              className="cq-search"
              placeholder="Callsign, route, or status…"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              aria-label="Search tracks"
            />
            <div className="cq-filter-row">
              <select
                className="cq-filter-select"
                value={routeFilter}
                onChange={(event) => setRouteFilter(event.target.value)}
              >
                <option value="all">All routes</option>
                {routeOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
              <select
                className="cq-filter-select"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="all">Any status</option>
                {statusOptions.map((option) => (
                  <option key={option} value={option}>
                    {formatLabel(option)}
                  </option>
                ))}
              </select>
            </div>
            <div className="cq-flow-filter">
              {["all", ...trafficFlowOptions].map((flow) => (
                <button
                  key={flow}
                  type="button"
                  className={
                    trafficFlowFilter === flow ? "cq-flow-btn on" : "cq-flow-btn"
                  }
                  onClick={() => setTrafficFlowFilter(flow)}
                >
                  {flow === "all" ? "All" : formatLabel(flow)}
                </button>
              ))}
            </div>
            <div className="cq-filter-summary">
              <strong>
                {filteredAircraft.length} / {aircraft.length}
              </strong>
              <button type="button" className="cq-clear-btn" onClick={resetFilters}>
                Clear
              </button>
            </div>
            */}
          </div>

          <div className="cq-scroll">
            {filteredAircraft.length === 0 ? (
              <p className="cq-empty">
                {aircraft.length === 0
                  ? "No tracks in this snapshot."
                  : "No tracks match the filters."}
              </p>
            ) : (
              <>
                {activeAircraftList.length > 0 ? (
                  <>
                    <div className="cq-group-label">
                      On frequency — {activeAircraftList.length}
                    </div>
                    {activeAircraftList.map((item) => (
                      <TrafficRow
                        key={item.id}
                        aircraft={item}
                        isSelected={item.id === selectedAircraft?.id}
                        onSelect={() => setSelectedAircraftId(item.id)}
                      />
                    ))}
                  </>
                ) : null}
                {finishedAircraftList.length > 0 ? (
                  <>
                    <div className="cq-group-label">
                      Clear of sector — {finishedAircraftList.length}
                    </div>
                    {finishedAircraftList.map((item) => (
                      <TrafficRow
                        key={item.id}
                        aircraft={item}
                        isSelected={item.id === selectedAircraft?.id}
                        onSelect={() => setSelectedAircraftId(item.id)}
                      />
                    ))}
                  </>
                ) : null}
              </>
            )}
          </div>

          <div className="cq-counters">
            <div className="cq-ctr">
              <span className="cq-ctr-n">{visibleActiveCount}</span>
              <span className="cq-ctr-l">Active</span>
            </div>
            <div className="cq-ctr">
              <span className="cq-ctr-n">{visibleHoldingCount}</span>
              <span className="cq-ctr-l">Hold</span>
            </div>
            <div className="cq-ctr">
              <span className="cq-ctr-n">{routeOptions.length}</span>
              <span className="cq-ctr-l">Routes</span>
            </div>
          </div>
        </aside>

        <section className="cq-map">
          {scenarioQuery.isError ? (
            <div className="traffic-map-note">
              Scenario overlay unavailable: {describeError(scenarioQuery.error)}
            </div>
          ) : null}
          <TrafficMap
            aircraft={filteredAircraft}
            overlay={scenarioOverlay}
            selectedAircraftId={selectedAircraft?.id ?? null}
            aircraftLabelDirections={aircraftLabelDirections}
            onSelect={setSelectedAircraftId}
            onInspect={handleMapInspect}
            isMeasureMode={isMeasureMode}
            measurementPoints={measurementPoints}
            onMeasurePick={handleMeasurementPick}
          />
          <button
            type="button"
            className={isMeasureMode ? "cq-map-measure-btn on" : "cq-map-measure-btn"}
            onClick={() => setIsMeasureMode((currentValue) => !currentValue)}
          >
            Measure
          </button>
          {practiceConfig ? (
            <PracticePanel config={practiceConfig} outcome={practiceOutcome} />
          ) : null}
          {simulateConfig && metadataAirspaceId && metadataScenarioTemplateId ? (
            <SimulatePanel
              config={simulateConfig}
              summary={simulateSummary}
              airspaceId={metadataAirspaceId}
              scenarioId={metadataScenarioTemplateId}
            />
          ) : null}
        </section>

        <aside className="cq-detail">
          <div className="cq-detail-head">
            <div className="cq-detail-label">Selected aircraft</div>
            <div className="cq-detail-cs">
              <h2>{selectedAircraftLabel}</h2>
              {selectedAircraft ? (
                <span
                  className={`cq-dsb ${
                    selectedAircraft.status === "active"
                      ? "cq-dsb-act"
                      : selectedAircraft.status === "holding"
                        ? "cq-dsb-hld"
                        : "cq-dsb-fin"
                  }`}
                >
                  {formatLabel(selectedAircraft.status)}
                </span>
              ) : null}
            </div>
            <div className="cq-tabs">
              <button
                type="button"
                className={activeTab === "state" ? "cq-tab active" : "cq-tab"}
                onClick={() => setActiveTab("state")}
              >
                State
              </button>
              <button
                type="button"
                className={activeTab === "clearances" ? "cq-tab active" : "cq-tab"}
                onClick={() => setActiveTab("clearances")}
              >
                Clearances
              </button>
              {showDespatchTab ? (
                <button
                  type="button"
                  className={activeTab === "despatch" ? "cq-tab active" : "cq-tab"}
                  onClick={() => setActiveTab("despatch")}
                >
                  Despatch
                </button>
              ) : null}
            </div>
          </div>

          <div className="cq-detail-body">
            {activeTab === "state" ? (
              <>
                {selectedAircraft && selectedAircraftLevelTrend ? (
                  <div className="cq-dg">
                    <div className="cq-dg-cell">
                      <div className="cq-dg-k">Type</div>
                      <div className="cq-dg-v">{selectedAircraft.aircraft_type ?? "UNKNOWN"}</div>
                    </div>
                    <div className="cq-dg-cell">
                      <div className="cq-dg-k">Route</div>
                      <div className="cq-dg-v">{selectedAircraft.route_id}</div>
                    </div>
                    <div className="cq-dg-cell">
                      <div className="cq-dg-k">Flow</div>
                      <div className="cq-dg-v">{formatLabel(selectedAircraft.traffic_flow)}</div>
                    </div>
                    <div className="cq-dg-cell">
                      <div className="cq-dg-k">Level</div>
                      <div className="cq-dg-v g">{selectedAircraftLevelTrend.label}</div>
                    </div>
                    <div className="cq-dg-cell">
                      <div className="cq-dg-k">Vertical</div>
                      <div className="cq-dg-v">
                        {selectedAircraftLevelTrend.status} · {selectedAircraftLevelTrend.rate}
                      </div>
                    </div>
                    <div className="cq-dg-cell">
                      <div className="cq-dg-k">Speed</div>
                      <div className="cq-dg-v g">{selectedAircraft.speed_kt.toFixed(0)} kt</div>
                    </div>
                    <div className="cq-dg-cell">
                      <div className="cq-dg-k">Heading</div>
                      <div className="cq-dg-v">
                        {formatHeading(selectedAircraft.heading_deg)}
                        {selectedAircraft.assigned_heading_deg !== null &&
                        selectedAircraft.assigned_heading_deg !== undefined
                          ? ` → ${formatHeading(selectedAircraft.assigned_heading_deg)}`
                          : ""}
                      </div>
                    </div>
                    <div className="cq-dg-cell">
                      <div className="cq-dg-k">Lateral</div>
                      <div className="cq-dg-v">
                        {formatLabel(selectedAircraft.lateral_mode)}
                        {selectedAircraft.assigned_radial_deg !== null &&
                        selectedAircraft.assigned_radial_deg !== undefined
                          ? ` · ${formatRadial(selectedAircraft.assigned_radial_deg)}`
                          : ""}
                        {selectedAircraft.radial_deviation_deg !== null &&
                        selectedAircraft.radial_deviation_deg !== undefined
                          ? ` · ${formatRadialDeviation(selectedAircraft.radial_deviation_deg)}`
                          : ""}
                        {selectedAircraft.radial_cross_track_nm !== null &&
                        selectedAircraft.radial_cross_track_nm !== undefined
                          ? ` · XTK ${Math.abs(selectedAircraft.radial_cross_track_nm).toFixed(1)} NM`
                          : ""}
                        {selectedAircraft.direct_to_fix_id
                          ? ` · DCT ${selectedAircraft.direct_to_fix_id}`
                          : ""}
                        {selectedAircraft.hold_fix_id
                          ? ` · HOLD ${selectedAircraft.hold_fix_id}`
                          : ""}
                      </div>
                    </div>
                    <div className="cq-dg-cell span2">
                      <div className="cq-dg-k">Center DME</div>
                      <div className="cq-dg-v bl">{selectedAircraftReferenceDme?.toFixed(1)} NM</div>
                    </div>
                    <div className="cq-dg-cell span2">
                      <div className="cq-dg-k">Position</div>
                      <div className="cq-dg-v">
                        {selectedAircraft.position_dd[0].toFixed(3)},{" "}
                        {selectedAircraft.position_dd[1].toFixed(3)}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="cq-note" style={{ padding: "13px" }}>
                    {filteredAircraft.length === 0
                      ? "No visible aircraft match the current filter set."
                      : "Select an aircraft from the map or rail."}
                  </p>
                )}

                <div className="cq-sec">
                  <div className="cq-sec-title">Label position</div>
                  <div className="cq-lbl-grid">
                    {(["left", "right", "top", "bottom"] as const).map((direction) => (
                      <button
                        key={direction}
                        type="button"
                        className={
                          selectedAircraft &&
                          aircraftLabelDirections[selectedAircraft.id] === direction
                            ? "cq-lbl-btn active"
                            : "cq-lbl-btn"
                        }
                        disabled={!selectedAircraft}
                        onClick={() => setSelectedAircraftLabelDirection(direction)}
                      >
                        {formatLabel(direction)}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="cq-sec">
                  <div className="cq-sec-title">Map tools</div>
                  {inspectTarget ? (
                    <div className="cq-inspect-card">
                      <span>{formatLabel(inspectTarget.type)}</span>
                      <strong>{inspectTarget.name}</strong>
                      <small>{inspectTarget.detail}</small>
                      {inspectTarget.position ? (
                        <small>
                          {formatPosition(inspectTarget.position)} · Center{" "}
                          {calculateDistanceNm(
                            referenceFixPosition,
                            inspectTarget.position,
                          ).toFixed(1)}{" "}
                          NM
                        </small>
                      ) : null}
                    </div>
                  ) : (
                    <p className="cq-note">Click a route or fix to inspect it.</p>
                  )}
                  <div className="cq-measure-card">
                    <span>{isMeasureMode ? "Measurement active" : "Measurement"}</span>
                    <strong>
                      {measurementDistanceNm !== null
                        ? `${measurementDistanceNm.toFixed(1)} NM`
                        : measurementPoints.length === 1
                          ? "Pick second point"
                          : "Pick two points"}
                    </strong>
                    {measurementPoints.length > 0 ? (
                      <small>{measurementPoints.map((point) => point.label).join(" → ")}</small>
                    ) : (
                      <small>Use aircraft or fixes on the map.</small>
                    )}
                  </div>
                  <button
                    type="button"
                    className="cq-clr-btn full"
                    onClick={clearMeasurement}
                    disabled={measurementPoints.length === 0}
                  >
                    Clear measurement
                  </button>
                </div>
              </>
            ) : null}

            {activeTab === "clearances" ? (
              <>
                {showSpeedForm ? (
                  <form className="cq-sec" onSubmit={handleSetSpeed}>
                    <div className="cq-sec-title">Speed restriction</div>
                    <div className="cq-clr-row">
                      <input
                        className="cq-clr-input"
                        aria-label="Assigned speed"
                        value={setSpeedValue}
                        onChange={(event) => setSetSpeedValue(event.target.value)}
                        type="number"
                        min="1"
                        step="1"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      />
                      <button
                        type="submit"
                        className="cq-clr-btn"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      >
                        Assign Speed
                      </button>
                    </div>
                  </form>
                ) : null}

                {showFlightLevelForm ? (
                  <form className="cq-sec" onSubmit={handleSetFlightLevel}>
                    <div className="cq-sec-title">Cleared to flight level</div>
                    <div className="cq-clr-row">
                      <input
                        className="cq-clr-input"
                        value={setFlightLevelValue}
                        onChange={(event) => setSetFlightLevelValue(event.target.value)}
                        type="number"
                        min="0"
                        step="1"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      />
                      <button
                        type="submit"
                        className="cq-clr-btn"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      >
                        {flightLevelActionLabel}
                      </button>
                    </div>
                  </form>
                ) : null}

                {showTurnControls ? (
                  <div className="cq-sec">
                    <div className="cq-sec-title">Turn amount (deg)</div>
                    <div className="cq-clr-row">
                      <input
                        className="cq-clr-input"
                        aria-label="Turn amount in degrees"
                        value={turnAmountValue}
                        onChange={(event) => setTurnAmountValue(event.target.value)}
                        type="number"
                        min="1"
                        max="180"
                        step="1"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      />
                    </div>
                    <div className="cq-clr-row">
                      <button
                        type="button"
                        className="cq-clr-btn"
                        disabled={!selectedAircraft || commandMutation.isPending}
                        onClick={() => handleTurn("left")}
                      >
                        ◄ Turn Left
                      </button>
                      <button
                        type="button"
                        className="cq-clr-btn"
                        disabled={!selectedAircraft || commandMutation.isPending}
                        onClick={() => handleTurn("right")}
                      >
                        Turn Right ►
                      </button>
                    </div>
                  </div>
                ) : null}

                {showHeadingForm ? (
                  <form className="cq-sec" onSubmit={handleAssignHeading}>
                    <div className="cq-sec-title">Heading</div>
                    <div className="cq-clr-row">
                      <input
                        className="cq-clr-input"
                        value={setHeadingValue}
                        onChange={(event) => setSetHeadingValue(event.target.value)}
                        type="number"
                        min="0"
                        max="359"
                        step="1"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      />
                      <button
                        type="submit"
                        className="cq-clr-btn"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      >
                        Turn Heading
                      </button>
                    </div>
                  </form>
                ) : null}

                {showRadialForm ? (
                  <form className="cq-sec" onSubmit={handleAssignRadial}>
                    <div className="cq-sec-title">Radial</div>
                    <div className="cq-clr-row">
                      <input
                        className="cq-clr-input"
                        value={setRadialValue}
                        onChange={(event) => setSetRadialValue(event.target.value)}
                        type="number"
                        min="0"
                        max="359"
                        step="1"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      />
                      <button
                        type="submit"
                        className="cq-clr-btn"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      >
                        Intercept Radial
                      </button>
                    </div>
                  </form>
                ) : null}

                {showDirectToForm ? (
                  <form className="cq-sec" onSubmit={handleDirectTo}>
                    <div className="cq-sec-title">Direct to fix</div>
                    <div className="cq-clr-row">
                      <input
                        className="cq-clr-input"
                        style={{ width: "auto", flex: 1 }}
                        value={directToFixValue}
                        onChange={(event) => setDirectToFixValue(event.target.value)}
                        placeholder="NRV_VOR"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      />
                      <button
                        type="submit"
                        className="cq-clr-btn"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      >
                        Direct To
                      </button>
                    </div>
                  </form>
                ) : null}

                {showHoldForm ? (
                  <form className="cq-sec" onSubmit={handleHoldAtFix}>
                    <div className="cq-sec-title">Hold at fix</div>
                    <div className="cq-clr-row">
                      <input
                        className="cq-clr-input"
                        style={{ width: "auto", flex: 1 }}
                        value={holdFixValue}
                        onChange={(event) => setHoldFixValue(event.target.value)}
                        placeholder="NRV_VOR"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      />
                      <button
                        type="submit"
                        className="cq-clr-btn"
                        disabled={!selectedAircraft || commandMutation.isPending}
                      >
                        Hold
                      </button>
                    </div>
                  </form>
                ) : null}

                {showRouteSection ? (
                  <div className="cq-sec">
                    <div className="cq-sec-title">Route</div>
                    <button
                      type="button"
                      className="cq-clr-btn full"
                      disabled={!selectedAircraft || commandMutation.isPending}
                      onClick={handleResumeRoute}
                    >
                      Resume Nav
                    </button>
                    <button
                      type="button"
                      className="cq-clr-btn full"
                      disabled={!selectedAircraft || commandMutation.isPending}
                      onClick={handleExitHold}
                    >
                      Exit Hold
                    </button>
                  </div>
                ) : null}

                {commandMutation.isError ? (
                  <p className="cq-error">{describeError(commandMutation.error)}</p>
                ) : null}
              </>
            ) : null}

            {activeTab === "despatch" && showDespatchTab ? (
              <form className="cq-sec" onSubmit={handleAddAircraft}>
                <div className="cq-sec-title">Despatch traffic</div>
                <div className="cq-inj-grid">
                  <div className="cq-inj-field">
                    <span className="cq-inj-label">Aircraft ID</span>
                    <input
                      className="cq-inj-input"
                      value={addAircraftId}
                      onChange={(event) => setAddAircraftId(event.target.value)}
                      placeholder="AC900"
                    />
                  </div>
                  <div className="cq-inj-field">
                    <span className="cq-inj-label">Callsign</span>
                    <input
                      className="cq-inj-input"
                      value={addCallsign}
                      onChange={(event) => setAddCallsign(event.target.value)}
                      placeholder="OPS900"
                    />
                  </div>
                  <div className="cq-inj-field">
                    <span className="cq-inj-label">Type</span>
                    <input
                      className="cq-inj-input"
                      value={addAircraftType}
                      onChange={(event) => setAddAircraftType(event.target.value)}
                      placeholder="B737"
                    />
                  </div>
                  <div className="cq-inj-field">
                    <span className="cq-inj-label">Route ID</span>
                    <input
                      className="cq-inj-input"
                      value={addRouteId}
                      onChange={(event) => setAddRouteId(event.target.value)}
                      placeholder="UL602"
                    />
                  </div>
                  <div className="cq-inj-field">
                    <span className="cq-inj-label">IAS (kt)</span>
                    <input
                      className="cq-inj-input"
                      value={addSpeedKt}
                      onChange={(event) => setAddSpeedKt(event.target.value)}
                      type="number"
                      min="1"
                      step="1"
                    />
                  </div>
                  <div className="cq-inj-field">
                    <span className="cq-inj-label">Flight level</span>
                    <input
                      className="cq-inj-input"
                      value={addFlightLevel}
                      onChange={(event) => setAddFlightLevel(event.target.value)}
                      type="number"
                      min="0"
                      step="1"
                      placeholder="350"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="cq-despatch-btn"
                  disabled={commandMutation.isPending}
                >
                  ↪ Despatch traffic
                </button>
              </form>
            ) : null}
          </div>
        </aside>

        <div className="cq-log">
          <div className="cq-log-head">
            <div className="cq-log-head-dot" />
            <h2 className="cq-log-title">Command History</h2>
            <span className="cq-log-count">
              {commandHistory.length} entr{commandHistory.length === 1 ? "y" : "ies"}
            </span>
          </div>
          <div className="cq-log-header">
            <span>Time</span>
            <span>Callsign</span>
            <span>Command</span>
            <span>Value</span>
          </div>
          <div className="cq-log-scroll">
            {commandHistory.length === 0 ? (
              <p className="cq-log-empty">No commands issued yet this session.</p>
            ) : (
              commandHistory.map((result) => {
                const reason = resolveCommandReason(result);
                return (
                  <div className="cq-log-row" key={result.command.id}>
                    <span className="cq-log-time">
                      {formatTimestamp(result.command.created_at)}
                    </span>
                    <span className="cq-log-cs">
                      {resolveCommandTarget(result, aircraft)}
                    </span>
                    <span className="cq-log-cmd">
                      {formatCommandAction(result.command.command_type)}
                    </span>
                    <span className="cq-log-val">
                      <span className="cq-log-state">{formatLabel(result.result.state)}</span>
                      {reason ? (
                        <>
                          {" · "}
                          <span className="cq-log-reason">{reason}</span>
                        </>
                      ) : null}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {toast ? (
        <div className={toast.isError ? "cq-toast err" : "cq-toast"}>
          ↪ {toast.message}
        </div>
      ) : null}
    </div>
  );
}

function TrafficRow({
  aircraft,
  isSelected,
  onSelect,
}: {
  aircraft: RunAircraftStateResponse;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const flowTone = aircraft.traffic_flow.toLowerCase();
  const dotClass = flowTone.includes("inbound")
    ? "cq-row-dot cq-dot-g"
    : flowTone.includes("outbound")
      ? "cq-row-dot cq-dot-a"
      : flowTone.includes("transit")
        ? "cq-row-dot cq-dot-x"
        : "cq-row-dot cq-dot-x";

  return (
    <button
      type="button"
      className={isSelected ? "cq-row selected" : "cq-row"}
      onClick={onSelect}
    >
      <div className={dotClass} />
      <div>
        <div className="cq-row-cs">{aircraft.callsign ?? aircraft.id}</div>
        <div className="cq-row-sub">
          {aircraft.route_id} · {formatLabel(aircraft.traffic_flow)}
        </div>
      </div>
      <div>
        <div className="cq-row-fl">{resolveFlightLevelTrend(aircraft).label.replaceAll(" ", "")}</div>
        <div className="cq-row-spd">{aircraft.speed_kt.toFixed(0)} kt</div>
      </div>
    </button>
  );
}
