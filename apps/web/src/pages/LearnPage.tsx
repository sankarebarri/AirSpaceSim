import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getContinueLearningEntry, type LearnProgressEntry } from "../lib/learnProgress";
import "./LearnPage.css";

interface LearnConcept {
  key: string;
  title: string;
  description: string;
  href: string;
}

const concepts: LearnConcept[] = [
  {
    key: "crossing_traffic",
    title: "Crossing Traffic",
    description:
      "Understand how two aircraft on converging tracks can develop a conflict and learn one way to resolve it.",
    href: "/lessons/crossing-traffic",
  },
];

export function LearnPage() {
  const [continueEntry, setContinueEntry] = useState<LearnProgressEntry | null>(null);

  useEffect(() => {
    setContinueEntry(getContinueLearningEntry());
  }, []);

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
          <h1>Learn</h1>
          <p>Understand traffic situations through guided simulation.</p>
        </div>

        {continueEntry ? (
          <section className="learn-continue">
            <div className="learn-continue-label">Continue learning</div>
            <div className="learn-continue-card">
              <div>
                <div className="learn-continue-title">{continueEntry.title}</div>
                <div className="learn-continue-stage">{continueEntry.stageLabel}</div>
              </div>
              <Link to="/lessons/crossing-traffic/learn" className="learn-continue-btn">
                Continue
              </Link>
            </div>
          </section>
        ) : null}

        <section className="learn-concepts">
          <div className="learn-concepts-label">Available learning concepts</div>
          <div className="learn-concepts-grid">
            {concepts.map((concept) => (
              <Link to={concept.href} className="learn-concept-card" key={concept.key}>
                <span className="learn-concept-title">{concept.title}</span>
                <p className="learn-concept-desc">{concept.description}</p>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
