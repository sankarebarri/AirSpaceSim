import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { AppFrame } from "../components/AppFrame";
import { createPracticeRun } from "../lib/api";

const lessonSteps = [
  {
    label: "1 Heading",
    title: "Heading is a direction to fly.",
    copy: "A heading instruction points the aircraft nose in a direction. If it is left on that heading, it can keep drifting away from the planned route.",
    phraseology: "Turn right heading 265.",
  },
  {
    label: "2 Radial",
    title: "Radial is a navigation line.",
    copy: "A radial instruction tells the aircraft to intercept a line from a navaid or fix. After capture, the aircraft tracks that line.",
    phraseology: "Intercept and follow radial 265.",
  },
  {
    label: "3 Compare",
    title: "The key difference is what happens after the turn.",
    copy: "Heading keeps the aircraft flying the assigned direction. Radial capture returns the aircraft to a defined navigation line.",
    phraseology: "Resume normal navigation.",
  },
  {
    label: "4 Try",
    title: "Practice it on this page.",
    copy: "Use the mini exercise below to compare heading drift, radial capture, and Resume Nav without starting the backend simulator.",
    phraseology: "ALP01, intercept and follow radial 265.",
  },
];

const checkQuestions = [
  {
    question: "Which instruction can keep drifting away from the planned route?",
    answer: "Heading. It tells the aircraft where to point, not which route line to capture.",
  },
  {
    question: "What should happen after radial capture?",
    answer: "The aircraft tracks the assigned radial line instead of continuing on the intercept heading.",
  },
  {
    question: "When you press Resume Nav, where should the aircraft return?",
    answer: "Back toward its planned route, not back to the last temporary radial.",
  },
];

const playbackCopy = {
  ready: {
    label: "Ready",
    instruction: "Both aircraft are established on Route Alpha / R250.",
    status: "Run the comparison first. Resume Normal Navigation becomes available after the aircraft have actually deviated.",
  },
  compare: {
    label: "Compare H265 and R265",
    instruction: "ALP01: turn right heading 265. ALP02: intercept and follow radial 265.",
    status: "ALP01 keeps drifting on heading 265. ALP02 captures R265, then follows that radial toward destination direction.",
  },
  resume: {
    label: "Resume Normal Navigation",
    instruction: "ALP01 and ALP02, resume normal navigation.",
    status: "Both aircraft start from their deviated positions, intercept the original route, then continue on Route Alpha / R250.",
  },
} as const;

type PlaybackMode = keyof typeof playbackCopy;

const playbackDurationSeconds = 10;

