import { Link } from "react-router-dom";

import { SIMULATE_SCENARIOS } from "../lib/simulateScenarios";
import "./LearnPage.css";
import "./SimulatePage.css";

export function SimulatePage() {
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

      <main className="learn-main">
        <div className="learn-heading">
          <h1>Simulate</h1>
          <p>Control predefined traffic situations using the AirSpaceSim simulation environment.</p>
        </div>

        <section className="learn-concepts">
          <div className="learn-concepts-label">Available simulations</div>
          <div className="learn-concepts-grid">
            {SIMULATE_SCENARIOS.map((scenario) => (
              <Link
                to={`/simulate/${scenario.slug}`}
                className="learn-concept-card"
                key={scenario.slug}
              >
                <span className="learn-concept-title">{scenario.title}</span>
                <p className="learn-concept-desc">{scenario.description}</p>
                <div className="sim-card-facts">
                  <span>{scenario.aircraftCount} aircraft</span>
                  <span>Predefined traffic</span>
                  <span>{scenario.mode}</span>
                </div>
                <span className="sim-card-btn">Open simulation</span>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
