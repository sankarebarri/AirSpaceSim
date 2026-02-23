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
const knownAircraftIds = new Set();
const latestAircraftById = new Map();
let selectedAircraftId = "";
const TRAFFIC_FLOW_COLORS = {
  outbound: "#1f8c53",
  inbound: "#d92d20",
  transit: "#f79009",
  unknown: "#64748b",
};

function resolveFlightLevelValue(aircraft) {
  const explicitFl = Number(aircraft?.flight_level);
  if (Number.isFinite(explicitFl) && explicitFl >= 0) {
    return Math.round(explicitFl);
  }
  const altitude = Number(aircraft?.altitude_ft);
  if (Number.isFinite(altitude) && altitude >= 0) {
    return Math.round(altitude / 100);
  }
  return null;
}

function formatFlightLevel(flightLevel, altitudeFt) {
  const resolvedFl = resolveFlightLevelValue({ flight_level: flightLevel, altitude_ft: altitudeFt });
  if (!Number.isFinite(resolvedFl)) return "FL---";
  return `FL${String(resolvedFl).padStart(3, "0")}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function getTrafficFlow(aircraft) {
  return typeof aircraft?.traffic_flow === "string" ? aircraft.traffic_flow : "unknown";
}

function getTrafficFlowColor(aircraft) {
  return TRAFFIC_FLOW_COLORS[getTrafficFlow(aircraft)] || TRAFFIC_FLOW_COLORS.unknown;
}

function getTrafficFlowLabel(aircraft) {
  const flow = getTrafficFlow(aircraft);
  if (flow === "outbound") return "Outbound";
  if (flow === "inbound") return "Inbound";
  if (flow === "transit") return "Transit";
  return "Unknown";
}

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

function refreshRowSelection() {
  document
    .querySelectorAll("#aircraft-table-body tr[data-aircraft-id]")
    .forEach((row) => {
      row.classList.toggle("is-selected", row.dataset.aircraftId === selectedAircraftId);
    });
}

function applyAutofillPreservingEdits(input, suggestedValue, selectionChanged) {
  if (!input) return;
  const normalizedSuggestion = String(suggestedValue ?? "").trim();
  if (!normalizedSuggestion) return;
  const activeElement = document.activeElement;
  const isFocused = activeElement === input;
  const currentValue = String(input.value ?? "").trim();
  const previousSuggestedValue = input.dataset.autofillValue || "";
  const isUntouched = currentValue === "" || currentValue === previousSuggestedValue;
  if (!isFocused && (selectionChanged || isUntouched)) {
    input.value = normalizedSuggestion;
    input.dataset.autofillValue = normalizedSuggestion;
  }
}

function setSelectedAircraft(aircraftId) {
  const previousSelectedAircraftId = selectedAircraftId;
  const normalizedId = typeof aircraftId === "string" ? aircraftId.trim() : "";
  if (normalizedId && latestAircraftById.has(normalizedId)) {
    selectedAircraftId = normalizedId;
  } else {
    selectedAircraftId = "";
  }

  const selectedNode = document.getElementById("selected-aircraft-status");
  const speedIdInput = document.getElementById("set-speed-aircraft-id");
  const flIdInput = document.getElementById("set-fl-aircraft-id");
  const flInput = document.getElementById("set-flight-level");
  const flCurrentNode = document.getElementById("set-fl-current");
  const aircraft = selectedAircraftId ? latestAircraftById.get(selectedAircraftId) : null;
  const selectionChanged = selectedAircraftId !== previousSelectedAircraftId;

  if (aircraft) {
    const flightLevel = resolveFlightLevelValue(aircraft);
    const flightLevelText = formatFlightLevel(aircraft.flight_level, aircraft.altitude_ft);
    if (selectedNode) {
      selectedNode.textContent = `Selected: ${aircraft.callsign || aircraft.id} (${aircraft.id}) ${flightLevelText}`;
    }
    applyAutofillPreservingEdits(speedIdInput, aircraft.id, selectionChanged);
    applyAutofillPreservingEdits(flIdInput, aircraft.id, selectionChanged);
    if (flInput && Number.isFinite(flightLevel)) {
      applyAutofillPreservingEdits(flInput, String(flightLevel), selectionChanged);
    }
    if (flCurrentNode) flCurrentNode.textContent = `Current FL: ${flightLevelText}`;
  } else {
    if (selectedNode) selectedNode.textContent = "Selected: none";
    if (flCurrentNode) flCurrentNode.textContent = "Current FL: -";
  }

  refreshRowSelection();
  refreshMarkerSelectionIcons();
}

function refreshMarkerSelectionIcons() {
  Object.entries(markers).forEach(([markerId, marker]) => {
    const aircraft = latestAircraftById.get(markerId);
    if (!aircraft) return;
    const isSelected = markerId === selectedAircraftId;
    const flow = getTrafficFlow(aircraft);
    if (
      marker.__airspacesimSelected !== isSelected ||
      marker.__airspacesimFlow !== flow
    ) {
      marker.setIcon(buildAircraftMarkerIcon(aircraft, isSelected));
      marker.__airspacesimSelected = isSelected;
      marker.__airspacesimFlow = flow;
    }
  });
}

function updateAircraftTable(aircraftData) {
  const tbody = document.getElementById("aircraft-table-body");
  const countNode = document.getElementById("aircraft-count");
  const syncNode = document.getElementById("aircraft-sync");

  knownAircraftIds.clear();
  aircraftData.forEach((aircraft) => {
    if (typeof aircraft?.id === "string" && aircraft.id.trim()) {
      knownAircraftIds.add(aircraft.id.trim());
    }
  });

  if (countNode) countNode.textContent = String(aircraftData.length);
  if (syncNode) syncNode.textContent = new Date().toLocaleTimeString();
  if (!tbody) return;

  tbody.innerHTML = "";
  if (aircraftData.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="4">No aircraft currently tracked.</td>';
    tbody.appendChild(row);
    refreshRowSelection();
    return;
  }

  aircraftData.forEach((aircraft) => {
    const row = document.createElement("tr");
    row.dataset.aircraftId = aircraft.id || "";
    row.addEventListener("click", () => setSelectedAircraft(aircraft.id || ""));
    const position = Array.isArray(aircraft.position)
      ? `${aircraft.position[0].toFixed(4)}, ${aircraft.position[1].toFixed(4)}`
      : "-";
    const flightLevel = formatFlightLevel(aircraft.flight_level, aircraft.altitude_ft);
    row.innerHTML = `
      <td>${aircraft.id ?? "-"}</td>
      <td>${aircraft.callsign ?? "-"}</td>
      <td>${flightLevel}</td>
      <td>${position}</td>
    `;
    tbody.appendChild(row);
  });
  refreshRowSelection();
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
  const isDevServerOrigin = window.location.port === "8080";
  const configuredCandidates = [];
  if (typeof sink === "string") {
    configuredCandidates.push(sink);
  } else if (typeof sink === "object" && sink !== null && typeof sink.url === "string") {
    configuredCandidates.push(sink.url);
  }

  const preferredWorkspaceSink = defaultEventSinkUrl();
  const sameOriginCandidates = [
    preferredWorkspaceSink,
    ...configuredCandidates,
    `${prefix}/api/events`,
    "/api/events",
  ];
  const devServerCandidates = [
    `http://${host}:8080/airspacesim-playground/api/events`,
    `http://${host}:8080${prefix}/api/events`,
    `http://${host}:8080/api/events`,
  ];
  const orderedCandidates = isDevServerOrigin
    ? [...sameOriginCandidates, ...devServerCandidates]
    : [...devServerCandidates, ...sameOriginCandidates];

  // Prefer dev_server endpoints when page is hosted on non-POST static servers (e.g., :5500).
  const resolved = orderedCandidates
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
  const flBtn = document.querySelector("#form-set-flight-level button[type='submit']");
  const simRateBtn = document.querySelector("#form-set-sim-rate button[type='submit']");

  if (sinkMode) {
    if (addBtn) addBtn.textContent = "Send ADD_AIRCRAFT";
    if (speedBtn) speedBtn.textContent = "Send SET_SPEED";
    if (flBtn) flBtn.textContent = "Send SET_FL";
    if (simRateBtn) simRateBtn.textContent = "Send SET_SIMULATION_SPEED";
    return;
  }

  if (addBtn) addBtn.textContent = "Queue ADD_AIRCRAFT";
  if (speedBtn) speedBtn.textContent = "Queue SET_SPEED";
  if (flBtn) flBtn.textContent = "Queue SET_FL";
  if (simRateBtn) simRateBtn.textContent = "Queue SET_SIMULATION_SPEED";
}

