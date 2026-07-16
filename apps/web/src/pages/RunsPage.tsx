import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AppFrame } from "../components/AppFrame";
import {
  buildRunExportUrl,
  createRun,
  listRuns,
  listScenarios,
  startRun,
} from "../lib/api";
import { describeError, formatLabel, formatTimestamp } from "../lib/format";

export function RunsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [scenarioId, setScenarioId] = useState("");

  const runsQuery = useQuery({
    queryKey: ["runs"],
    queryFn: listRuns,
  });
  const scenariosQuery = useQuery({
    queryKey: ["scenarios"],
    queryFn: listScenarios,
  });

  const createRunMutation = useMutation({
    mutationFn: createRun,
    onSuccess: async (run) => {
      await queryClient.invalidateQueries({ queryKey: ["runs"] });
      setName("");
      navigate(`/runs/${run.id}`);
    },
  });

  const startRunMutation = useMutation({
    mutationFn: startRun,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["runs"] });
    },
  });

  const runs = runsQuery.data?.items ?? [];
  const scenarios = scenariosQuery.data?.items ?? [];
  const scenarioNames = new Map(
    scenarios.map((scenario) => [scenario.id, scenario.name]),
  );
  const activeRuns = runs.filter(
    (item) => item.status === "running" || item.status === "paused",
  );

  function handleCreateRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createRunMutation.mutate({
      name: name.trim() || null,
      scenario_id: scenarioId || null,
    });
  }

  return (
    <AppFrame>
      <section className="dashboard-metrics">
        <article>
          <span>Scenarios</span>
          <strong>{scenariosQuery.isPending ? "…" : scenarios.length}</strong>
        </article>
        <article>
          <span>Active runs</span>
          <strong>{runsQuery.isPending ? "…" : activeRuns.length}</strong>
        </article>
        <article>
          <span>Total runs</span>
          <strong>{runsQuery.isPending ? "…" : runs.length}</strong>
        </article>
      </section>

      <section className="hero-card hero-grid">
        <div>
          <p className="eyebrow">Runs</p>
          <h1>Simulation Deck</h1>
          <p className="hero-copy">
            Create draft sessions, launch live runs, and jump into the active
            simulator console without leaving the app.
          </p>
        </div>

        <form className="content-card inline-form" onSubmit={handleCreateRun}>
          <div className="field-row">
            <label className="field">
              <span className="field-label">Run name</span>
              <input
                className="field-input"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Morning flow calibration"
              />
            </label>

            <label className="field">
              <span className="field-label">Scenario source</span>
              <select
                className="field-input"
                value={scenarioId}
                onChange={(event) => setScenarioId(event.target.value)}
              >
                <option value="">Packaged default scenario</option>
                {scenarios.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="action-row">
            <button
              type="submit"
              className="button-primary"
              disabled={createRunMutation.isPending}
            >
              {createRunMutation.isPending ? "Creating…" : "Create Draft Run"}
            </button>
            <p className="field-help">
              Draft runs can start from a stored scenario or from the packaged
              default contracts.
            </p>
          </div>
          {createRunMutation.isError ? (
            <p className="error-panel">{describeError(createRunMutation.error)}</p>
          ) : null}
        </form>
      </section>

      {runsQuery.isError ? (
        <section className="content-card">
          <p className="error-panel">{describeError(runsQuery.error)}</p>
        </section>
      ) : runs.length === 0 && !runsQuery.isPending ? (
        <section className="content-card">
          <p className="empty-state">
            No runs are stored yet. Create a draft run above to start the deck.
          </p>
        </section>
      ) : (
        <section className="card-grid">
          {runs.map((run) => (
            <article key={run.id} className="content-card run-card">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Run</p>
                  <h2>{run.name ?? "Untitled Run"}</h2>
                </div>
                <span className={`status-pill status-${run.status}`}>
                  {formatLabel(run.status)}
                </span>
              </div>

              <div className="table-list">
                <div className="data-pair">
                  <span>Scenario</span>
                  <strong>
                    {scenarioNames.get(run.scenario_id ?? "") ??
                      "Packaged default"}
                  </strong>
                </div>
                <div className="data-pair">
                  <span>Created</span>
                  <strong>{formatTimestamp(run.created_at)}</strong>
                </div>
                <div className="data-pair">
                  <span>Simulation rate</span>
                  <strong>{run.sim_rate.toFixed(1)}x</strong>
                </div>
              </div>

              <div className="hero-actions">
                <Link to={`/runs/${run.id}`} className="button-primary button-compact">
                  Open Console
                </Link>
                {run.status === "draft" ? (
                  <button
                    type="button"
                    className="button-secondary button-compact"
                    disabled={startRunMutation.isPending}
                    onClick={() => startRunMutation.mutate(run.id)}
                  >
                    Launch
                  </button>
                ) : null}
                <a
                  href={buildRunExportUrl(run.id)}
                  className="button-secondary button-compact"
                >
                  CSV
                </a>
              </div>
            </article>
          ))}
        </section>
      )}
    </AppFrame>
  );
}
