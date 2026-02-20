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
  const runtimeConfig = await loadUiRuntimeConfig();
  globalThis.__airspacesimAircraftDataCandidates = resolveUiCandidates(
    runtimeConfig,
    "aircraft_state",
    DEFAULT_AIRCRAFT_CONFIG_CANDIDATES
  );
  const pollIntervalMs = resolveUiPollIntervalMs(runtimeConfig, getPollIntervalMs());
  fetchAircraftData();
  pollHandle = setInterval(fetchAircraftData, pollIntervalMs);
}

if (map && map.aircraftLayer) {
  startPolling();
} else {
  document.addEventListener("airspacesim:map-ready", startPolling, { once: true });
}
