// The generic lesson runner: renders any lesson from content-API data,
// drives the classification flow, and shows no prediction metrics.

import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppRoutes } from "../src/app/routes";
import { LanguageProvider } from "../src/lib/i18n";
import { installJsonFetchMock } from "./http";

const routerFuture = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

const API = "http://127.0.0.1:8000";

const CURRICULUM = {
  families: [
    {
      id: "separation_fundamentals",
      title_key: "curriculum.separation_fundamentals.title",
      description_key: "curriculum.separation_fundamentals.description",
      service: "enroute",
      concepts: [
        {
          id: "traffic_relationships",
          status: "available",
          title_key: "curriculum.traffic_relationships.title",
          description_key: "curriculum.traffic_relationships.description",
          airspace_id: "training_alpha",
          lessons: [
            {
              lesson_id: "tr_same_track",
              title_key: "lessons.tr_same_track.title",
            },
          ],
        },
      ],
    },
  ],
};

const LESSON = {
  airspace_id: "training_alpha",
  lesson_id: "tr_same_track",
  lesson: {
    id: "tr_same_track",
    title: "Same-Track Traffic",
    title_key: "lessons.tr_same_track.title",
    duration_minutes: 4,
    concept: "traffic_relationships",
    lesson_steps: [
      {
        type: "observe",
        id: "observe",
        scenario_id: "tr_same_track",
        text_key: "lessons.tr_same_track.steps.observe.text",
        sim: "running",
      },
      {
        type: "classify",
        id: "classify",
        question_key: "lessons.classify.question",
        options: ["same_track", "reciprocal_track", "crossing_track", "neither"],
        explanation_key: "lessons.tr_same_track.steps.classify.explanation",
      },
      {
        type: "complete",
        id: "complete",
        title_key: "lessons.tr_same_track.complete.title",
        text_key: "lessons.tr_same_track.complete.text",
      },
    ],
  },
};

const RUN = {
  id: "run-1",
  scenario_id: "scenario-1",
  name: "Lesson Run",
  status: "running",
  sim_rate: 1,
  created_at: "2026-07-18T08:00:00Z",
  updated_at: "2026-07-18T08:00:00Z",
  started_at: "2026-07-18T08:00:00Z",
  ended_at: null,
};

const RUN_STATE = {
  run: RUN,
  runtime_status: "running",
  sim_rate: 1,
  updated_utc: "2026-07-18T08:00:01Z",
  source: "runtime_session",
  last_error: null,
  aircraft: [],
  metrics: {
    aircraft_count: 2,
    active_aircraft_count: 2,
    finished_aircraft_count: 0,
    pending_aircraft_count: 0,
  },
};

const SCENARIO = {
  id: "scenario-1",
  slug: "lesson-scenario",
  name: "Same-Track Traffic",
  description: null,
  airspace_payload: { data: { points: {}, routes: [], airspaces: [] } },
  aircraft_payload: { data: { aircraft: [] } },
  metadata_payload: {
    learn: { visible_route_ids: ["A1"], labels: {} },
    traffic_relationship: { type: "same_track", aircraft: ["NVR212", "SKL308"] },
  },
  created_at: "2026-07-18T08:00:00Z",
  updated_at: "2026-07-18T08:00:00Z",
};

function renderRunner() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <LanguageProvider>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter
          initialEntries={["/learn/traffic_relationships/tr_same_track"]}
          future={routerFuture}
        >
          <AppRoutes />
        </MemoryRouter>
      </QueryClientProvider>
    </LanguageProvider>,
  );
}

function installRunnerFetchMock() {
  installJsonFetchMock([
    { path: `${API}/api/v1/content/curriculum`, response: { body: CURRICULUM } },
    {
      path: `${API}/api/v1/content/lessons/training_alpha/tr_same_track`,
      response: { body: LESSON },
    },
    { path: `${API}/api/v1/runs/practice`, method: "POST", response: { body: RUN } },
    { path: `${API}/api/v1/runs/run-1/state`, response: { body: RUN_STATE } },
    { path: `${API}/api/v1/runs/run-1/stop`, method: "POST", response: { body: RUN } },
    { path: `${API}/api/v1/runs/run-1/pause`, method: "POST", response: { body: RUN } },
    { path: `${API}/api/v1/scenarios/scenario-1`, response: { body: SCENARIO } },
  ]);
}

describe("LessonRunnerPage", () => {
  it("drives a data-driven lesson through observe, classify, and complete", async () => {
    installRunnerFetchMock();
    renderRunner();

    // Observation step from lesson JSON + locale catalogue.
    expect(
      await screen.findByText(
        "Both aircraft are travelling along the same route in the same direction.",
      ),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    // Classification step with the four relationship options.
    expect(
      await screen.findByText("What is the traffic relationship?"),
    ).toBeInTheDocument();
    for (const option of ["Same track", "Reciprocal track", "Crossing track", "Neither"]) {
      expect(screen.getByRole("button", { name: option })).toBeInTheDocument();
    }

    // A wrong answer explains the correct classification (from scenario
    // metadata, not the lesson file) without any score.
    // Wait for the scenario metadata (source of the correct answer) before
    // answering, mirroring a learner who watches the traffic first.
    await screen.findByText("What is the traffic relationship?");
    fireEvent.click(screen.getByRole("button", { name: "Reciprocal track" }));
    expect(await screen.findByText("Not quite.")).toBeInTheDocument();
    expect(
      await screen.findByText("The correct classification is: Same track."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    // Completion step.
    expect(await screen.findByText("Same track recognised")).toBeInTheDocument();

    // Foundational lessons must never show prediction metrics.
    expect(document.body.textContent).not.toMatch(/\d+(\.\d+)?\s?NM/);
    expect(document.body.textContent?.toLowerCase()).not.toContain("minimum separation");
  });

  it("renders French lesson content when the learner switches language", async () => {
    installRunnerFetchMock();
    window.localStorage.setItem("airspacesim.language", "fr");
    renderRunner();

    expect(
      await screen.findByText(
        "Les deux aéronefs suivent la même route dans la même direction.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continuer" })).toBeInTheDocument();
    window.localStorage.removeItem("airspacesim.language");
  });
});
