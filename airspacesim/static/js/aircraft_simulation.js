// static/js/aircraft_simulation.js
import { map } from "./map_renderer.js";
import { DATA_BASE_URL, loadUiRuntimeConfig, resolveUiCandidates, resolveUiPollIntervalMs } from "./ui_runtime.js";

const DEFAULT_AIRCRAFT_CONFIG_CANDIDATES = [
  new URL("aircraft_state.v1.json", DATA_BASE_URL).toString(),
  new URL("aircraft_data.json", DATA_BASE_URL).toString(),
];

const markers = {};
let pollHandle = null;
let lastFeedIssue = "";
let runtimeConfigCache = {};
let controlsReady = false;
let pendingEvents = [];
let sinkMode = false;

function getPollIntervalMs() {
  const candidate = Number(globalThis.__airspacesimAircraftPollIntervalMs);
  return Number.isFinite(candidate) && candidate >= 250 ? Math.trunc(candidate) : 1000;
}

function updateAircraftStatus(message, level = "") {
  const node = document.getElementById("aircraft-status");
  if (!node) return;
  node.textContent = message;
  node.className = `status-line${level ? ` ${level}` : ""}`;
}

function updateControlsStatus(message, level = "") {
  const node = document.getElementById("controls-status");
  if (!node) return;
  node.textContent = message;
  node.className = `status-line${level ? ` ${level}` : ""}`;
}

function updateAircraftTable(aircraftData) {
  const tbody = document.getElementById("aircraft-table-body");
  const countNode = document.getElementById("aircraft-count");
  const syncNode = document.getElementById("aircraft-sync");

  if (countNode) countNode.textContent = String(aircraftData.length);
  if (syncNode) syncNode.textContent = new Date().toLocaleTimeString();
  if (!tbody) return;

  tbody.innerHTML = "";
  if (aircraftData.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="4">No aircraft currently tracked.</td>';
    tbody.appendChild(row);
    return;
  }

  aircraftData.forEach((aircraft) => {
    const row = document.createElement("tr");
    const position = Array.isArray(aircraft.position)
      ? `${aircraft.position[0].toFixed(4)}, ${aircraft.position[1].toFixed(4)}`
      : "-";
    row.innerHTML = `
      <td>${aircraft.id ?? "-"}</td>
      <td>${aircraft.callsign ?? "-"}</td>
      <td>${aircraft.speed ?? "-"}</td>
      <td>${position}</td>
    `;
    tbody.appendChild(row);
  });
}

