import { Link, useNavigate } from "react-router-dom";

import { getLearnProgress } from "../lib/learnProgress";
import "./LearnPage.css";
import "./CrossingTrafficIntroPage.css";

const objectives = [
  "identify converging traffic",
  "understand the required separation",
  "issue a resolution",
  "observe the result",
];

const CONCEPT_ID = "crossing_traffic";

function learnStatusLabel(): string {
  const progress = getLearnProgress(CONCEPT_ID);
  if (!progress || !progress.started) {
    return "Not started";
  }
  return progress.completed ? "Completed" : "In progress";
}

export function CrossingTrafficIntroPage() {
  const navigate = useNavigate();
  const learnStatus = learnStatusLabel();

  return (
    <div className="learn-page">
      <nav className="learn-nav">
        <Link to="/lessons" className="learn-brand">
          AirSpaceSim
        </Link>
        <button type="button" className="learn-signin">
          Sign in
        </button>
      </nav>

      <main className="intro-main">
        <p className="intro-eyebrow">Learn</p>
        <h1 className="intro-title">Crossing Traffic</h1>
        <p className="intro-desc">
          Two aircraft are converging at the same level. Learn how to recognise the developing
          conflict and resolve it before separation is lost.
        </p>

        <ul className="intro-objectives">
          {objectives.map((objective) => (
            <li key={objective}>{objective}</li>
          ))}
        </ul>

        <button
          type="button"
          className="intro-start-btn"
          onClick={() => navigate("/lessons/crossing-traffic/learn")}
        >
          Start learning
        </button>

        <div className="ct-progression">
          <h2 className="ct-progression-title">Crossing Traffic</h2>
          <Link to="/lessons/crossing-traffic/learn" className="ct-progression-row">
            <span>Learn</span>
            <span className="ct-progression-status">{learnStatus}</span>
          </Link>
          <Link to="/lessons/crossing-traffic/practice" className="ct-progression-row">
            <span>Practice 1 — Conflict announced</span>
            <span className="ct-progression-status">→</span>
          </Link>
          <Link to="/lessons/crossing-traffic/practice-2" className="ct-progression-row">
            <span>Practice 2 — No conflict announcement</span>
            <span className="ct-progression-status">→</span>
          </Link>
        </div>
      </main>
    </div>
  );
}
