// Generic data-driven lesson runner (LearnRunner). Renders any lesson served
// by the content API: observation, highlight, classification, and completion
// steps. Adding a lesson requires lesson JSON + locale keys only — no new
// React pages. Deliberately shows no prediction metrics (brief
// non-negotiable #10): no separation distances, no time-to-minimum figures.

import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { TrafficMap, type AircraftLabelDirection } from "../components/TrafficMap";
import {
  createPracticeRun,
  getRunState,
  getScenario,
  pauseRun,
  resumeRun,
  stopRun,
} from "../lib/api";
import { fetchCurriculum, fetchLesson, type LessonStep } from "../lib/content";
import { LanguageToggle, useI18n } from "../lib/i18n";
import { markLessonComplete } from "../lib/learnProgress";
import { filterOverlayByRouteIds, parseScenarioMapOverlay } from "../lib/scenario-map";
import "./LearnPage.css";
import "./LessonRunnerPage.css";

function desiredScenarioForStep(steps: LessonStep[], stepIndex: number): string | null {
  for (let index = stepIndex; index >= 0; index -= 1) {
    if (steps[index]?.scenario_id) {
      return steps[index].scenario_id ?? null;
    }
  }
  for (let index = stepIndex + 1; index < steps.length; index += 1) {
    if (steps[index]?.scenario_id) {
      return steps[index].scenario_id ?? null;
    }
  }
  return null;
}

