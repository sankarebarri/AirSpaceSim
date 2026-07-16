import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { createPracticeRun } from "../lib/api";
import { describeError } from "../lib/format";
import "../pages/LearnPage.css";
import "../pages/CrossingTrafficIntroPage.css";

export function PracticeIntroScreen({
  eyebrow = "Practice",
  title,
  paragraphs,
  scenarioId,
  lessonId,
  runName,
}: {
  eyebrow?: string;
  title: string;
  paragraphs: string[];
  scenarioId: string;
  lessonId?: string;
  runName: string;
}) {
  const navigate = useNavigate();

  const beginMutation = useMutation({
    mutationFn: () =>
      createPracticeRun({
        airspace_id: "training_alpha",
        scenario_id: scenarioId,
        lesson_id: lessonId,
        name: runName,
      }),
    onSuccess: (run) => {
      navigate(`/runs/${run.id}`);
    },
  });

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
        <p className="intro-eyebrow">{eyebrow}</p>
        <h1 className="intro-title">{title}</h1>
        {paragraphs.map((paragraph) => (
          <p className="intro-desc" key={paragraph}>
            {paragraph}
          </p>
        ))}

        <button
          type="button"
          className="intro-start-btn"
          disabled={beginMutation.isPending}
          onClick={() => beginMutation.mutate()}
        >
          {beginMutation.isPending ? "Starting…" : "Begin"}
        </button>
        {beginMutation.isError ? (
          <p style={{ marginTop: 16, color: "#c0392b", fontSize: 13 }}>
            {describeError(beginMutation.error)}
          </p>
        ) : null}
      </main>
    </div>
  );
}
