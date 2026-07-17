import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RunDetailPage } from "../src/pages/RunDetailPage";
import { installJsonFetchMock } from "./http";

const routerFuture = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

vi.mock("../src/components/TrafficMap", () => ({
  TrafficMap: ({
    aircraft,
    overlay,
    selectedAircraftId,
    onSelect,
  }: {
    aircraft: Array<{ id: string; callsign: string | null }>;
    overlay: { routes: unknown[]; airspaces: unknown[] };
    selectedAircraftId: string | null;
    onSelect: (aircraftId: string) => void;
  }) => (
    <div data-testid="traffic-map">
      <div>
        {`routes:${overlay.routes.length} airspaces:${overlay.airspaces.length} selected:${selectedAircraftId ?? "none"}`}
      </div>
      {aircraft.map((item) => (
        <button key={item.id} type="button" onClick={() => onSelect(item.id)}>
          {item.callsign ?? item.id}
        </button>
      ))}
    </div>
  ),
}));

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static instances: MockWebSocket[] = [];

  readonly url: string;
  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close(code = 1000) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code } as CloseEvent);
  }

  emitOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event("open"));
  }

  emitMessage(payload: unknown) {
    this.onmessage?.({
      data: JSON.stringify(payload),
    } as MessageEvent<string>);
  }

  emitError() {
    this.onerror?.(new Event("error"));
  }

  emitClose(code = 1000) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code } as CloseEvent);
  }

  static latest(): MockWebSocket {
    const latest = MockWebSocket.instances.at(-1);
    if (!latest) {
      throw new Error("Expected a websocket instance to exist.");
    }
    return latest;
  }

  static reset() {
    MockWebSocket.instances = [];
  }
}

function buildRun() {
  return {
    id: "run-1",
    scenario_id: "scenario-1",
    name: "Morning flow calibration",
    status: "running",
    sim_rate: 1,
    created_at: "2026-05-12T10:00:00Z",
    updated_at: "2026-05-12T10:05:00Z",
    started_at: "2026-05-12T10:01:00Z",
    ended_at: null,
  };
}

function buildAircraftState() {
  return [
    {
      id: "AC100",
      callsign: "OPS100",
      aircraft_type: "B737",
      route_id: "UL602",
      position_dd: [16.25, -0.03] as [number, number],
      speed_kt: 420,
      flight_level: 350,
      target_flight_level: 350,
      altitude_ft: 35000,
      vertical_rate_fpm: 0,
      heading_deg: 45,
      assigned_heading_deg: null,
      assigned_radial_deg: null,
      radial_deviation_deg: null,
      radial_cross_track_nm: null,
      lateral_mode: "route",
      direct_to_fix_id: null,
      hold_fix_id: null,
      traffic_flow: "outbound",
      status: "active",
      updated_utc: "2026-05-12T10:05:00Z",
    },
    {
      id: "AC200",
      callsign: "OPS200",
      aircraft_type: "A320",
      route_id: "UB800",
      position_dd: [16.6, 0.18] as [number, number],
      speed_kt: 400,
      flight_level: 310,
      target_flight_level: 300,
      altitude_ft: 31000,
      vertical_rate_fpm: -200,
      heading_deg: 225,
      assigned_heading_deg: 180,
      assigned_radial_deg: null,
      radial_deviation_deg: null,
      radial_cross_track_nm: null,
      lateral_mode: "heading",
      direct_to_fix_id: null,
      hold_fix_id: null,
      traffic_flow: "inbound",
      status: "holding",
      updated_utc: "2026-05-12T10:05:00Z",
    },
  ];
}

function buildRunState() {
  const run = buildRun();
  const aircraft = buildAircraftState();

  return {
    run,
    runtime_status: "running",
    sim_rate: 1,
    updated_utc: "2026-05-12T10:05:00Z",
    source: "runtime_session",
    last_error: null,
    aircraft,
    metrics: {
      aircraft_count: aircraft.length,
      active_aircraft_count: 1,
      finished_aircraft_count: 0,
    },
  };
}