export function LessonRunnerPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { conceptId, lessonId } = useParams<{
    conceptId: string;
    lessonId: string;
  }>();

  const curriculumQuery = useQuery({
    queryKey: ["curriculum"],
    queryFn: fetchCurriculum,
  });
  const concept = curriculumQuery.data?.families
    .flatMap((family) => family.concepts)
    .find((entry) => entry.id === conceptId);
  const airspaceId = concept?.airspace_id ?? null;

  const lessonQuery = useQuery({
    queryKey: ["lesson", airspaceId, lessonId],
    queryFn: () => fetchLesson(airspaceId ?? "", lessonId ?? ""),
    enabled: Boolean(airspaceId && lessonId),
  });
  const lesson = lessonQuery.data?.lesson;
  const steps = useMemo(() => lesson?.lesson_steps ?? [], [lesson]);

  const [stepIndex, setStepIndex] = useState(0);
  const [runId, setRunId] = useState<string | null>(null);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(null);
  const [selection, setSelection] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const isSwitchingRun = useRef(false);

  // Reset all lesson state when navigating between lessons.
  useEffect(() => {
    setStepIndex(0);
    setSelection(null);
  }, [lessonId]);

  const step: LessonStep | undefined = steps[stepIndex];
  const desiredScenarioId = useMemo(
    () => desiredScenarioForStep(steps, stepIndex),
    [steps, stepIndex],
  );

  // Create (or replace) the backing run when the step's scenario changes.
  useEffect(() => {
    if (!airspaceId || !desiredScenarioId) {
      return;
    }
    if (desiredScenarioId === activeScenarioId || isSwitchingRun.current) {
      return;
    }
    isSwitchingRun.current = true;
    const previousRunId = runId;
    (async () => {
      if (previousRunId) {
        try {
          await stopRun(previousRunId);
        } catch {
          // The previous run may already be finished; that is fine.
        }
      }
      const run = await createPracticeRun({
        airspace_id: airspaceId,
        scenario_id: desiredScenarioId,
      });
      setRunId(run.id);
      setActiveScenarioId(desiredScenarioId);
      setRunError(null);
    })()
      .catch((error: unknown) => {
        setRunError(error instanceof Error ? error.message : String(error));
      })
      .finally(() => {
        isSwitchingRun.current = false;
      });
  }, [airspaceId, desiredScenarioId, activeScenarioId, runId]);

  // Stop the live run when leaving the lesson entirely.
  useEffect(() => {
    return () => {
      if (runId) {
        stopRun(runId).catch(() => undefined);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stateQuery = useQuery({
    queryKey: ["lesson-run", runId, "state"],
    queryFn: () => getRunState(runId ?? ""),
    enabled: Boolean(runId),
    refetchInterval: 1_000,
  });
  const scenarioId = stateQuery.data?.run.scenario_id ?? null;
  const scenarioQuery = useQuery({
    queryKey: ["lesson-scenario", scenarioId],
    queryFn: () => getScenario(scenarioId ?? ""),
    enabled: Boolean(scenarioId),
  });

  // Match the simulation pause state to the step definition.
  const runtimeStatus = stateQuery.data?.runtime_status;
  useEffect(() => {
    if (!runId || !step) {
      return;
    }
    const desired = step.sim ?? "running";
    if (runtimeStatus === "running" && desired === "paused") {
      pauseRun(runId).catch(() => undefined);
    } else if (runtimeStatus === "paused" && desired === "running") {
      resumeRun(runId).catch(() => undefined);
    }
  }, [runId, step, runtimeStatus]);

  // Record completion once the learner reaches the completion step.
  useEffect(() => {
    if (step?.type === "complete" && conceptId && lessonId) {
      markLessonComplete(conceptId, lessonId);
    }
  }, [step, conceptId, lessonId]);

  const scenarioMetadata = scenarioQuery.data?.metadata_payload as
    | Record<string, unknown>
    | undefined;
  const learnMetadata = (scenarioMetadata?.learn ?? {}) as {
    visible_route_ids?: string[];
    labels?: Record<string, AircraftLabelDirection>;
  };
  const relationship = (scenarioMetadata?.traffic_relationship ?? null) as {
    type?: string;
  } | null;

  const overlay = useMemo(() => {
    const parsed = parseScenarioMapOverlay(scenarioQuery.data);
    return learnMetadata.visible_route_ids
      ? filterOverlayByRouteIds(parsed, learnMetadata.visible_route_ids)
      : parsed;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarioQuery.data, JSON.stringify(learnMetadata.visible_route_ids)]);

  const aircraft = stateQuery.data?.aircraft ?? [];
  const correctAnswer =
    step?.type === "classify"
      ? step.correct ?? relationship?.type ?? null
      : null;
  const isAnswered = selection !== null;
  const isCorrect = isAnswered && selection === correctAnswer;

  const advance = () => {
    setSelection(null);
    setStepIndex((index) => Math.min(index + 1, steps.length - 1));
  };

  if (!lesson || !step) {
    return (
      <div className="learn-page">
        <main className="learn-main">
          <p className="runner-status">
            {lessonQuery.isError || curriculumQuery.isError
              ? t("runner.error")
              : t("runner.loading")}
          </p>
        </main>
      </div>
    );
  }

  return (
    <div className="learn-page runner-page">
      <nav className="learn-nav">
        <Link to="/" className="learn-brand">
          AirSpaceSim
        </Link>
        <div className="learn-nav-actions">
          <LanguageToggle />
          <Link to={`/learn/${conceptId}`} className="learn-signin">
            {t("runner.backToConcept")}
          </Link>
        </div>
      </nav>

      <main className="runner-layout">
        <section className="runner-map" aria-label="Simulation">
          <TrafficMap
            aircraft={aircraft}
            overlay={overlay}
            selectedAircraftId={null}
            aircraftLabelDirections={learnMetadata.labels ?? {}}
            onSelect={() => undefined}
            onInspect={() => undefined}
            isMeasureMode={false}
            measurementPoints={[]}
            onMeasurePick={() => undefined}
          />
        </section>

        <aside className="runner-panel">
          <header className="runner-header">
            <h1>{t(lesson.title_key)}</h1>
            <span className="runner-progress">
              {t("runner.stepOf", {
                current: stepIndex + 1,
                total: steps.length,
              })}
            </span>
          </header>

          {runError ? <p className="runner-status runner-error">{runError}</p> : null}

          {step.type === "observe" ? (
            <div className="runner-step">
              <p className="runner-text">{t(step.text_key ?? "")}</p>
              <button type="button" className="runner-primary" onClick={advance}>
                {t("runner.continue")}
              </button>
            </div>
          ) : null}

          {step.type === "classify" ? (
            <div className="runner-step">
              <p className="runner-text runner-question">
                {t(step.question_key ?? "lessons.classify.question")}
              </p>
              <div className="runner-options" role="group">
                {(step.options ?? []).map((option) => {
                  const optionLabel = t(`lessons.classify.options.${option}`);
                  const tone = !isAnswered
                    ? ""
                    : option === correctAnswer
                      ? " runner-option-correct"
                      : option === selection
                        ? " runner-option-incorrect"
                        : "";
                  return (
                    <button
                      key={option}
                      type="button"
                      className={`runner-option${tone}`}
                      disabled={isAnswered}
                      onClick={() => setSelection(option)}
                    >
                      {optionLabel}
                    </button>
                  );
                })}
              </div>
              {isAnswered ? (
                <div
                  className={
                    isCorrect
                      ? "runner-feedback runner-feedback-correct"
                      : "runner-feedback runner-feedback-incorrect"
                  }
                >
                  <p className="runner-verdict">
                    {isCorrect ? t("runner.correct") : t("runner.incorrect")}
                  </p>
                  {!isCorrect && correctAnswer ? (
                    <p>
                      {t("runner.correctAnswerWas", {
                        answer: t(`lessons.classify.options.${correctAnswer}`),
                      })}
                    </p>
                  ) : null}
                  <p>{t(step.explanation_key ?? "")}</p>
                  <button type="button" className="runner-primary" onClick={advance}>
                    {t("runner.continue")}
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}

          {step.type === "complete" ? (
            <div className="runner-step runner-complete">
              <h2>{t(step.title_key ?? "")}</h2>
              <p className="runner-text">{t(step.text_key ?? "")}</p>
              {step.point_keys ? (
                <ul className="runner-points">
                  {step.point_keys.map((key) => (
                    <li key={key}>{t(key)}</li>
                  ))}
                </ul>
              ) : null}
              <div className="runner-actions">
                {step.next_lesson_id ? (
                  <button
                    type="button"
                    className="runner-primary"
                    onClick={() =>
                      navigate(`/learn/${conceptId}/${step.next_lesson_id}`)
                    }
                  >
                    {t("runner.nextLesson")}
                  </button>
                ) : (
                  <Link to="/lessons/crossing-traffic" className="runner-primary">
                    {t("runner.continueToCrossing")}
                  </Link>
                )}
                <Link to={`/learn/${conceptId}`} className="runner-secondary">
                  {t("runner.backToConcept")}
                </Link>
                <Link to="/lessons" className="runner-secondary">
                  {t("runner.backToFamily")}
                </Link>
              </div>
            </div>
          ) : null}
        </aside>
      </main>
    </div>
  );
}
