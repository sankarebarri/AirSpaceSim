import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getContinueLearningEntry, type LearnProgressEntry } from "../lib/learnProgress";
import "./HomePage.css";

interface PrimaryAction {
  key: string;
  label: string;
  description: string;
  href: string;
}

const primaryActions: PrimaryAction[] = [
  {
    key: "learn",
    label: "Learn",
    description: "Understand traffic situations through guided demonstrations and actions.",
    href: "/lessons",
  },
  {
    key: "practice",
    label: "Practice",
    description: "Work through traffic scenarios with progressively less assistance.",
    href: "/scenarios",
  },
  {
    key: "simulate",
    label: "Simulate",
    description: "Control predefined traffic freely in the simulation environment.",
    href: "/simulate",
  },
];

export function HomePage() {
  const [continueEntry, setContinueEntry] = useState<LearnProgressEntry | null>(null);

  useEffect(() => {
    setContinueEntry(getContinueLearningEntry());
  }, []);

  return (
    <div className="landing-page">
      <nav className="home-nav">
        <Link to="/" className="home-brand">
          AirSpaceSim
        </Link>
        <button type="button" className="home-signin">
          Sign in
        </button>
      </nav>

      <main className="home-main">
        <h1 className="home-tagline">
          Learn traffic.
          <br />
          Control traffic.
        </h1>

        <div className="home-actions">
          {primaryActions.map((action) => (
            <Link to={action.href} className="home-action" key={action.key}>
              <span className="home-action-label">{action.label}</span>
              <p className="home-action-desc">{action.description}</p>
            </Link>
          ))}
        </div>

        {continueEntry ? (
          <div className="home-continue">
            <div className="home-continue-label">Continue training</div>
            <div className="home-continue-card">
              <div>
                <div className="home-continue-title">{continueEntry.title}</div>
                <div className="home-continue-stage">{continueEntry.stageLabel}</div>
              </div>
              <Link to="/lessons/crossing-traffic/learn" className="home-continue-btn">
                Continue
              </Link>
            </div>
          </div>
        ) : null}
      </main>

      <footer className="home-footer">
        <span className="home-footer-brand">AirSpaceSim</span>
        <p className="home-footer-legal">
          Training and visualisation software only. Not for real aircraft operations or live
          traffic control. All airspaces and scenarios are fictional.
        </p>
      </footer>
    </div>
  );
}