function setFormBusy(form, busy) {
  if (!form) return;
  form.dataset.busy = busy ? "1" : "0";
  const submitBtn = form.querySelector("button[type='submit']");
  if (!submitBtn) return;
  submitBtn.disabled = busy;
  if (busy) {
    if (!submitBtn.dataset.defaultLabel) {
      submitBtn.dataset.defaultLabel = submitBtn.textContent || "Submit";
    }
    submitBtn.textContent = "Sending...";
    return;
  }

  const defaultLabel = submitBtn.dataset.defaultLabel;
  if (defaultLabel) {
    submitBtn.textContent = defaultLabel;
  }
  applyControlButtonLabels();
}

function wireOperatorControls() {
  if (controlsReady) return;
  controlsReady = true;

  const addForm = document.getElementById("form-add-aircraft");
  const speedForm = document.getElementById("form-set-speed");
  const setFlForm = document.getElementById("form-set-flight-level");
  const simRateForm = document.getElementById("form-set-sim-rate");
  const copyBtn = document.getElementById("btn-copy-events");
  const clearBtn = document.getElementById("btn-clear-events");

  if (addForm) {
    addForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (addForm.dataset.busy === "1") return;
      setFormBusy(addForm, true);
      try {
        const aircraftId = document.getElementById("add-aircraft-id")?.value?.trim();
        const callsign = document.getElementById("add-callsign")?.value?.trim();
        const routeId = document.getElementById("add-route-id")?.value?.trim();
        const speedKt = Number(document.getElementById("add-speed-kt")?.value);
        const flightLevelRaw = document.getElementById("add-flight-level")?.value?.trim();
        const flightLevel = flightLevelRaw ? Number(flightLevelRaw) : null;
        if (!aircraftId || !routeId || !Number.isFinite(speedKt) || speedKt <= 0) {
          updateControlsStatus("Invalid ADD_AIRCRAFT input.", "err");
          return;
        }
        if (flightLevelRaw && (!Number.isFinite(flightLevel) || flightLevel < 0)) {
          updateControlsStatus("Invalid FL value for ADD_AIRCRAFT.", "err");
          return;
        }
        if (knownAircraftIds.has(aircraftId)) {
          updateControlsStatus(
            `Aircraft ID '${aircraftId}' already exists. Use a new ID or remove existing aircraft first.`,
            "warn"
          );
          return;
        }
        const payload = {
          aircraft_id: aircraftId,
          route_id: routeId,
          callsign: callsign || aircraftId,
          speed_kt: speedKt,
        };
        if (flightLevelRaw) {
          payload.flight_level = Math.round(flightLevel);
        }
        await queueOrSendEvent(
          buildEvent("ADD_AIRCRAFT", payload)
        );
      } finally {
        setFormBusy(addForm, false);
      }
    });
  }

  if (speedForm) {
    speedForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (speedForm.dataset.busy === "1") return;
      setFormBusy(speedForm, true);
      try {
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
      } finally {
        setFormBusy(speedForm, false);
      }
    });
  }

  if (setFlForm) {
    setFlForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (setFlForm.dataset.busy === "1") return;
      setFormBusy(setFlForm, true);
      try {
        const aircraftId = document.getElementById("set-fl-aircraft-id")?.value?.trim();
        const flightLevel = Number(document.getElementById("set-flight-level")?.value);
        if (!aircraftId || !Number.isFinite(flightLevel) || flightLevel < 0) {
          updateControlsStatus("Invalid SET_FL input.", "err");
          return;
        }
        await queueOrSendEvent(
          buildEvent("SET_FL", {
            aircraft_id: aircraftId,
            flight_level: Math.round(flightLevel),
          })
        );
      } finally {
        setFormBusy(setFlForm, false);
      }
    });
  }

  if (simRateForm) {
    simRateForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (simRateForm.dataset.busy === "1") return;
      setFormBusy(simRateForm, true);
      try {
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
      } finally {
        setFormBusy(simRateForm, false);
      }
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
  setSelectedAircraft(selectedAircraftId);
}

