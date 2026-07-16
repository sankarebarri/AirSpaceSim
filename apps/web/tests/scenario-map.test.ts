import { describe, expect, it } from "vitest";

import { parseScenarioMapOverlay } from "../src/lib/scenario-map";
import type { ScenarioResponse } from "../src/types/api";

function buildScenario(
  airspacePayload: Record<string, unknown>,
): ScenarioResponse {
  return {
    id: "scenario-1",
    slug: "core-flow",
    name: "Core Flow",
    description: "Scenario overlay test",
    airspace_payload: airspacePayload,
    aircraft_payload: { data: { aircraft: [] } },
    metadata_payload: {},
    created_at: "2026-05-11T08:00:00Z",
    updated_at: "2026-05-11T09:00:00Z",
  };
}

describe("parseScenarioMapOverlay", () => {
  it("parses points, routes, and airspaces from the normalized contract", () => {
    const overlay = parseScenarioMapOverlay(
      buildScenario({
        data: {
          points: {
            P1: { type: "fix", name: "Point 1", coord: { dd: [10, 1] } },
            P2: { type: "fix", name: "Point 2", coord: { dd: [11, 1.5] } },
          },
          routes: [{ id: "R1", name: "North Flow", waypoint_ids: ["P1", "P2"] }],
          airspaces: [{ id: "A1", center_point_id: "P1", radius_nm: 30 }],
        },
      }),
    );

    expect(overlay.points).toEqual([
      { id: "P1", name: "Point 1", type: "fix", position: [10, 1] },
      { id: "P2", name: "Point 2", type: "fix", position: [11, 1.5] },
    ]);
    expect(overlay.routes).toEqual([
      {
        id: "R1",
        name: "North Flow",
        waypointIds: ["P1", "P2"],
        path: [
          [10, 1],
          [11, 1.5],
        ],
      },
    ]);
    expect(overlay.airspaces).toEqual([
      {
        type: "circle",
        id: "A1",
        name: "A1",
        centerPointId: "P1",
        center: [10, 1],
        radiusNm: 30,
        radiusMeters: 55560,
      },
    ]);
  });

  it("skips invalid route and airspace references", () => {
    const overlay = parseScenarioMapOverlay(
      buildScenario({
        data: {
          points: {
            P1: { type: "fix", name: "Point 1", coord: { dd: [10, 1] } },
          },
          routes: [{ id: "R1", waypoint_ids: ["P1", "MISSING"] }],
          airspaces: [
            { id: "A1", center_point_id: "MISSING", radius_nm: 30 },
            { id: "A2", center_point_id: "P1", radius_nm: -1 },
          ],
        },
      }),
    );

    expect(overlay.routes).toEqual([]);
    expect(overlay.airspaces).toEqual([]);
    expect(overlay.points).toHaveLength(1);
  });
});
