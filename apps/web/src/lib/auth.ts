// Authentication client: cookie-based server-side sessions.
// All requests send credentials so the HttpOnly session cookie flows.

import { API_BASE_URL } from "./api";
import { getSessionId } from "./session";

export interface UserResponse {
  id: string;
  email: string;
  display_name: string | null;
  preferred_language: string;
  created_at: string;
}

async function authRequest<TResponse>(
  path: string,
  init?: RequestInit,
): Promise<TResponse> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  // Guest session id lets the backend adopt anonymous runs on sign-in.
  headers.set("X-Airspacesim-Session", getSessionId());
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (response.status === 204) {
    return undefined as TResponse;
  }
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        detail = payload.detail;
      }
    } catch {
      // keep status text
    }
    throw new Error(detail);
  }
  return (await response.json()) as TResponse;
}

export function register(payload: {
  email: string;
  password: string;
  display_name?: string;
}): Promise<UserResponse> {
  return authRequest<UserResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function login(payload: {
  email: string;
  password: string;
}): Promise<UserResponse> {
  return authRequest<UserResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout(): Promise<void> {
  return authRequest<void>("/api/v1/auth/logout", { method: "POST" });
}

export async function fetchCurrentUser(): Promise<UserResponse | null> {
  try {
    return await authRequest<UserResponse>("/api/v1/auth/me");
  } catch {
    return null;
  }
}

export function updateProfile(payload: {
  display_name?: string | null;
  preferred_language?: string;
}): Promise<UserResponse> {
  return authRequest<UserResponse>("/api/v1/auth/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// ---- learning progress persistence (signed-in users only) ----

export interface ProgressEntry {
  concept_id: string;
  stage_key: string;
  status: string;
  updated_at: string;
}

export async function fetchServerProgress(): Promise<ProgressEntry[]> {
  try {
    const response = await authRequest<{ items: ProgressEntry[] }>(
      "/api/v1/progress",
    );
    return response.items;
  } catch {
    return []; // guests simply have no server progress
  }
}

export function syncLessonComplete(
  conceptId: string,
  lessonId: string,
): Promise<void> {
  return authRequest<unknown>("/api/v1/progress", {
    method: "PUT",
    body: JSON.stringify({ concept_id: conceptId, stage_key: lessonId }),
  })
    .then(() => undefined)
    .catch(() => undefined); // guest or offline: local storage still has it
}