function buildAircraftMarkerIcon(aircraft, isSelected = false) {
  const color = getTrafficFlowColor(aircraft);
  const selectedClass = isSelected ? " is-selected" : "";
  const iconHtml = `
    <div class="aircraft-marker${selectedClass}" style="--aircraft-color: ${escapeHtml(color)};">
      <svg viewBox="0 0 24 24" class="aircraft-marker-svg" aria-hidden="true">
        <path fill="var(--aircraft-color)" d="M11 1.5c.8 0 1.4.6 1.6 1.3l1.2 6.2 7.3 3.1c.6.2 1 .8 1 1.4 0 .6-.4 1.2-1 1.4l-7.3 3.1-1.2 6.2c-.1.7-.8 1.3-1.6 1.3s-1.4-.6-1.6-1.3l-1.2-6.2L.9 15.4c-.5-.2-.9-.8-.9-1.4 0-.6.4-1.2.9-1.4l7.3-3.1 1.2-6.2c.2-.7.8-1.3 1.6-1.3z"/>
      </svg>
    </div>
  `;
  return L.divIcon({
    className: "aircraft-div-icon",
    html: iconHtml,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    tooltipAnchor: [0, 14],
    popupAnchor: [0, -14],
  });
}

function buildAircraftPopupContent(aircraft) {
  const flowLabel = getTrafficFlowLabel(aircraft);
  const flightLevel = formatFlightLevel(aircraft.flight_level, aircraft.altitude_ft);
  const verticalRate = Number(aircraft.vertical_rate_fpm);
  const verticalRateText = Number.isFinite(verticalRate) ? `${verticalRate.toFixed(0)} fpm` : "-";
  const updatedUtc = aircraft.updated_utc ? escapeHtml(aircraft.updated_utc) : "-";
  const routeId = aircraft.route_id ? escapeHtml(aircraft.route_id) : "-";
  const status = aircraft.status ? escapeHtml(aircraft.status) : "-";
  const callsign = aircraft.callsign ? escapeHtml(aircraft.callsign) : "-";
  const id = aircraft.id ? escapeHtml(aircraft.id) : "-";

  return `
    <div class="aircraft-popup">
      <div><strong>${callsign}</strong> (${id})</div>
      <div>Route: ${routeId}</div>
      <div>Level: ${flightLevel}</div>
      <div>Vertical: ${verticalRateText}</div>
      <div>Flow: ${flowLabel}</div>
      <div>Status: ${status}</div>
      <div>Updated: ${updatedUtc}</div>
    </div>
  `;
}

