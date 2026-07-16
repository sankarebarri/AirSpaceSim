import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import type { PracticeConfig, PracticeOutcomeState } from "../lib/practiceOutcome";

function formatRatingLabel(outcome: PracticeOutcomeState): string {
  switch (outcome.rating) {
    case "safe_effective":
      return "SAFE AND EFFECTIVE";
    case "loss_of_separation":
      return "LOSS OF SEPARATION";
    default:
      return "RUN ENDED";
  }
}

function DebriefBody({ outcome }: { outcome: PracticeOutcomeState }) {
  if (outcome.separationMaintained === null) {
    return <p className="cq-pp-note">Run terminated before the encounter developed.</p>;
  }

  return (
    <>
      <div className="cq-pp-row">
        <span>Required separation maintained</span>
        <strong className={outcome.separationMaintained ? "" : "warn"}>
          {outcome.separationMaintained ? "Yes" : "No"}
        </strong>
      </div>
      <div className="cq-pp-row">
        <span>Conflict resolved before crossing</span>
        <strong className={outcome.conflictResolvedBeforeCrossing ? "" : "warn"}>
          {outcome.conflictResolvedBeforeCrossing ? "Yes" : "No"}
        </strong>
      </div>
      {outcome.separationMaintained ? (
        <>
          <div className="cq-pp-row">
            <span>Applicable separation used</span>
            <strong>{outcome.applicableForm === "vertical" ? "Vertical" : "Horizontal"}</strong>
          </div>
          <div className="cq-pp-row">
            <span>
              {outcome.applicableForm === "vertical"
                ? "Minimum vertical separation"
                : "Closest horizontal separation"}
            </span>
            <strong>
              {outcome.applicableForm === "vertical"
                ? `${outcome.closestVerticalFt?.toFixed(0)} ft`
                : `${outcome.closestHorizontalNm?.toFixed(1)} NM`}
            </strong>
          </div>
        </>
      ) : (
        <div className="cq-pp-row">
          <span>Closest applicable separation</span>
          <strong className="warn">{outcome.closestHorizontalNm?.toFixed(1)} NM</strong>
        </div>
      )}
      <div className="cq-pp-row">
        <span>Instructions issued</span>
        <strong>{outcome.commandCount}</strong>
      </div>
      <div className="cq-pp-row">
        <span>Outcome</span>
        <strong className={outcome.rating === "loss_of_separation" ? "warn" : ""}>
          {formatRatingLabel(outcome)}
        </strong>
      </div>
      {outcome.explanation ? <p className="cq-pp-note">{outcome.explanation}</p> : null}
    </>
  );
}

export function PracticePanel({
  config,
  outcome,
}: {
  config: PracticeConfig;
  outcome: PracticeOutcomeState;
}) {
  const [collapsed, setCollapsed] = useState(true);

  // Reveal the panel on its own once the run's outcome is ready — the
  // trainee shouldn't have to remember to check for the debrief.
  useEffect(() => {
    if (outcome.ready) {
      setCollapsed(false);
    }
  }, [outcome.ready]);

  if (collapsed) {
    return (
      <button
        type="button"
        className="cq-pp-pill"
        onClick={() => setCollapsed(false)}
      >
        {outcome.ready ? "DEBRIEF" : "OBJECTIVE"}
      </button>
    );
  }

  return (
    <div className="cq-pp">
      <div className="cq-pp-head">
        <span className="cq-pp-title">{outcome.ready ? "Practice debrief" : config.title}</span>
        <button
          type="button"
          className="cq-pp-toggle"
          onClick={() => setCollapsed(true)}
          aria-label="Collapse panel"
        >
          ▾
        </button>
      </div>
      <div className="cq-pp-body">
        {outcome.ready ? (
          <>
            <DebriefBody outcome={outcome} />
            {outcome.rating === "safe_effective" && config.next ? (
              <Link to={config.next.path} className="cq-pp-next">
                {config.next.label}
              </Link>
            ) : null}
          </>
        ) : (
          <>
            <p className="cq-pp-line">
              <span className="cq-pp-label">Objective</span> {config.objective}
            </p>
            {config.assistance ? (
              <p className="cq-pp-line">
                <span className="cq-pp-label">Assistance</span> {config.assistance}
              </p>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
