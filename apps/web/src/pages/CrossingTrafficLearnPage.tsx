import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { TrafficMap, type AircraftLabelDirection } from "../components/TrafficMap";
import {
  createPracticeRun,
  getRun,
  getRunState,
  getScenario,
  pauseRun,
  resumeRun,
  submitRunCommand,
} from "../lib/api";
import {
  REQUIRED_HORIZONTAL_SEPARATION_NM,
  REQUIRED_VERTICAL_SEPARATION_FT,
  distanceNm,
} from "../lib/conflict";
import { describeError } from "../lib/format";
import { saveLearnProgress } from "../lib/learnProgress";
import { filterOverlayByRouteIds, parseScenarioMapOverlay } from "../lib/scenario-map";
import "./RunDetailPage.css";
import "./CrossingTrafficLearnPage.css";

const AFR_ID = "AFR612";
const RAM_ID = "RAM401";
const TARGET_FLIGHT_LEVEL = 310;
const RESOLVED_FLIGHT_LEVEL_GAP = 10; // 10 FL units = 1,000 ft
const CONCEPT_ID = "crossing_traffic";
const CONCEPT_TITLE = "Crossing Traffic";
const TOTAL_STAGES = 5;

// The shared training_alpha airspace carries routes for other scenarios too.
// This lesson only wants the two converging tracks plus one extra route for
// visual activity — kept as a display-only filter here rather than a new
// backend concept, since it's purely about what the map shows.
const VISIBLE_ROUTE_IDS = ["X1", "X2", "A2"];

const LABEL_DIRECTIONS: Record<string, AircraftLabelDirection> = {
  [AFR_ID]: "left",
  [RAM_ID]: "right",
};

type Stage = 1 | 2 | 3 | 4 | 5;

const stageCopy: Record<Stage, { title: string; body: string }> = {
  1: {
    title: "Watch the traffic",
    body: "AFR612 and RAM401 are maintaining the same flight level and their tracks are converging.",
  },
  2: {
    title: "Developing conflict",
    body: "The aircraft are converging at the same level. The required horizontal separation is 10 NM.",
  },
  3: {
    title: "Resolve the conflict",
    body: "One possible solution is to change the level of AFR612 before the required separation is lost.",
  },
  4: {
    title: "Watch the result",
    body: "AFR612 is leaving FL330 and vertical separation is being established.",
  },
  5: {
    title: "Conflict resolved",
    body: "The aircraft were originally converging at the same level. Descending AFR612 established vertical separation before the required separation was lost.",
  },
};

function stageLabel(stage: Stage): string {
  return `Stage ${stage} of ${TOTAL_STAGES}`;
}