export function HeadingVersusRadialLessonPage() {
  const navigate = useNavigate();
  const [playbackMode, setPlaybackMode] = useState<PlaybackMode>("ready");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [deviationReady, setDeviationReady] = useState(false);
  const activePractice = playbackCopy[playbackMode];
  const canRunComparison = playbackMode === "ready" && !isRunning;
  const practiceRunMutation = useMutation({
    mutationFn: () =>
      createPracticeRun({
        airspace_id: "training_alpha",
        lesson_id: "enroute_heading_vs_radial_intro",
        name: "Heading Versus Radial Practice",
      }),
    onSuccess: (run) => {
      navigate(`/runs/${run.id}`);
    },
  });

  useEffect(() => {
    if (!isRunning) {
      return undefined;
    }

    const startedAt = Date.now();
    const interval = window.setInterval(() => {
      const nextElapsed = Math.min(
        playbackDurationSeconds,
        Math.floor((Date.now() - startedAt) / 1000),
      );
      setElapsedSeconds(nextElapsed);
      if (nextElapsed >= playbackDurationSeconds) {
        setIsRunning(false);
        if (playbackMode === "compare") {
          setDeviationReady(true);
        }
        if (playbackMode === "resume") {
          setDeviationReady(false);
        }
      }
    }, 160);

    return () => window.clearInterval(interval);
  }, [isRunning, playbackMode]);

  function runPlayback(nextMode: Exclude<PlaybackMode, "ready">) {
    setPlaybackMode(nextMode);
    setElapsedSeconds(0);
    setIsRunning(true);
    if (nextMode === "compare") {
      setDeviationReady(false);
    }
  }

  function resetPlayback() {
    setPlaybackMode("ready");
    setElapsedSeconds(0);
    setIsRunning(false);
    setDeviationReady(false);
  }

  return (
    <AppFrame pageClassName="lesson-page-shell">
      <section className="lesson-hero">
        <div>
          <p className="eyebrow">En-route · Beginner · 5 min</p>
          <h1>Heading Versus Radial</h1>
          <p>
            Learn the operational difference between assigning a heading and
            assigning a radial, then practice radial capture and normal navigation
            recovery directly on this page.
          </p>
        </div>
        <div className="lesson-hero-actions">
          <a href="#practice" className="button-primary">
            Start Practice
          </a>
          <Link to="/lessons" className="button-secondary">
            Back To Lessons
          </Link>
        </div>
      </section>

      <section className="lesson-objective">
        <div>
          <span>Objective</span>
          <strong>
            Understand when to use a heading instruction, when to use a radial
            instruction, and how Resume Nav should return the aircraft to its route.
          </strong>
        </div>
      </section>

      <section className="lesson-layout">
        <div className="lesson-flow">
          <div className="lesson-step-tabs" aria-label="Lesson steps">
            {lessonSteps.map((step) => (
              <a key={step.label} href={`#${step.label.replace(" ", "-").toLowerCase()}`}>
                {step.label}
              </a>
            ))}
          </div>

          {lessonSteps.map((step) => (
            <article
              className="lesson-step-card"
              id={step.label.replace(" ", "-").toLowerCase()}
              key={step.label}
            >
              <p className="eyebrow">{step.label}</p>
              <h2>{step.title}</h2>
              <p>{step.copy}</p>
              <div className="phraseology-card">
                <span>Phraseology example</span>
                <strong>{step.phraseology}</strong>
              </div>
            </article>
          ))}
        </div>

        <aside className="lesson-visual-panel">
          <div className="lesson-mini-map">
            <div className="mini-route mini-route-main" />
            <div className="mini-route mini-route-radial" />
            <div className="mini-heading-arrow" />
            <div className="mini-fix mini-fix-center">VOR</div>
            <div className="mini-aircraft mini-aircraft-heading">
              <span />
              <strong>Heading 265</strong>
            </div>
            <div className="mini-aircraft mini-aircraft-radial">
              <span />
              <strong>R265 captured</strong>
            </div>
            <div className="mini-label mini-label-route">Planned route</div>
            <div className="mini-label mini-label-radial">Radial line</div>
          </div>
          <div className="lesson-command-card">
            <span>Lesson practice mode</span>
            <strong>Frontend-first, live simulator ready</strong>
            <p>
              Use the page exercise without the API server, or launch a live
              Training Alpha run when the hosted backend is running.
            </p>
          </div>
        </aside>
      </section>

      <section className="lesson-check-section">
        <div className="landing-section-heading">
          <p className="eyebrow">Check Yourself</p>
          <h2>Three questions before you practice.</h2>
        </div>
        <div className="lesson-check-grid">
          {checkQuestions.map((item) => (
            <details className="lesson-check-card" key={item.question}>
              <summary>{item.question}</summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="lesson-practice-section" id="practice">
        <div className="landing-section-heading">
          <p className="eyebrow">Practice On This Page</p>
          <h2>See the difference without starting a run.</h2>
        </div>
        <div className="lesson-practice-demo">
          <div className={`practice-radar practice-radar-${playbackMode}`}>
            <div className="practice-route-line practice-route-alpha" />
            <div className="practice-radial-line" />
            <div className="practice-route-label practice-route-label-alpha">
              Route Alpha / R250
            </div>
            <div className="practice-route-label practice-route-label-radial">
              Temporary R265
            </div>
            <div className="practice-vor">VOR</div>
            <div className="practice-destination">DEST A</div>
            <div className="practice-legend" aria-label="Practice map legend">
              <span>
                <i className="practice-legend-route" />
                Route Alpha / R250
              </span>
              <span>
                <i className="practice-legend-radial" />
                Temporary R265
              </span>
              <span>
                <i className="practice-legend-heading" />
                H265 drift
              </span>
              <span>
                <i className="practice-legend-resume" />
                Resume NN
              </span>
            </div>
            <div className="practice-track practice-track-heading" />
            <div className="practice-track practice-track-radial" />
            <div className="practice-track practice-track-resume-one" />
            <div className="practice-track practice-track-resume-two" />
            <div className="practice-aircraft practice-aircraft-heading">
              <span />
              <strong>ALP01 | FL250</strong>
            </div>
            <div className="practice-aircraft practice-aircraft-radial">
              <span />
              <strong>ALP02 | FL250</strong>
            </div>
          </div>

          <div className="practice-control-panel">
            <div>
              <p className="eyebrow">Active Instruction</p>
              <h3>{activePractice.label}</h3>
              <p>{activePractice.instruction}</p>
            </div>
            <div className="practice-status-card">
              <span>What to observe</span>
              <strong>{activePractice.status}</strong>
            </div>
            <div className="practice-timer-card">
              <span>Playback</span>
              <strong>
                {elapsedSeconds}s / {playbackDurationSeconds}s
              </strong>
              <div>
                <i style={{ width: `${(elapsedSeconds / playbackDurationSeconds) * 100}%` }} />
              </div>
            </div>
            <div className="practice-command-buttons">
              <button
                className={playbackMode === "compare" ? "button-primary" : "button-secondary"}
                type="button"
                onClick={() => runPlayback("compare")}
                disabled={!canRunComparison}
                title={!canRunComparison ? "Reset before running a new comparison." : undefined}
              >
                Compare H265 vs R265
              </button>
              <button
                className={playbackMode === "resume" ? "button-primary" : "button-secondary"}
                type="button"
                onClick={() => runPlayback("resume")}
                disabled={isRunning || !deviationReady}
                title={
                  deviationReady
                    ? "Resume from the aircraft current deviated positions."
                    : "Run the comparison first."
                }
              >
                Resume Normal Navigation
              </button>
              <button
                className="button-secondary"
                type="button"
                onClick={resetPlayback}
                disabled={isRunning && elapsedSeconds < 1}
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="lesson-next-actions">
        <div>
          <p className="eyebrow">Next Step</p>
          <h2>Use the simulator after the concept is clear.</h2>
        </div>
        <div className="hero-actions">
          <Link to="/lessons" className="button-secondary">
            Back To Lessons
          </Link>
          <button
            className="button-primary"
            type="button"
            onClick={() => practiceRunMutation.mutate()}
            disabled={practiceRunMutation.isPending}
          >
            {practiceRunMutation.isPending
              ? "Opening Practice..."
              : "Open Live Simulator Practice"}
          </button>
        </div>
        {practiceRunMutation.isError ? (
          <p className="error-panel">
            Could not create the live practice run. Confirm the API server is
            running, then try again.
          </p>
        ) : null}
      </section>
    </AppFrame>
  );
}
