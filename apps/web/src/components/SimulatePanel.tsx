import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { createPracticeRun } from "../lib/api";
import type { SimulateConfig, SimulateSummaryState } from "../lib/simulateSummary";

function formatDuration(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes} min ${seconds} sec`;
}

export function SimulatePanel({
  config,
  summary,
  airspaceId,
  scenarioId,
}: {
  config: SimulateConfig;
  summary: SimulateSummaryState;
  airspaceId: string;
  scenarioId: string;
}) {
  const navigate = useNavigate();

  const runAgainMutation = useMutation({
    mutationFn: () =>
      createPracticeRun({
        airspace_id: airspaceId,
        scenario_id: scenarioId,
        name: config.title,
      }),
    onSuccess: (run) => {
      navigate(`/runs/${run.id}`);
    },
  });

  if (!summary.ready) {
    return null;
  }

  return (
    <div className="cq-pp">
      <div className="cq-pp-head">
        <span className="cq-pp-title">Simulation complete</span>
      </div>
      <div className="cq-pp-body">
        <div className="cq-pp-row">
          <span>Duration</span>
          <strong>{formatDuration(summary.durationSeconds)}</strong>
        </div>
        <div className="cq-pp-row">
          <span>Aircraft in simulation</span>
          <strong>{summary.aircraftInSimulation}</strong>
        </div>
        <div className="cq-pp-row">
          <span>Instructions issued</span>
          <strong>{summary.instructionsIssued}</strong>
        </div>
        <div className="cq-pp-row">
          <span>Losses of separation</span>
          <strong className={summary.lossOfSeparationCount > 0 ? "warn" : ""}>
            {summary.lossOfSeparationCount}
          </strong>
        </div>
        <div className="cq-pp-actions">
          <button
            type="button"
            className="cq-pp-next"
            disabled={runAgainMutation.isPending}
            onClick={() => runAgainMutation.mutate()}
          >
            {runAgainMutation.isPending ? "Starting…" : "Run again"}
          </button>
          <Link to="/simulate" className="cq-pp-next">
            Back to Simulate
          </Link>
        </div>
        {runAgainMutation.isError ? (
          <p className="cq-pp-note">Could not start a new run. Try again.</p>
        ) : null}
      </div>
    </div>
  );
}
