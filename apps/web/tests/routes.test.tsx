import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppRoutes } from "../src/app/routes";
import { installJsonFetchMock } from "./http";

const routerFuture = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

function renderRoutes(initialEntry: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]} future={routerFuture}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AppRoutes", () => {
  it("renders the scenario library route", async () => {
    installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/scenarios",
        response: {
          body: {
            items: [
              {
                id: "scenario-1",
                slug: "core-flow",
                name: "Core Flow",
                description: "Baseline route inventory",
                airspace_payload: {
                  data: {
                    routes: [{ id: "UA612" }],
                    points: [{ id: "PT1" }, { id: "PT2" }],
                  },
                },
                aircraft_payload: {
                  data: {
                    aircraft: [{ id: "AC100" }],
                  },
                },
                metadata_payload: {},
                created_at: "2026-05-11T08:00:00Z",
                updated_at: "2026-05-11T09:00:00Z",
              },
            ],
          },
        },
      },
    ]);

    renderRoutes("/scenarios");

    expect(await screen.findByRole("heading", { name: "Scenario Library" }))
      .toBeInTheDocument();
    expect(await screen.findByText("Core Flow")).toBeInTheDocument();
    expect(await screen.findByText("Baseline route inventory")).toBeInTheDocument();
  });

  it("renders the run deck route", async () => {
    installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/scenarios",
        response: {
          body: {
            items: [
              {
                id: "scenario-1",
                slug: "core-flow",
                name: "Core Flow",
                description: null,
                airspace_payload: { data: {} },
                aircraft_payload: { data: {} },
                metadata_payload: {},
                created_at: "2026-05-11T08:00:00Z",
                updated_at: "2026-05-11T09:00:00Z",
              },
            ],
          },
        },
      },
      {
        path: "http://127.0.0.1:8000/api/v1/runs",
        response: {
          body: {
            items: [
              {
                id: "run-1",
                scenario_id: "scenario-1",
                name: "Morning flow calibration",
                status: "draft",
                sim_rate: 1,
                created_at: "2026-05-11T10:00:00Z",
                updated_at: "2026-05-11T10:00:00Z",
                started_at: null,
                ended_at: null,
              },
            ],
          },
        },
      },
    ]);

    renderRoutes("/runs");

    expect(await screen.findByRole("heading", { name: "Simulation Deck" }))
      .toBeInTheDocument();
    expect(await screen.findByText("Morning flow calibration")).toBeInTheDocument();
    expect(screen.getByText("Create Draft Run")).toBeInTheDocument();
  });

  it("renders airspace packages from the API", async () => {
    installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/airspaces",
        response: {
          body: {
            items: [
              {
                id: "training_alpha",
                name: "Training Alpha",
                description: "Fictional beginner airspace",
                package_type: "fictional",
                service_types: ["enroute"],
                difficulty: "beginner",
                training_modes: ["solo_guided"],
                airspace_file: "airspaces/training_alpha/airspace.v1.json",
                default_scenario: "beginner_mix",
                map: {},
                scenarios: [
                  {
                    id: "beginner_mix",
                    title: "Beginner Mixed Traffic",
                    path: "scenarios/beginner_mix.v1.json",
                    description: null,
                    service_type: "enroute",
                    training_mode: "solo_guided",
                    difficulty: "beginner",
                  },
                ],
                lessons: [],
              },
            ],
          },
        },
      },
    ]);

    renderRoutes("/airspaces");

    expect(
      await screen.findByRole("heading", {
        name: "Select the training environment before loading traffic.",
      }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Training Alpha")).toBeInTheDocument();
    expect(await screen.findByText("Fictional")).toBeInTheDocument();
    expect(
      await screen.findByText("Includes a ready-to-run training scenario"),
    ).toBeInTheDocument();
  });

  it("redirects unknown routes back to the overview", async () => {
    renderRoutes("/does-not-exist");

    expect(await screen.findByText("Sign in")).toBeInTheDocument();
  });
});
