import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { createPracticeRun } from "../lib/api";
import { describeError } from "../lib/format";
import { getSimulateScenario } from "../lib/simulateScenarios";
import "./LearnPage.css";
import "./CrossingTrafficIntroPage.css";
import "./SimulatePage.css";

export function SimulateBriefPage() {
  const { scenarioSlug } = useParams();
  const navigate = useNavigate();
  const scenario = scenarioSlug ? getSimulateScenario(scenarioSlug) : null;

  const launchMutation = useMutation({
    mutationFn: () => {
      if (!scenario) {
        throw new Error("Simulation not found.");
      }
      return createPracticeRun({
        airspace_id: scenario.airspaceId,
        scenario_id: scenario.scenarioId,
        name: scenario.title,
      });
    },
    onSuccess: (run) => {
      navigate(`/runs/${run.id}`);
    },
  });

  if (!scenario) {
    return (
      <div className="learn-page">
        <nav className="learn-nav">
          <Link to="/" className="learn-brand">
            AirSpaceSim
          </Link>
          <button type="button" className="learn-signin">
            Sign in
          </button>
        </nav>
        <main className="intro-main">
          <p className="intro-eyebrow">Simulate</p>
          <h1 className="intro-title">Simulation not found</h1>
          <Link to="/simulate" className="intro-start-btn">
            Back to Simulate
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="learn-page">
      <nav className="learn-nav">
        <Link to="/" className="learn-brand">
          AirSpaceSim
        </Link>
        <button type="button" className="learn-signin">
          Sign in
        </button>
      </nav>

      <main className="intro-main">
        <p className="intro-eyebrow">Simulate</p>
        <h1 className="intro-title">{scenario.title}</h1>
        <p className="intro-desc">Control the traffic through the sector using the available clearances.</p>

        <div className="sim-brief-facts">
          <div>
            <span className="sim-brief-label">Traffic</span>
            <strong>{scenario.aircraftCount} aircraft</strong>
          </div>
          <div>
            <span className="sim-brief-label">Routes</span>
            <strong>{scenario.routeCount}</strong>
          </div>
          <div>
            <span className="sim-brief-label">Mode</span>
            <strong>{scenario.mode}</strong>
          </div>
        </div>

        <button
          type="button"
          className="intro-start-btn"
          disabled={launchMutation.isPending}
          onClick={() => launchMutation.mutate()}
        >
          {launchMutation.isPending ? "Launching…" : "Launch simulation"}
        </button>
        {launchMutation.isError ? (
          <p style={{ marginTop: 16, color: "#c0392b", fontSize: 13 }}>
            {describeError(launchMutation.error)}
          </p>
        ) : null}
      </main>
    </div>
  );
}
