const DATA_BASE_URL = new URL("../../data/", import.meta.url);
const UI_RUNTIME_URL = new URL("ui_runtime.v1.json", DATA_BASE_URL).toString();

function isAbsoluteRef(ref) {
  return /^https?:\/\//.test(ref) || ref.startsWith("/");
}

function asUrl(ref) {
  if (typeof ref !== "string" || !ref) return null;
  if (isAbsoluteRef(ref)) {
    return new URL(ref, window.location.origin).toString();
  }
  return new URL(ref, DATA_BASE_URL).toString();
}

function devServerEquivalent(url) {
  try {
    const parsed = new URL(url, window.location.href);
    const isHttp = parsed.protocol === "http:" || parsed.protocol === "https:";
    if (!isHttp) return null;
    if (parsed.hostname !== window.location.hostname) return null;
    if (parsed.port === "8080") return null;
    parsed.port = "8080";
    return parsed.toString();
  } catch (_) {
    return null;
  }
}

function prioritizeDevServer(urls) {
  const list = (Array.isArray(urls) ? urls : [])
    .filter((item) => typeof item === "string" && item.length > 0);
  if (window.location.port === "8080") {
    return [...new Set(list)];
  }
  const devCandidates = list.map(devServerEquivalent).filter(Boolean);
  return [...new Set([...devCandidates, ...list])];
}

function normalizeRuntimePayload(payload) {
  if (payload?.schema?.name === "airspacesim.ui_runtime" && payload?.schema?.version === "1.0") {
    return payload.data || {};
  }
  return payload || {};
}

async function fetchJsonFirst(candidates) {
  const orderedCandidates = prioritizeDevServer(candidates);
  let lastError = null;
  for (const url of orderedCandidates) {
    try {
      const separator = url.includes("?") ? "&" : "?";
      const response = await fetch(`${url}${separator}_ts=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) {
        lastError = new Error(`HTTP ${response.status} for ${url}`);
        continue;
      }
      return response.json();
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error("No runtime candidate URLs available.");
}

export async function loadUiRuntimeConfig() {
  if (!globalThis.__airspacesimUiRuntimePromise) {
    globalThis.__airspacesimUiRuntimePromise = (async () => {
      try {
        const payload = await fetchJsonFirst([UI_RUNTIME_URL]);
        return normalizeRuntimePayload(payload);
      } catch (_) {
        return {};
      }
    })();
  }
  return globalThis.__airspacesimUiRuntimePromise;
}

export function resolveUiCandidates(runtimeConfig, sourceKey, fallbackCandidates) {
  const source = runtimeConfig?.sources?.[sourceKey];
  if (!source) return fallbackCandidates;

  let refs = [];
  if (Array.isArray(source)) refs = source;
  else if (typeof source === "string") refs = [source];
  else if (typeof source === "object" && source !== null) {
    refs = source.candidates || source.endpoints || (source.path ? [source.path] : []);
  }

  const resolved = refs.map(asUrl).filter(Boolean);
  const candidates = resolved.length > 0 ? resolved : fallbackCandidates;
  return prioritizeDevServer(candidates);
}

export function resolveUiPollIntervalMs(runtimeConfig, fallbackMs = 1000) {
  const raw = Number(runtimeConfig?.ui?.aircraft_poll_interval_ms);
  if (Number.isFinite(raw) && raw >= 250) {
    return Math.trunc(raw);
  }
  return fallbackMs;
}

export { DATA_BASE_URL };
