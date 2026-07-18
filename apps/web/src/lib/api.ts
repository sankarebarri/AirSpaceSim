import type {
  AirspacePackageListResponse,
  PracticeRunCreateRequest,
  RunCommandCreateRequest,
  RunCommandSubmissionResponse,
  RunCreateRequest,
  RunListResponse,
  RunResponse,
  RunStateResponse,
  ScenarioResponse,
  ScenarioListResponse,
} from "../types/api";
import { getSessionId } from "./session";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const SESSION_HEADER_NAME = "X-Airspacesim-Session";
const SESSION_QUERY_PARAM = "sid";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

if (import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL) {
  // Production must never depend on localhost (brief deployment criteria).
  console.error(
    "VITE_API_BASE_URL is not set: this production build is falling back to " +
      `${DEFAULT_API_BASE_URL} and will not reach a hosted API. ` +
      "Rebuild with VITE_API_BASE_URL pointing at the deployed backend.",
  );
}

export function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export function buildWebSocketUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(normalizedPath, API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.searchParams.set(SESSION_QUERY_PARAM, getSessionId());
  return url.toString();
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall back to status text below.
  }

  return `${response.status} ${response.statusText}`;
}

async function requestJson<TResponse>(
  path: string,
  init?: RequestInit,
): Promise<TResponse> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  headers.set(SESSION_HEADER_NAME, getSessionId());
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await readErrorDetail(response));
  }

  return (await response.json()) as TResponse;
}

export function listScenarios() {
  return requestJson<ScenarioListResponse>("/api/v1/scenarios");
}

export function listAirspaces() {
  return requestJson<AirspacePackageListResponse>("/api/v1/airspaces");
}

export function getScenario(scenarioId: string) {
  return requestJson<ScenarioResponse>(`/api/v1/scenarios/${scenarioId}`);
}

export function listRuns() {
  return requestJson<RunListResponse>("/api/v1/runs");
}

export function getRun(runId: string) {
  return requestJson<RunResponse>(`/api/v1/runs/${runId}`);
}

export function getRunState(runId: string) {
  return requestJson<RunStateResponse>(`/api/v1/runs/${runId}/state`);
}

export function createRun(payload: RunCreateRequest) {
  return requestJson<RunResponse>("/api/v1/runs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createPracticeRun(payload: PracticeRunCreateRequest) {
  return requestJson<RunResponse>("/api/v1/runs/practice", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function startRun(runId: string) {
  return requestJson<RunResponse>(`/api/v1/runs/${runId}/start`, {
    method: "POST",
  });
}

export function pauseRun(runId: string) {
  return requestJson<RunResponse>(`/api/v1/runs/${runId}/pause`, {
    method: "POST",
  });
}

export function resumeRun(runId: string) {
  return requestJson<RunResponse>(`/api/v1/runs/${runId}/resume`, {
    method: "POST",
  });
}

export function stopRun(runId: string) {
  return requestJson<RunResponse>(`/api/v1/runs/${runId}/stop`, {
    method: "POST",
  });
}

export function buildRunExportUrl(runId: string): string {
  const url = new URL(buildApiUrl(`/api/v1/runs/${runId}/export.csv`));
  url.searchParams.set(SESSION_QUERY_PARAM, getSessionId());
  return url.toString();
}

export function buildRunStreamUrl(runId: string): string {
  return buildWebSocketUrl(`/api/v1/runs/${runId}/stream`);
}

export function submitRunCommand(
  runId: string,
  payload: RunCommandCreateRequest,
) {
  return requestJson<RunCommandSubmissionResponse>(
    `/api/v1/runs/${runId}/commands`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