async function fetchFirstAvailableJson(candidates) {
  for (const url of candidates) {
    try {
      const separator = url.includes("?") ? "&" : "?";
      const response = await fetch(`${url}${separator}_ts=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) continue;
      return await response.json();
    } catch (_) {
      // Try next candidate.
    }
  }
  return null;
}

function isoNow() {
  return new Date().toISOString();
}

function eventEnvelope(events) {
  return {
    schema: {
      name: "airspacesim.inbox_events",
      version: "1.0",
    },
    metadata: {
      source: "airspacesim.ui.operator_controls",
      generated_utc: isoNow(),
    },
    data: { events },
  };
}

function refreshEventPayloadView() {
  const textarea = document.getElementById("events-payload");
  if (!textarea) return;
  textarea.value = JSON.stringify(eventEnvelope(pendingEvents), null, 2);
}

function deriveWorkspacePrefix() {
  const path = window.location?.pathname || "";
  const marker = "/templates/";
  const markerIndex = path.indexOf(marker);
  if (markerIndex <= 0) return "";
  return path.slice(0, markerIndex);
}

function defaultEventSinkUrl() {
  const prefix = deriveWorkspacePrefix();
  return `${prefix}/api/events`;
}

function normalizeSinkUrl(candidate) {
  if (typeof candidate !== "string" || !candidate) return null;
  try {
    if (/^https?:\/\//.test(candidate)) {
      return new URL(candidate).toString();
    }
    if (candidate.startsWith("/")) {
      return new URL(candidate, window.location.origin).toString();
    }
    return new URL(candidate, window.location.href).toString();
  } catch (_) {
    return null;
  }
}

function resolveEventSinkCandidates(runtimeConfig) {
  const sink = runtimeConfig?.sinks?.aircraft_events;
  const prefix = deriveWorkspacePrefix();
  const host = window.location.hostname || "127.0.0.1";
  const configuredCandidates = [];
  if (typeof sink === "string") {
    configuredCandidates.push(sink);
  } else if (typeof sink === "object" && sink !== null && typeof sink.url === "string") {
    configuredCandidates.push(sink.url);
  }

  const fallbackCandidates = [
    defaultEventSinkUrl(),
    "/api/events",
    `http://${host}:8080${prefix}/api/events`,
    `http://${host}:8080/api/events`,
    `http://${host}:8080/airspacesim-playground/api/events`,
  ];

  const resolved = [...configuredCandidates, ...fallbackCandidates]
    .map(normalizeSinkUrl)
    .filter(Boolean);

  return [...new Set(resolved)];
}

function getEventSinkUrl(runtimeConfig) {
  const candidates = resolveEventSinkCandidates(runtimeConfig);
  return candidates[0] || "";
}

async function sendEventToSink(event) {
  const sinkCandidates = resolveEventSinkCandidates(runtimeConfigCache);
  if (sinkCandidates.length === 0) return false;

  let lastError = "unknown error";
  for (const sinkUrl of sinkCandidates) {
    try {
      const response = await fetch(sinkUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(eventEnvelope([event])),
      });
      if (!response.ok) {
        lastError = `HTTP ${response.status}`;
        continue;
      }
      const responseBody = await response.json().catch(() => ({}));
      const targetPath =
        typeof responseBody?.target === "string" ? responseBody.target : sinkUrl;
      const acceptedCount = Number(responseBody?.accepted);
      const acceptedSuffix = Number.isFinite(acceptedCount)
        ? ` accepted=${acceptedCount}`
        : "";
      console.info(
        `[EVENT SINK] sent event_id=${event.event_id} type=${event.type} target=${targetPath}${acceptedSuffix}`
      );
      updateControlsStatus(`Event ${event.event_id} sent -> ${targetPath}.`, "ok");
      return true;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
  }

  console.warn("Failed to POST event to all sink candidates:", {
    sinkCandidates,
    lastError,
  });
  const primarySink = sinkCandidates[0];
  updateControlsStatus(
    `Event sink unavailable (${primarySink}). Last error: ${lastError}. Event queued in payload box.`,
    "warn"
  );
  return false;
}

function buildEvent(type, payload) {
  return {
    event_id: `evt-${type.toLowerCase()}-${Date.now()}`,
    type,
    created_utc: isoNow(),
    payload,
  };
}

async function queueOrSendEvent(event) {
  const sent = await sendEventToSink(event);
  if (!sent) {
    pendingEvents.push(event);
    refreshEventPayloadView();
    updateControlsStatus("Event queued locally. Start dev_server.py or paste payload into inbox file.", "warn");
  }
}

function applyControlButtonLabels() {
  const addBtn = document.querySelector("#form-add-aircraft button[type='submit']");
  const speedBtn = document.querySelector("#form-set-speed button[type='submit']");
  const simRateBtn = document.querySelector("#form-set-sim-rate button[type='submit']");

  if (sinkMode) {
    if (addBtn) addBtn.textContent = "Send ADD_AIRCRAFT";
    if (speedBtn) speedBtn.textContent = "Send SET_SPEED";
    if (simRateBtn) simRateBtn.textContent = "Send SET_SIMULATION_SPEED";
    return;
  }

  if (addBtn) addBtn.textContent = "Queue ADD_AIRCRAFT";
  if (speedBtn) speedBtn.textContent = "Queue SET_SPEED";
  if (simRateBtn) simRateBtn.textContent = "Queue SET_SIMULATION_SPEED";
}

function wireOperatorControls() {
  if (controlsReady) return;
  controlsReady = true;

  const addForm = document.getElementById("form-add-aircraft");
  const speedForm = document.getElementById("form-set-speed");
  const simRateForm = document.getElementById("form-set-sim-rate");
  const copyBtn = document.getElementById("btn-copy-events");
  const clearBtn = document.getElementById("btn-clear-events");

  if (addForm) {
    addForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const aircraftId = document.getElementById("add-aircraft-id")?.value?.trim();
      const callsign = document.getElementById("add-callsign")?.value?.trim();
      const routeId = document.getElementById("add-route-id")?.value?.trim();
      const speedKt = Number(document.getElementById("add-speed-kt")?.value);
      if (!aircraftId || !routeId || !Number.isFinite(speedKt) || speedKt <= 0) {
        updateControlsStatus("Invalid ADD_AIRCRAFT input.", "err");
        return;
      }
      await queueOrSendEvent(
        buildEvent("ADD_AIRCRAFT", {
          aircraft_id: aircraftId,
          route_id: routeId,
          callsign: callsign || aircraftId,
          speed_kt: speedKt,
        })
      );
    });
  }

  if (speedForm) {
    speedForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const aircraftId = document.getElementById("set-speed-aircraft-id")?.value?.trim();
      const speedKt = Number(document.getElementById("set-speed-kt")?.value);
      if (!aircraftId || !Number.isFinite(speedKt) || speedKt <= 0) {
        updateControlsStatus("Invalid SET_SPEED input.", "err");
        return;
      }
      await queueOrSendEvent(
        buildEvent("SET_SPEED", {
          aircraft_id: aircraftId,
          speed_kt: speedKt,
        })
      );
    });
  }

  if (simRateForm) {
    simRateForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const simRate = Number(document.getElementById("set-sim-rate")?.value);
      if (!Number.isFinite(simRate) || simRate <= 0) {
        updateControlsStatus("Invalid SET_SIMULATION_SPEED input.", "err");
        return;
      }
      await queueOrSendEvent(
        buildEvent("SET_SIMULATION_SPEED", {
          sim_rate: simRate,
        })
      );
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      const payload = document.getElementById("events-payload")?.value || "";
      if (!payload) return;
      try {
        await navigator.clipboard.writeText(payload);
        updateControlsStatus("Event payload copied.", "ok");
      } catch (_) {
        updateControlsStatus("Clipboard copy failed. Select and copy manually.", "warn");
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      pendingEvents = [];
      refreshEventPayloadView();
      updateControlsStatus("Pending events cleared.", "ok");
    });
  }

  sinkMode = Boolean(getEventSinkUrl(runtimeConfigCache));
  applyControlButtonLabels();
  const sinkCandidates = resolveEventSinkCandidates(runtimeConfigCache);
  if (sinkCandidates.length > 0) {
    console.info("[EVENT SINK] candidates", sinkCandidates);
    updateControlsStatus(`Command sink target: ${sinkCandidates[0]}`, "ok");
  } else {
    updateControlsStatus("No command sink configured. Queue then copy payload into data/inbox_events.v1.json.", "warn");
  }

  refreshEventPayloadView();
}