export function CrossingTrafficLearnPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [runId, setRunId] = useState<string | null>(null);
  const [stage, setStage] = useState<Stage>(1);
  const [selectedAircraftId, setSelectedAircraftId] = useState<string | null>(null);
  const [encounterMin, setEncounterMin] = useState<{
    horizontalNm: number;
    verticalFt: number;
  } | null>(null);

  const hasCreatedRun = useRef(false);
  const hasResumedForStage3 = useRef(false);
  const hasResolved = useRef(false);

  const createMutation = useMutation({
    mutationFn: () =>
      createPracticeRun({
        airspace_id: "training_alpha",
        lesson_id: "enroute_crossing_traffic_intro",
      }),
    onSuccess: async (run) => {
      await pauseRun(run.id);
      setRunId(run.id);
      saveLearnProgress({
        conceptId: CONCEPT_ID,
        title: CONCEPT_TITLE,
        stageLabel: stageLabel(1),
        stage: 1,
        totalStages: TOTAL_STAGES,
        started: true,
        completed: false,
      });
    },
  });

  useEffect(() => {
    if (hasCreatedRun.current) {
      return;
    }
    hasCreatedRun.current = true;
    createMutation.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runQuery = useQuery({
    queryKey: ["learn-run", runId],
    queryFn: () => getRun(runId ?? ""),
    enabled: Boolean(runId),
    refetchInterval: 4_000,
  });
  const stateQuery = useQuery({
    queryKey: ["learn-run", runId, "state"],
    queryFn: () => getRunState(runId ?? ""),
    enabled: Boolean(runId),
    refetchInterval: 1_000,
  });
  const scenarioQuery = useQuery({
    queryKey: ["learn-scenario", runQuery.data?.scenario_id],
    queryFn: () => getScenario(runQuery.data?.scenario_id ?? ""),
    enabled: Boolean(runQuery.data?.scenario_id),
  });

  const resumeMutation = useMutation({
    mutationFn: () => resumeRun(runId ?? ""),
  });

  const commandMutation = useMutation({
    mutationFn: (payload: { command_type: string; payload: Record<string, unknown> }) => {
      if (!runId) {
        throw new Error("Run id is missing.");
      }
      return submitRunCommand(runId, payload);
    },
    onSuccess: async (response) => {
      await queryClient.invalidateQueries({ queryKey: ["learn-run", runId, "state"] });
      const commandPayload = response.command.payload as Record<string, unknown>;
      if (
        response.command.command_type === "SET_FL" &&
        commandPayload.aircraft_id === AFR_ID &&
        response.result.state !== "rejected" &&
        stage === 3
      ) {
        setStage(4);
        saveLearnProgress({
          conceptId: CONCEPT_ID,
          title: CONCEPT_TITLE,
          stageLabel: stageLabel(4),
          stage: 4,
          totalStages: TOTAL_STAGES,
          started: true,
          completed: false,
        });
      }
    },
  });

  function handleTryPractice() {
    saveLearnProgress({
      conceptId: CONCEPT_ID,
      title: CONCEPT_TITLE,
      stageLabel: stageLabel(5),
      stage: 5,
      totalStages: TOTAL_STAGES,
      started: true,
      completed: true,
    });
    navigate("/lessons/crossing-traffic/practice");
  }

  const state = stateQuery.data;
  const aircraft = state?.aircraft ?? [];
  const afr = aircraft.find((item) => item.id === AFR_ID) ?? null;
  const ram = aircraft.find((item) => item.id === RAM_ID) ?? null;
  const overlay = filterOverlayByRouteIds(
    parseScenarioMapOverlay(scenarioQuery.data),
    VISIBLE_ROUTE_IDS,
  );

  // Track the real observed minimum horizontal separation (and the vertical
  // separation at that moment) once the live encounter is underway.
  useEffect(() => {
    if (!afr || !ram || stage < 3) {
      return;
    }
    const horizontalNm = distanceNm(afr.position_dd, ram.position_dd);
    const verticalFt = Math.abs(afr.flight_level - ram.flight_level) * 100;
    setEncounterMin((current) => {
      if (!current || horizontalNm < current.horizontalNm) {
        return { horizontalNm, verticalFt };
      }
      return current;
    });
  }, [afr, ram, stage]);

  // Stage 3 -> 4 requires the run to actually be moving so the descent has an
  // effect; resume it once, right when the resolution stage begins. The
  // encounter plays out over several simulated minutes, so the rate is
  // raised too — otherwise the trainee would wait minutes of wall-clock time
  // to see the aircraft actually pass each other.
  useEffect(() => {
    if (stage === 3 && runId && !hasResumedForStage3.current) {
      hasResumedForStage3.current = true;
      resumeMutation.mutate();
      commandMutation.mutate({
        command_type: "SET_SIMULATION_SPEED",
        payload: { sim_rate: 6 },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, runId]);

  // Stage 4 -> 5 once the aircraft have actually passed their closest point
  // of approach — checking only the flight-level gap would fire as soon as
  // the descent completes, often long before the two tracks actually cross.
  useEffect(() => {
    if (stage !== 4 || !afr || !ram || !encounterMin || hasResolved.current) {
      return;
    }
    const currentHorizontalNm = distanceNm(afr.position_dd, ram.position_dd);
    const pastClosestApproach = currentHorizontalNm > encounterMin.horizontalNm + 0.5;
    if (pastClosestApproach) {
      hasResolved.current = true;
      setStage(5);
      saveLearnProgress({
        conceptId: CONCEPT_ID,
        title: CONCEPT_TITLE,
        stageLabel: stageLabel(5),
        stage: 5,
        totalStages: TOTAL_STAGES,
        started: true,
        completed: false,
      });
    }
  }, [stage, afr, ram, encounterMin]);

  function goToStage(nextStage: Stage) {
    setStage(nextStage);
    saveLearnProgress({
      conceptId: CONCEPT_ID,
      title: CONCEPT_TITLE,
      stageLabel: stageLabel(nextStage),
      stage: nextStage,
      totalStages: TOTAL_STAGES,
      started: true,
      completed: false,
    });
  }

  function handleDescend() {
    commandMutation.mutate({
      command_type: "SET_FL",
      payload: {
        aircraft_id: AFR_ID,
        flight_level: TARGET_FLIGHT_LEVEL,
      },
    });
  }

  if (createMutation.isError) {
    return (
      <div className="console-page">
        <p className="cq-error" style={{ padding: 24 }}>
          Could not start the Crossing Traffic lesson: {describeError(createMutation.error)}
        </p>
        <Link to="/lessons/crossing-traffic" className="cq-btn" style={{ margin: 24 }}>
          ← Back
        </Link>
      </div>
    );
  }

  if (!runId || !state || !afr || !ram) {
    return (
      <div className="console-page">
        <p className="cq-note" style={{ padding: 24 }}>
          Setting up the traffic…
        </p>
      </div>
    );
  }

  const required = REQUIRED_HORIZONTAL_SEPARATION_NM;
  const copy = stageCopy[stage];
  const isAfrSelected = selectedAircraftId === AFR_ID;
  const showDescendPrompt = stage === 3 && isAfrSelected;
  const horizontalMaintained = encounterMin ? encounterMin.horizontalNm >= required : true;
  const verticalEstablished = encounterMin
    ? encounterMin.verticalFt >= REQUIRED_VERTICAL_SEPARATION_FT
    : false;
  const separationMaintained = horizontalMaintained || verticalEstablished;

  return (
    <div className="console-page">
      <nav className="cq-topbar">
        <Link to="/" className="cq-brand">
          AirSpaceSim
        </Link>
        <div className="cq-sep" />
        <div className="cq-run">
          LEARN <span className="cq-run-heading">Crossing Traffic</span>
        </div>
        <Link to="/lessons/crossing-traffic" className="cq-btn">
          ← Exit
        </Link>
      </nav>

      <div className="tp-body">
        <section className="cq-map tp-map">
          <TrafficMap
            aircraft={aircraft}
            overlay={overlay}
            selectedAircraftId={selectedAircraftId}
            aircraftLabelDirections={LABEL_DIRECTIONS}
            onSelect={setSelectedAircraftId}
            onInspect={() => undefined}
            isMeasureMode={false}
            measurementPoints={[]}
            onMeasurePick={() => undefined}
          />
        </section>

        <aside className="tp-panel">
          <div className="tp-progress">
            {([1, 2, 3, 4, 5] as Stage[]).map((item) => (
              <span
                key={item}
                className={
                  item === stage ? "tp-dot active" : item < stage ? "tp-dot done" : "tp-dot"
                }
              />
            ))}
          </div>

          <h2 className="tp-title">{copy.title}</h2>
          <p className="tp-copy">{copy.body}</p>

          {stage === 2 ? (
            <div className="tp-metrics">
              <div className="tp-metric">
                <span>Required horizontal separation</span>
                <strong>{required.toFixed(0)} NM</strong>
              </div>
            </div>
          ) : null}

          {stage === 3 ? (
            <div className="tp-action-block">
              <p className={isAfrSelected ? "tp-instruction done" : "tp-instruction"}>
                {isAfrSelected ? "AFR612 selected." : "Select AFR612."}
              </p>
              <div className="tp-select-row">
                {[AFR_ID, RAM_ID].map((id) => (
                  <button
                    key={id}
                    type="button"
                    className={
                      selectedAircraftId === id
                        ? "tp-chip active"
                        : id === AFR_ID && !isAfrSelected
                          ? "tp-chip pulse"
                          : "tp-chip"
                    }
                    onClick={() => setSelectedAircraftId(id)}
                  >
                    {id}
                  </button>
                ))}
              </div>

              {showDescendPrompt ? (
                <div className="tp-command pulse">
                  <p className="tp-instruction">Descend AFR612 to FL{TARGET_FLIGHT_LEVEL}.</p>
                  <div className="cq-clr-row">
                    <input
                      className="cq-clr-input"
                      value={TARGET_FLIGHT_LEVEL}
                      readOnly
                      aria-label="Target flight level"
                    />
                    <button
                      type="button"
                      className="cq-clr-btn"
                      disabled={commandMutation.isPending}
                      onClick={handleDescend}
                    >
                      Descend
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {stage === 5 ? (
            <>
              <div className="tp-metrics">
                <div className="tp-metric">
                  <span>Horizontal separation reached</span>
                  <strong>{encounterMin ? encounterMin.horizontalNm.toFixed(1) : "—"} NM</strong>
                </div>
                <div className="tp-metric">
                  <span>Vertical separation established</span>
                  <strong>{encounterMin ? encounterMin.verticalFt.toFixed(0) : "—"} ft</strong>
                </div>
                <div className="tp-metric">
                  <span>Required separation maintained</span>
                  <strong className={separationMaintained ? "" : "warn"}>
                    {separationMaintained ? "Yes" : "No"}
                  </strong>
                </div>
              </div>
              {!horizontalMaintained && verticalEstablished ? (
                <p className="tp-note">
                  Horizontal separation fell below 10 NM, but the aircraft were already
                  vertically separated.
                </p>
              ) : null}
            </>
          ) : null}

          <div className="tp-actions">
            {stage === 1 ? (
              <button type="button" className="tp-primary-btn" onClick={() => goToStage(2)}>
                Continue
              </button>
            ) : null}
            {stage === 2 ? (
              <button type="button" className="tp-primary-btn" onClick={() => goToStage(3)}>
                Continue
              </button>
            ) : null}
            {stage === 4 ? <p className="tp-waiting">Watching the descent…</p> : null}
            {stage === 5 ? (
              <button type="button" className="tp-primary-btn" onClick={handleTryPractice}>
                Try a similar scenario
              </button>
            ) : null}
          </div>
        </aside>
      </div>
    </div>
  );
}
