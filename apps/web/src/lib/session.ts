const SESSION_STORAGE_KEY = "airspacesim.session-id";
const SESSION_QUERY_PARAM = "sid";
const SESSION_ID_PATTERN = /^[A-Za-z0-9-]{8,64}$/;

function getSessionIdFromUrl(): string | null {
  const candidate = new URLSearchParams(window.location.search).get(
    SESSION_QUERY_PARAM,
  );
  if (!candidate || !SESSION_ID_PATTERN.test(candidate)) {
    return null;
  }
  window.localStorage.setItem(SESSION_STORAGE_KEY, candidate);
  return candidate;
}

export function getSessionId(): string {
  const urlSessionId = getSessionIdFromUrl();
  if (urlSessionId) {
    return urlSessionId;
  }

  const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }
  const created = crypto.randomUUID();
  window.localStorage.setItem(SESSION_STORAGE_KEY, created);
  return created;
}