function normalizeAircraftData(payload) {
  if (Array.isArray(payload?.aircraft_data)) {
    return payload.aircraft_data;
  }
  if (Array.isArray(payload?.data?.aircraft_data)) {
    return payload.data.aircraft_data;
  }

  const canonical = payload?.data?.aircraft;
  if (!Array.isArray(canonical)) {
    return [];
  }

  return canonical.map((aircraft) => ({
    id: aircraft.id,
    callsign: aircraft.callsign,
    speed: aircraft.speed_kt,
    position: aircraft.position_dd,
  }));
}

function syncMarkers(aircraftData) {
  if (!map || !map.aircraftLayer) return;

  const seen = new Set();
  aircraftData.forEach((aircraft) => {
    if (!Array.isArray(aircraft.position)) return;

    const markerId = aircraft.id;
    seen.add(markerId);

    if (markers[markerId]) {
      markers[markerId].setLatLng(aircraft.position);
      markers[markerId].setTooltipContent(`${aircraft.callsign || markerId} | ${aircraft.speed || "?"} kt`);
      return;
    }

    const marker = L.circleMarker(aircraft.position, {
      radius: 7,
      color: "#ff0000",
      weight: 2,
      fillColor: "#ff0000",
      fillOpacity: 1.0,
    }).bindTooltip(`${aircraft.callsign || markerId} | ${aircraft.speed || "?"} kt`, {
      permanent: true,
      direction: "bottom",
    });

    marker.addTo(map.aircraftLayer);
    markers[markerId] = marker;
  });

  Object.keys(markers).forEach((markerId) => {
    if (!seen.has(markerId)) {
      map.aircraftLayer.removeLayer(markers[markerId]);
      delete markers[markerId];
    }
  });
}

async function fetchAircraftData() {
  if (!map || !map.aircraftLayer) return;

  try {
    const data = await fetchFirstAvailableJson(globalThis.__airspacesimAircraftDataCandidates || DEFAULT_AIRCRAFT_CONFIG_CANDIDATES);
    if (!data) {
      if (lastFeedIssue !== "missing") {
        console.warn("Aircraft feed file not found in configured data path.");
        lastFeedIssue = "missing";
      }
      syncMarkers([]);
      updateAircraftTable([]);
      updateAircraftStatus("Aircraft feed unavailable (missing file).", "warn");
      return;
    }
    const aircraftData = normalizeAircraftData(data);

    syncMarkers(aircraftData);
    updateAircraftTable(aircraftData);
    updateAircraftStatus("Aircraft feed healthy.", "ok");
    lastFeedIssue = "";
  } catch (error) {
    if (lastFeedIssue !== "error") {
      console.error("Error fetching aircraft data:", error);
      lastFeedIssue = "error";
    }
    syncMarkers([]);
    updateAircraftTable([]);
    updateAircraftStatus("Aircraft feed unavailable (read error).", "warn");
  }
}

async function startPolling() {
  if (pollHandle) return;
  runtimeConfigCache = await loadUiRuntimeConfig();
  globalThis.__airspacesimAircraftDataCandidates = resolveUiCandidates(
    runtimeConfigCache,
    "aircraft_state",
    DEFAULT_AIRCRAFT_CONFIG_CANDIDATES
  );
  const pollIntervalMs = resolveUiPollIntervalMs(runtimeConfigCache, getPollIntervalMs());
  wireOperatorControls();
  fetchAircraftData();
  pollHandle = setInterval(fetchAircraftData, pollIntervalMs);
}

if (map && map.aircraftLayer) {
  startPolling();
} else {
  document.addEventListener("airspacesim:map-ready", startPolling, { once: true });
}
