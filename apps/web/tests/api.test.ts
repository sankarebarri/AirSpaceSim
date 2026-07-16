import { describe, expect, it } from "vitest";

import {
  buildApiUrl,
  buildRunExportUrl,
  buildRunStreamUrl,
  createPracticeRun,
  createRun,
  getScenario,
  listAirspaces,
  listScenarios,
} from "../src/lib/api";
import { getSessionId } from "../src/lib/session";
import { installJsonFetchMock } from "./http";

describe("api client", () => {
  it("adopts a valid session id from the URL query string", () => {
    window.history.pushState(
      {},
      "",
      "/runs/run-123?sid=airspacesim-local-dev-demo",
    );

    expect(getSessionId()).toBe("airspacesim-local-dev-demo");
    expect(window.localStorage.getItem("airspacesim.session-id")).toBe(
      "airspacesim-local-dev-demo",
    );
    expect(buildRunExportUrl("run-123")).toBe(
      "http://127.0.0.1:8000/api/v1/runs/run-123/export.csv?sid=airspacesim-local-dev-demo",
    );
    expect(buildRunStreamUrl("run-123")).toBe(
      "ws://127.0.0.1:8000/api/v1/runs/run-123/stream?sid=airspacesim-local-dev-demo",
    );
  });

  it("builds REST and websocket URLs from the configured base", () => {
    const sessionId = getSessionId();
    expect(buildApiUrl("/api/v1/runs")).toBe("http://127.0.0.1:8000/api/v1/runs");
    expect(buildRunExportUrl("run-123")).toBe(
      `http://127.0.0.1:8000/api/v1/runs/run-123/export.csv?sid=${sessionId}`,
    );
    expect(buildRunStreamUrl("run-123")).toBe(
      `ws://127.0.0.1:8000/api/v1/runs/run-123/stream?sid=${sessionId}`,
    );
  });

  it("requests JSON payloads with the expected headers", async () => {
    const fetchMock = installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/scenarios",
        response: {
          body: {
            items: [],
          },
        },
      },
    ]);

    const response = await listScenarios();

    expect(response).toEqual({ items: [] });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/scenarios",
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    );

    const requestInit = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = requestInit.headers as Headers;
    expect(headers.get("Accept")).toBe("application/json");
    expect(headers.get("Content-Type")).toBeNull();
    expect(headers.get("X-Airspacesim-Session")).toBe(getSessionId());
  });

  it("surfaces API detail messages for failed writes", async () => {
    installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/runs",
        method: "POST",
        response: {
          body: {
            detail: "Scenario is missing.",
          },
          status: 404,
          statusText: "Not Found",
        },
      },
    ]);

    await expect(
      createRun({
        name: "Broken draft",
        scenario_id: "missing-scenario",
      }),
    ).rejects.toThrow("Scenario is missing.");
  });

  it("creates a live practice run from lesson/package identifiers", async () => {
    const fetchMock = installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/runs/practice",
        method: "POST",
        response: {
          body: {
            id: "run-practice-1",
            scenario_id: "scenario-practice-1",
            name: "Heading Versus Radial Practice",
            status: "running",
            sim_rate: 1,
            created_at: "2026-05-11T08:00:00Z",
            updated_at: "2026-05-11T08:00:00Z",
            started_at: "2026-05-11T08:00:00Z",
            ended_at: null,
          },
        },
      },
    ]);

    const response = await createPracticeRun({
      airspace_id: "training_alpha",
      lesson_id: "enroute_heading_vs_radial_intro",
      name: "Heading Versus Radial Practice",
    });

    expect(response.status).toBe("running");
    expect(response.id).toBe("run-practice-1");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/runs/practice",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          airspace_id: "training_alpha",
          lesson_id: "enroute_heading_vs_radial_intro",
          name: "Heading Versus Radial Practice",
        }),
      }),
    );
  });

  it("fetches a scenario by id", async () => {
    installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/scenarios/scenario-1",
        response: {
          body: {
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
        },
      },
    ]);

    const response = await getScenario("scenario-1");

    expect(response.name).toBe("Core Flow");
    expect(response.id).toBe("scenario-1");
  });

  it("fetches airspace package summaries", async () => {
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

    const response = await listAirspaces();

    expect(response.items).toHaveLength(1);
    expect(response.items[0]?.id).toBe("training_alpha");
    expect(response.items[0]?.scenarios[0]?.path).toBe(
      "scenarios/beginner_mix.v1.json",
    );
  });
});