function buildScenario() {
  return {
    id: "scenario-1",
    slug: "core-flow",
    name: "Core Flow",
    description: "Baseline traffic lane",
    airspace_payload: {
      data: {
        points: {
          P1: { type: "fix", name: "Point 1", coord: { dd: [16.25, -0.03] } },
          P2: { type: "fix", name: "Point 2", coord: { dd: [16.8, 0.22] } },
        },
        routes: [
          { id: "UL602", name: "North Gate", waypoint_ids: ["P1", "P2"] },
        ],
        airspaces: [{ id: "A1", center_point_id: "P1", radius_nm: 40 }],
      },
    },
    aircraft_payload: { data: { aircraft: [] } },
    metadata_payload: {},
    created_at: "2026-05-12T09:00:00Z",
    updated_at: "2026-05-12T09:10:00Z",
  };
}

function renderRunWorkspace() {
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
      <MemoryRouter initialEntries={["/runs/run-1"]} future={routerFuture}>
        <Routes>
          <Route path="/runs/:runId" element={<RunDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  MockWebSocket.reset();
  vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);
});

describe("RunDetailPage", () => {
  it("stops polling and streaming when the route points at a missing run", async () => {
    const fetchMock = installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/runs/run-1",
        response: {
          body: {
            detail: "Run not found: run-1",
          },
          status: 404,
          statusText: "Not Found",
        },
      },
    ]);

    renderRunWorkspace();

    expect(await screen.findByText("Run not found: run-1")).toBeInTheDocument();
    expect(
      await screen.findByText(/Open the latest seeded run URL/),
    ).toBeInTheDocument();
    expect(MockWebSocket.instances).toHaveLength(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("renders the visible traffic list", async () => {
    installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/runs/run-1",
        response: { body: buildRun() },
      },
      {
        path: "http://127.0.0.1:8000/api/v1/runs/run-1/state",
        response: { body: buildRunState() },
      },
      {
        path: "http://127.0.0.1:8000/api/v1/scenarios/scenario-1",
        response: { body: buildScenario() },
      },
    ]);

    renderRunWorkspace();

    expect(await screen.findByRole("heading", { name: "Morning flow calibration" }))
      .toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Tracks" })).toBeInTheDocument();
    expect(await screen.findByText("2/2")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "OPS100" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /OPS200 UB800/ }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Search tracks")).not.toBeInTheDocument();
  });

  it("submits a guided SET_SPEED command and shows the last result", async () => {
    const fetchMock = installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/runs/run-1",
        response: { body: buildRun() },
      },
      {
        path: "http://127.0.0.1:8000/api/v1/runs/run-1/state",
        response: { body: buildRunState() },
      },
      {
        path: "http://127.0.0.1:8000/api/v1/scenarios/scenario-1",
        response: { body: buildScenario() },
      },
      {
        path: "http://127.0.0.1:8000/api/v1/runs/run-1/commands",
        method: "POST",
        response: {
          body: {
            command: {
              id: "cmd-1",
              run_id: "run-1",
              command_type: "SET_SPEED",
              status: "applied",
              payload: {
                aircraft_id: "AC100",
                speed_kt: 480,
              },
              created_at: "2026-05-12T10:06:00Z",
              applied_at: "2026-05-12T10:06:01Z",
            },
            result: {
              state: "applied",
              applied: ["cmd-1"],
              skipped: [],
              rejected: [],
            },
          },
        },
      },
    ]);

    renderRunWorkspace();

    expect(await screen.findByRole("heading", { name: "Morning flow calibration" }))
      .toBeInTheDocument();

    fireEvent.click(await screen.findByRole("button", { name: "Clearances" }));

    const speedInputs = await screen.findAllByLabelText("Assigned speed");
    fireEvent.change(speedInputs[0], { target: { value: "480" } });
    fireEvent.click(screen.getByRole("button", { name: "Assign Speed" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Command History" })).toBeInTheDocument();
      expect(screen.getByText("Speed assigned")).toBeInTheDocument();
      expect(screen.getAllByText("Applied").length).toBeGreaterThan(0);
    });

    const commandCall = fetchMock.mock.calls.find(
      ([input, init]) =>
        input === "http://127.0.0.1:8000/api/v1/runs/run-1/commands" &&
        (init as RequestInit | undefined)?.method === "POST",
    );

    expect(commandCall).toBeDefined();
    const requestInit = commandCall?.[1] as RequestInit;
    expect(JSON.parse(String(requestInit.body))).toEqual({
      command_type: "SET_SPEED",
      payload: {
        aircraft_id: "AC100",
        speed_kt: 480,
      },
    });
  });

  it("applies websocket state and command-result events to the workspace", async () => {
    installJsonFetchMock([
      {
        path: "http://127.0.0.1:8000/api/v1/runs/run-1",
        response: { body: buildRun() },
      },
      {
        path: "http://127.0.0.1:8000/api/v1/runs/run-1/state",
        response: { body: buildRunState() },
      },
      {
        path: "http://127.0.0.1:8000/api/v1/scenarios/scenario-1",
        response: { body: buildScenario() },
      },
    ]);

    renderRunWorkspace();

    expect(await screen.findByRole("heading", { name: "Morning flow calibration" }))
      .toBeInTheDocument();

    act(() => {
      MockWebSocket.latest().emitOpen();
    });

    await waitFor(() => {
      expect(screen.getAllByText("Open").length).toBeGreaterThan(0);
    });

    act(() => {
      MockWebSocket.latest().emitMessage({
        type: "run_state.updated",
        run_id: "run-1",
        emitted_at: "2026-05-12T10:07:00Z",
        data: {
          runtime_status: "running",
          sim_rate: 1.5,
          updated_utc: "2026-05-12T10:07:00Z",
          last_error: null,
          aircraft: [
            ...buildAircraftState(),
            {
              id: "AC300",
              callsign: "OPS300",
              aircraft_type: "E190",
              route_id: "UL602",
              position_dd: [17.1, 0.44],
              speed_kt: 390,
              flight_level: 290,
              target_flight_level: 300,
              altitude_ft: 29000,
              vertical_rate_fpm: 500,
              heading_deg: 90,
              assigned_heading_deg: null,
              assigned_radial_deg: null,
              radial_deviation_deg: null,
              radial_cross_track_nm: null,
              lateral_mode: "route",
              direct_to_fix_id: null,
              hold_fix_id: null,
              traffic_flow: "outbound",
              status: "active",
              updated_utc: "2026-05-12T10:07:00Z",
            },
          ],
          metrics: {
            aircraft_count: 3,
            active_aircraft_count: 2,
            finished_aircraft_count: 0,
          },
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByText("3/3")).toBeInTheDocument();
      expect(screen.getAllByText("OPS300").length).toBeGreaterThan(0);
      expect(screen.getByText("1.5x")).toBeInTheDocument();
    });

    act(() => {
      MockWebSocket.latest().emitMessage({
        type: "run_command.result",
        run_id: "run-1",
        emitted_at: "2026-05-12T10:07:05Z",
        data: {
          command: {
            id: "cmd-2",
            run_id: "run-1",
            command_type: "ADD_AIRCRAFT",
            status: "skipped",
            payload: {
              aircraft_id: "AC300",
            },
            created_at: "2026-05-12T10:07:05Z",
            applied_at: null,
          },
          result: {
            state: "skipped",
            applied: [],
            skipped: [
              {
                command_id: "cmd-2",
                reason: "Duplicate aircraft id",
              },
            ],
            rejected: [],
          },
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Command History" })).toBeInTheDocument();
      expect(screen.getByText("Track added")).toBeInTheDocument();
      expect(screen.getAllByText("Skipped").length).toBeGreaterThan(0);
      expect(screen.getByText("Duplicate aircraft id")).toBeInTheDocument();
    });
  });
});
