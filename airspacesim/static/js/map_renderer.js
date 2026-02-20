// static/js/map_renderer.js
import {
  DATA_BASE_URL,
  loadUiRuntimeConfig,
  resolveUiCandidates,
  resolveUiPollIntervalMs,
} from "./ui_runtime.js";

const DEFAULT_CONFIG_CANDIDATES = [
  new URL("map_config.v1.json", DATA_BASE_URL).toString(),
  new URL("airspace_config.json", DATA_BASE_URL).toString(),
  new URL("gao_airspace.json", DATA_BASE_URL).toString(),
  new URL("gao_airspace_config.json", DATA_BASE_URL).toString(),
];

export let map;
let lastZoomFocus = null;

function resetExistingMapInstance() {
  const existingMap = globalThis.__airspacesimLeafletMap;
  if (existingMap && typeof existingMap.remove === "function") {
    existingMap.remove();
  }

  const container = document.getElementById("map");
  if (container && container._leaflet_id) {
    container._leaflet_id = null;
  }
}

function getRenderLayer(config, type) {
  const layers = config?.render?.layers;
  if (!Array.isArray(layers)) return null;
  return layers.find((layer) => layer.type === type) || null;
}

function resolveIconPath(iconUrl) {
  if (!iconUrl || typeof iconUrl !== "string") return iconUrl;
  if (iconUrl.startsWith("static/")) return `../${iconUrl}`;
  if (iconUrl.startsWith("./static/")) return `../${iconUrl.slice(2)}`;
  if (iconUrl.startsWith("../icons/")) return `../static/icons/${iconUrl.slice("../icons/".length)}`;
  if (iconUrl.startsWith("icons/")) return `../static/icons/${iconUrl.slice("icons/".length)}`;
  return iconUrl;
}

function resolveMapCenter(config) {
  const renderCenter = config?.render?.map?.center;
  if (Array.isArray(config.center)) return config.center;
  if (Array.isArray(renderCenter)) return renderCenter;

  const pointId = renderCenter?.point_id;
  if (!pointId) return [0, 0];

  const marker = (config.elements || []).find(
    (element) =>
      element.type === "marker" &&
      (element.source_point_id === pointId || element.source_navaid_id === pointId || element.label_text === pointId)
  );
  return Array.isArray(marker?.coords) ? marker.coords : [0, 0];
}

function updateConfigStatus(message) {
  const node = document.getElementById("config-status");
  if (node) {
    node.textContent = message;
  }
}

function updateElementPanel(summary, routeDetails) {
  const routeCount = document.getElementById("route-count");
  const zoneCount = document.getElementById("zone-count");
  const navCount = document.getElementById("nav-count");
  const routeList = document.getElementById("route-list");

  if (routeCount) routeCount.textContent = String(summary.routes);
  if (zoneCount) zoneCount.textContent = String(summary.zones);
  if (navCount) navCount.textContent = String(summary.navAids);

  if (routeList) {
    routeList.innerHTML = "";
    if (routeDetails.length === 0) {
      const empty = document.createElement("li");
      empty.textContent = "No routes found in config.";
      routeList.appendChild(empty);
      return;
    }

    routeDetails.forEach((route) => {
      const item = document.createElement("li");
      item.textContent = `${route.name} (${route.points} points)`;
      routeList.appendChild(item);
    });
  }
}

async function fetchFirstAvailableJson(candidates) {
  for (const url of candidates) {
    try {
      const response = await fetch(url);
      if (!response.ok) continue;
      return await response.json();
    } catch (_) {
      // Try next candidate.
    }
  }
  throw new Error(`No valid config found in: ${candidates.join(", ")}`);
}

function normalizeMapConfig(payload) {
  if (payload?.schema?.name === "airspacesim.map_config" && payload?.schema?.version === "1.0") {
    return payload.data || {};
  }
  return payload;
}