function normalizeAircraftData(payload) {
  if (Array.isArray(payload?.aircraft_data)) {
    return payload.aircraft_data.map((aircraft) => ({
      id: aircraft.id,
      callsign: aircraft.callsign,
      speed: aircraft.speed,
      flight_level: aircraft.flight_level,
      altitude_ft: aircraft.altitude_ft,
      vertical_rate_fpm: aircraft.vertical_rate_fpm,
      route_id: aircraft.route_id,
      status: aircraft.status,
      updated_utc: aircraft.updated_utc,
      traffic_flow: aircraft.traffic_flow,
      position: aircraft.position,
    }));
  }
  if (Array.isArray(payload?.data?.aircraft_data)) {
    return payload.data.aircraft_data.map((aircraft) => ({
      id: aircraft.id,
      callsign: aircraft.callsign,
      speed: aircraft.speed,
      flight_level: aircraft.flight_level,
      altitude_ft: aircraft.altitude_ft,
      vertical_rate_fpm: aircraft.vertical_rate_fpm,
      route_id: aircraft.route_id,
      status: aircraft.status,
      updated_utc: aircraft.updated_utc,
      traffic_flow: aircraft.traffic_flow,
      position: aircraft.position,
    }));
  }

  const canonical = payload?.data?.aircraft;
  if (!Array.isArray(canonical)) {
    return [];
  }

  return canonical.map((aircraft) => ({
    id: aircraft.id,
    callsign: aircraft.callsign,
    speed: aircraft.speed_kt,
    flight_level: aircraft.flight_level,
    altitude_ft: aircraft.altitude_ft,
    vertical_rate_fpm: aircraft.vertical_rate_fpm,
    route_id: aircraft.route_id,
    status: aircraft.status,
    updated_utc: aircraft.updated_utc,
    traffic_flow: aircraft.traffic_flow,
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
    const flightLevel = formatFlightLevel(aircraft.flight_level, aircraft.altitude_ft);
    const tooltipLabel = `${aircraft.callsign || markerId} | ${flightLevel}`;
    const isSelected = markerId === selectedAircraftId;

    if (markers[markerId]) {
      const existingMarker = markers[markerId];
      existingMarker.setLatLng(aircraft.position);
      existingMarker.setTooltipContent(tooltipLabel);
      existingMarker.setPopupContent(buildAircraftPopupContent(aircraft));
      const flow = getTrafficFlow(aircraft);
      if (
        existingMarker.__airspacesimFlow !== flow ||
        existingMarker.__airspacesimSelected !== isSelected
      ) {
        existingMarker.setIcon(buildAircraftMarkerIcon(aircraft, isSelected));
        existingMarker.__airspacesimFlow = flow;
        existingMarker.__airspacesimSelected = isSelected;
      }
      return;
    }

    const marker = L.marker(aircraft.position, {
      icon: buildAircraftMarkerIcon(aircraft, isSelected),
      keyboard: true,
    }).bindTooltip(tooltipLabel, {
      permanent: true,
      direction: "bottom",
    });
    marker.bindPopup(buildAircraftPopupContent(aircraft));
    marker.__airspacesimFlow = getTrafficFlow(aircraft);
    marker.__airspacesimSelected = isSelected;
    marker.on("click", () => {
      setSelectedAircraft(markerId);
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
      latestAircraftById.clear();
      syncMarkers([]);
      updateAircraftTable([]);
      setSelectedAircraft("");
      updateAircraftStatus("Aircraft feed unavailable (missing file).", "warn");
      return;
    }
    const aircraftData = normalizeAircraftData(data);
    latestAircraftById.clear();
    aircraftData.forEach((aircraft) => {
      if (typeof aircraft?.id === "string" && aircraft.id.trim()) {
        latestAircraftById.set(aircraft.id.trim(), aircraft);
      }
    });

    syncMarkers(aircraftData);
    updateAircraftTable(aircraftData);
    setSelectedAircraft(selectedAircraftId);
    updateAircraftStatus("Aircraft feed healthy.", "ok");
    lastFeedIssue = "";
  } catch (error) {
    if (lastFeedIssue !== "error") {
      console.error("Error fetching aircraft data:", error);
      lastFeedIssue = "error";
    }
    latestAircraftById.clear();
    syncMarkers([]);
    updateAircraftTable([]);
    setSelectedAircraft("");
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