function initializeMap(config, runtimeConfig) {
  resetExistingMapInstance();
  const renderMap = config?.render?.map || {};
  const center = resolveMapCenter(config);
  const zoom = config.zoom || renderMap.zoom || 8;
  const tileLayer = config.tile_layer || renderMap.tile_layer;
  const pollIntervalCandidate =
    renderMap.aircraft_poll_interval_ms ??
    renderMap.poll_interval_ms ??
    config.aircraft_poll_interval_ms;
  const pollIntervalMs = Number(pollIntervalCandidate);
  const mapPollIntervalMs = Number.isFinite(pollIntervalMs) && pollIntervalMs >= 250 ? Math.trunc(pollIntervalMs) : 1000;
  globalThis.__airspacesimAircraftPollIntervalMs = resolveUiPollIntervalMs(runtimeConfig, mapPollIntervalMs);

  map = L.map("map").setView(center, zoom);
  globalThis.__airspacesimLeafletMap = map;

  // Keep zoom target stable: after wheel zoom, center map on the zoomed area.
  map.on("wheel", (event) => {
    if (event && event.latlng) {
      lastZoomFocus = event.latlng;
    }
  });

  map.on("zoomend", () => {
    if (lastZoomFocus) {
      map.panTo(lastZoomFocus, { animate: false });
      lastZoomFocus = null;
    }
  });

  const layers = {
    routes: L.layerGroup().addTo(map),
    zones: L.layerGroup().addTo(map),
    navAids: L.layerGroup().addTo(map),
    aircraft: L.layerGroup().addTo(map),
  };

  if (tileLayer) {
    L.tileLayer(tileLayer.url, {
      attribution: tileLayer.attribution,
      maxZoom: 19,
    }).addTo(map);
  }

  const routeRender = getRenderLayer(config, "routes");
  const zoneRender = getRenderLayer(config, "airspaces");
  const pointRender = getRenderLayer(config, "points");

  const summary = { routes: 0, zones: 0, navAids: 0 };
  const routeDetails = [];
  const bounds = [];

  (config.elements || []).forEach((element) => {
    if (element.type === "polyline") {
      summary.routes += 1;
      const routeStyle = routeRender?.style || {};
      const line = L.polyline(element.coords || [], {
        color: element.color || routeStyle.color || "#1f8c53",
        weight: element.weight || routeStyle.weight || 3,
        opacity: element.opacity || routeStyle.opacity || 0.95,
      }).addTo(layers.routes);
      if (element.name) line.bindPopup(element.name);
      if (Array.isArray(element.coords)) {
        bounds.push(...element.coords);
        routeDetails.push({ name: element.name || "Unnamed Route", points: element.coords.length });
      }
    } else if (element.type === "circle") {
      summary.zones += 1;
      const zoneStroke = zoneRender?.style?.stroke || {};
      const zoneFill = zoneRender?.style?.fill || {};
      const zone = L.circle(element.center, {
        radius: element.radius,
        color: element.color || zoneStroke.color || "#b25700",
        opacity: element.opacity || zoneStroke.opacity || 1,
        dashArray: element.dash_array || zoneStroke.dash_array || undefined,
        fillColor: element.fill_color || zoneFill.color || "#b25700",
        fillOpacity: element.fill_opacity || zoneFill.opacity || 0.18,
        interactive: element.interactive ?? false,
      }).addTo(layers.zones);
      if (element.name && (element.interactive ?? false)) zone.bindPopup(element.name);
      if (element.center) bounds.push(element.center);
    } else if (element.type === "marker") {
      summary.navAids += 1;
      const markerId = element.source_point_id || element.source_navaid_id || element.label_text;
      const pointDefaults = pointRender?.defaults || {};
      const pointOverride = markerId ? pointRender?.overrides?.[markerId] : null;
      const iconUrl = resolveIconPath(
        element.icon_url || pointOverride?.marker_icon || pointDefaults.marker_icon || "../icons/triangle_9.svg"
      );
      const iconSize =
        element.icon_size || pointOverride?.marker_icon_size || pointDefaults.marker_icon_size || [18, 18];
      const marker = L.marker(element.coords, {
        icon: L.icon({
          iconUrl,
          iconSize,
        }),
      }).addTo(layers.navAids);
      marker.bindPopup(element.popup_text || element.name || "Marker");
      if (element.label_text) {
        marker.bindTooltip(element.label_text, { permanent: true, direction: "top" });
      }
      if (element.coords) bounds.push(element.coords);
    }
  });

  if (bounds.length > 1) {
    map.fitBounds(bounds, { padding: [24, 24] });
  }

  L.control
    .layers(null, {
      Routes: layers.routes,
      Zones: layers.zones,
      "Nav Aids": layers.navAids,
      Aircraft: layers.aircraft,
    })
    .addTo(map);

  map.aircraftLayer = layers.aircraft;
  updateElementPanel(summary, routeDetails);
  updateConfigStatus("Config loaded");
  document.dispatchEvent(new CustomEvent("airspacesim:map-ready"));
}

async function loadMapConfig() {
  updateConfigStatus("Loading config...");
  try {
    const runtimeConfig = await loadUiRuntimeConfig();
    const configCandidates = resolveUiCandidates(runtimeConfig, "map_config", DEFAULT_CONFIG_CANDIDATES);
    const payload = await fetchFirstAvailableJson(configCandidates);
    const config = normalizeMapConfig(payload);
    initializeMap(config, runtimeConfig);
  } catch (error) {
    updateConfigStatus("Config unavailable");
    console.error("Error loading map configuration:", error);
  }
}

loadMapConfig();
