import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import type { LatLngBoundsExpression, LatLngTuple } from "leaflet";
import {
  Circle,
  CircleMarker,
  MapContainer,
  Polygon,
  Polyline,
  ScaleControl,
  Tooltip,
  ZoomControl,
  useMap,
} from "react-leaflet";

import type { ScenarioMapOverlay } from "../lib/scenario-map";
import type { RunAircraftStateResponse } from "../types/api";

export type AircraftLabelDirection = "left" | "right" | "top" | "bottom";
export type MapInspectTarget =
  | {
      type: "fix";
      id: string;
      name: string;
      detail: string;
      position: LatLngTuple;
    }
  | {
      type: "route";
      id: string;
      name: string;
      detail: string;
      position?: undefined;
    };
export interface MeasurementPoint {
  id: string;
  label: string;
  position: LatLngTuple;
  type: "aircraft" | "fix";
}

const DEFAULT_CENTER: LatLngTuple = [16.25, -40.0];
const MIN_DEFAULT_VIEW_NM = 56;
const VIEW_PADDING_FACTOR = 1.03;
const AIRCRAFT_MARKER_RADIUS = 7;
const AIRCRAFT_CLICK_TARGET_RADIUS = 18;
const AIRCRAFT_HEADING_VECTOR_NM = 10;
const SELECTED_AIRCRAFT_HEADING_VECTOR_NM = 16;

const AIRCRAFT_FLOW_COLORS = {
  arrival: {
    fill: "#e24c4b",
    stroke: "#641616",
  },
  departure: {
    fill: "#24a56a",
    stroke: "#0d4d31",
  },
  overflight: {
    fill: "#9a6a2f",
    stroke: "#4a2f12",
  },
  unknown: {
    fill: "#56c6ff",
    stroke: "#08283f",
  },
} as const;

interface TrafficMapProps {
  aircraft: RunAircraftStateResponse[];
  overlay: ScenarioMapOverlay;
  selectedAircraftId: string | null;
  aircraftLabelDirections: Record<string, AircraftLabelDirection>;
  onSelect: (aircraftId: string) => void;
  onInspect: (target: MapInspectTarget) => void;
  isMeasureMode: boolean;
  measurementPoints: MeasurementPoint[];
  onMeasurePick: (point: MeasurementPoint) => void;
}

interface MapViewportControllerProps {
  bounds: LatLngBoundsExpression | null;
  boundsKey: string;
  resetNonce: number;
}

interface FallbackPoint {
  id: string;
  label: string;
  position: LatLngTuple;
  tone: "point" | "aircraft" | "selected";
}

interface TrafficFallbackProps {
  aircraft: RunAircraftStateResponse[];
  overlay: ScenarioMapOverlay;
  selectedAircraftId: string | null;
}

function resolveAircraftFlowTone(trafficFlow: string):
  | "arrival"
  | "departure"
  | "overflight"
  | "unknown" {
  const normalizedFlow = trafficFlow.toLowerCase();
  if (normalizedFlow.includes("inbound") || normalizedFlow.includes("arrival")) {
    return "arrival";
  }
  if (normalizedFlow.includes("outbound") || normalizedFlow.includes("departure")) {
    return "departure";
  }
  if (
    normalizedFlow.includes("transit") ||
    normalizedFlow.includes("overflight") ||
    normalizedFlow.includes("overflying") ||
    normalizedFlow.includes("over")
  ) {
    return "overflight";
  }
  return "unknown";
}

function resolveDefaultLabelDirection(
  trafficFlow: string,
): AircraftLabelDirection {
  const flowTone = resolveAircraftFlowTone(trafficFlow);
  if (flowTone === "arrival") {
    return "left";
  }
  if (flowTone === "overflight") {
    return "top";
  }
  return "right";
}

function resolveLabelOffset(direction: AircraftLabelDirection): [number, number] {
  switch (direction) {
    case "left":
      return [-10, 0];
    case "top":
      return [0, -10];
    case "bottom":
      return [0, 10];
    case "right":
      return [10, 0];
  }
}

function formatAircraftLevelLabel(aircraft: RunAircraftStateResponse) {
  const currentLevel = `FL${aircraft.flight_level}`;
  const targetLevel = aircraft.target_flight_level;
  const verticalRate = aircraft.vertical_rate_fpm;
  if (
    targetLevel === null ||
    targetLevel === undefined ||
    targetLevel === aircraft.flight_level ||
    Math.abs(verticalRate) < 1
  ) {
    return currentLevel;
  }
  const trend = verticalRate > 0 ? "↑" : "↓";
  return `${currentLevel} ${trend} FL${targetLevel}`;
}

function buildAircraftMeasurementPoint(
  aircraft: RunAircraftStateResponse,
): MeasurementPoint {
  return {
    id: aircraft.id,
    label: aircraft.callsign ?? aircraft.id,
    position: aircraft.position_dd,
    type: "aircraft",
  };
}

function calculateBearingDeg(
  fromPosition: LatLngTuple,
  toPosition: LatLngTuple,
): number {
  const fromLat = (fromPosition[0] * Math.PI) / 180;
  const toLat = (toPosition[0] * Math.PI) / 180;
  const deltaLon = ((toPosition[1] - fromPosition[1]) * Math.PI) / 180;
  const y = Math.sin(deltaLon) * Math.cos(toLat);
  const x =
    Math.cos(fromLat) * Math.sin(toLat) -
    Math.sin(fromLat) * Math.cos(toLat) * Math.cos(deltaLon);

  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

function projectHeadingPoint(
  position: LatLngTuple,
  headingDeg: number,
  distanceNm: number,
): LatLngTuple {
  const earthRadiusNm = 3440.065;
  const lat1 = (position[0] * Math.PI) / 180;
  const lon1 = (position[1] * Math.PI) / 180;
  const bearing = (headingDeg * Math.PI) / 180;
  const angularDistance = distanceNm / earthRadiusNm;

  const lat2 = Math.asin(
    Math.sin(lat1) * Math.cos(angularDistance) +
      Math.cos(lat1) * Math.sin(angularDistance) * Math.cos(bearing),
  );
  const lon2 =
    lon1 +
    Math.atan2(
      Math.sin(bearing) * Math.sin(angularDistance) * Math.cos(lat1),
      Math.cos(angularDistance) - Math.sin(lat1) * Math.sin(lat2),
    );

  return [
    (lat2 * 180) / Math.PI,
    ((((lon2 * 180) / Math.PI + 540) % 360) - 180),
  ];
}

function MapRenderController() {
  const map = useMap();

  useEffect(() => {
    const invalidateMapSize = () => {
      map.invalidateSize(false);
    };
    const scheduleInvalidate = () => {
      window.requestAnimationFrame(invalidateMapSize);
    };
    const firstFrame = window.requestAnimationFrame(invalidateMapSize);
    const secondFrame = window.setTimeout(invalidateMapSize, 250);
    const thirdFrame = window.setTimeout(invalidateMapSize, 900);
    const container = map.getContainer();
    const observer =
      typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(scheduleInvalidate);

    observer?.observe(container);
    window.addEventListener("resize", scheduleInvalidate);
    window.addEventListener("orientationchange", scheduleInvalidate);

    return () => {
      window.cancelAnimationFrame(firstFrame);
      window.clearTimeout(secondFrame);
      window.clearTimeout(thirdFrame);
      observer?.disconnect();
      window.removeEventListener("resize", scheduleInvalidate);
      window.removeEventListener("orientationchange", scheduleInvalidate);
    };
  }, [map]);

  return null;
}

function buildBounds(
  aircraft: RunAircraftStateResponse[],
  overlay: ScenarioMapOverlay,
): LatLngBoundsExpression | null {
  const airspacePositions = overlay.airspaces.flatMap((airspace) =>
    airspace.type === "circle" ? [airspace.center] : airspace.points,
  );
  const fallbackPositions: LatLngTuple[] = [
    ...airspacePositions,
    ...aircraft.map((item) => item.position_dd),
    ...overlay.points.map((point) => point.position),
    ...overlay.routes.flatMap((route) => route.path),
  ];
  const positions = airspacePositions.length > 0 ? airspacePositions : fallbackPositions;

  if (positions.length === 0) {
    return null;
  }

  const extent = buildExtent(positions);
  if (!extent) {
    return null;
  }

  const boundsExtents = overlay.airspaces.reduce(
    (currentExtent, airspace) => {
      if (airspace.type === "polygon") {
        const polygonExtent = buildExtent(airspace.points);
        if (!polygonExtent) {
          return currentExtent;
        }
        return {
          minLat: Math.min(currentExtent.minLat, polygonExtent.minLat),
          maxLat: Math.max(currentExtent.maxLat, polygonExtent.maxLat),
          minLon: Math.min(currentExtent.minLon, polygonExtent.minLon),
          maxLon: Math.max(currentExtent.maxLon, polygonExtent.maxLon),
        };
      }

      const latRadius = airspace.radiusNm / 60;
      const centerLatRadians = (airspace.center[0] * Math.PI) / 180;
      const lonRadius =
        airspace.radiusNm /
        (60 * Math.max(Math.cos(centerLatRadians), 0.2));

      return {
        minLat: Math.min(currentExtent.minLat, airspace.center[0] - latRadius),
        maxLat: Math.max(currentExtent.maxLat, airspace.center[0] + latRadius),
        minLon: Math.min(currentExtent.minLon, airspace.center[1] - lonRadius),
        maxLon: Math.max(currentExtent.maxLon, airspace.center[1] + lonRadius),
      };
    },
    extent,
  );

  const displayExtents = boundsExtents;

  const centerLat = (displayExtents.minLat + displayExtents.maxLat) / 2;
  const centerLon = (displayExtents.minLon + displayExtents.maxLon) / 2;
  const minLatSpan = MIN_DEFAULT_VIEW_NM / 60;
  const centerLatRadians = (centerLat * Math.PI) / 180;
  const minLonSpan =
    MIN_DEFAULT_VIEW_NM / (60 * Math.max(Math.cos(centerLatRadians), 0.2));
  const latSpan = Math.max(displayExtents.maxLat - displayExtents.minLat, minLatSpan);
  const lonSpan = Math.max(displayExtents.maxLon - displayExtents.minLon, minLonSpan);
  const paddedLatSpan = latSpan * VIEW_PADDING_FACTOR;
  const paddedLonSpan = lonSpan * VIEW_PADDING_FACTOR;

  return [
    [centerLat - paddedLatSpan / 2, centerLon - paddedLonSpan / 2],
    [centerLat + paddedLatSpan / 2, centerLon + paddedLonSpan / 2],
  ];
}

function buildExtent(points: LatLngTuple[]) {
  if (points.length === 0) {
    return null;
  }

  const lats = points.map((point) => point[0]);
  const lons = points.map((point) => point[1]);
  return {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
  };
}

function createProjector(points: LatLngTuple[]) {
  const extent = buildExtent(points);
  const pad = 8;
  const width = 100;
  const height = 100;

  if (!extent) {
    return (_point: LatLngTuple): [number, number] => [width / 2, height / 2];
  }

  const lonSpan = Math.max(extent.maxLon - extent.minLon, 0.01);
  const latSpan = Math.max(extent.maxLat - extent.minLat, 0.01);
  const usableWidth = width - pad * 2;
  const usableHeight = height - pad * 2;

  return ([lat, lon]: LatLngTuple): [number, number] => {
    const x = pad + ((lon - extent.minLon) / lonSpan) * usableWidth;
    const y = height - pad - ((lat - extent.minLat) / latSpan) * usableHeight;
    return [x, y];
  };
}

function TrafficFallback({
  aircraft,
  overlay,
  selectedAircraftId,
}: TrafficFallbackProps) {
  const projected = useMemo(() => {
    const allPoints: LatLngTuple[] = [
      ...aircraft.map((item) => item.position_dd),
      ...overlay.points.map((point) => point.position),
      ...overlay.airspaces.flatMap((airspace) =>
        airspace.type === "circle" ? [airspace.center] : airspace.points,
      ),
    ];
    const project = createProjector(allPoints);

    return {
      routes: overlay.routes.map((route) => ({
        id: route.id,
        name: route.name,
        path: route.path.map(project),
      })),
      airspaces: overlay.airspaces.map((airspace) => {
        if (airspace.type === "polygon") {
          return {
            type: "polygon" as const,
            id: airspace.id,
            points: airspace.points.map(project),
          };
        }

        const center = project(airspace.center);
        const edge = project([
          airspace.center[0],
          airspace.center[1] + airspace.radiusNm / 60,
        ]);
        const radius = Math.max(Math.abs(edge[0] - center[0]), 4);
        return {
          type: "circle" as const,
          id: airspace.id,
          center,
          radius,
        };
      }),
      points: [
        ...overlay.points.map<FallbackPoint>((point) => ({
          id: point.id,
          label: point.id,
          position: point.position,
          tone: "point",
        })),
        ...aircraft.map<FallbackPoint>((item) => ({
          id: item.id,
          label: item.callsign ?? item.id,
          position: item.position_dd,
          tone: item.id === selectedAircraftId ? "selected" : "aircraft",
        })),
      ].map((point) => ({
        ...point,
        projected: project(point.position),
      })),
    };
  }, [aircraft, overlay, selectedAircraftId]);

  return (
    <div className="traffic-map-fallback" aria-hidden="true">
      <svg
        className="traffic-map-fallback-svg"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        {projected.airspaces.map((airspace) => (
          airspace.type === "circle" ? (
            <circle
              key={airspace.id}
              cx={airspace.center[0]}
              cy={airspace.center[1]}
              r={airspace.radius}
              className="traffic-map-fallback-airspace"
            />
          ) : (
            <polygon
              key={airspace.id}
              points={airspace.points.map((point) => point.join(",")).join(" ")}
              className="traffic-map-fallback-airspace"
            />
          )
        ))}

        {projected.routes.map((route) => (
          <polyline
            key={route.id}
            points={route.path.map((point) => point.join(",")).join(" ")}
            className="traffic-map-fallback-route"
          />
        ))}

        {projected.points.map((point) => (
          <g key={point.id}>
            <circle
              cx={point.projected[0]}
              cy={point.projected[1]}
              r={point.tone === "point" ? 1.2 : point.tone === "selected" ? 2.2 : 1.8}
              className={`traffic-map-fallback-point traffic-map-fallback-point-${point.tone}`}
            />
            {point.tone !== "point" ? (
              <text
                x={point.projected[0] + 1.4}
                y={point.projected[1] - 1.4}
                className={`traffic-map-fallback-label traffic-map-fallback-label-${point.tone}`}
              >
                {point.label}
              </text>
            ) : null}
          </g>
        ))}
      </svg>
    </div>
  );
}

function buildBoundsKey(
  aircraft: RunAircraftStateResponse[],
  overlay: ScenarioMapOverlay,
): string {
  return [
    aircraft.map((item) => item.id).sort().join(","),
    overlay.points.map((item) => item.id).sort().join(","),
    overlay.routes.map((item) => item.id).sort().join(","),
    overlay.airspaces.map((item) => item.id).sort().join(","),
  ].join("|");
}

function resolveMapCenter(
  aircraft: RunAircraftStateResponse[],
  overlay: ScenarioMapOverlay,
  selectedAircraftId: string | null,
): LatLngTuple {
  const selectedAircraft = aircraft.find((item) => item.id === selectedAircraftId);
  if (selectedAircraft) {
    return selectedAircraft.position_dd;
  }

  if (aircraft.length > 0) {
    return aircraft[0].position_dd;
  }

  if (overlay.points.length > 0) {
    return overlay.points[0].position;
  }

  if (overlay.airspaces.length > 0) {
    const firstAirspace = overlay.airspaces[0];
    return firstAirspace.type === "circle"
      ? firstAirspace.center
      : firstAirspace.points[0];
  }

  return DEFAULT_CENTER;
}

function MapViewportController({
  bounds,
  boundsKey,
  resetNonce,
}: MapViewportControllerProps) {
  const map = useMap();
  const lastFittedBoundsKey = useRef<string | null>(null);
  const lastResetNonce = useRef(resetNonce);

  useEffect(() => {
    const shouldReset = lastResetNonce.current !== resetNonce;
    if (!bounds || (lastFittedBoundsKey.current === boundsKey && !shouldReset)) {
      return;
    }

    map.fitBounds(bounds, {
      padding: [18, 18],
      maxZoom: 8,
      animate: shouldReset,
    });
    lastFittedBoundsKey.current = boundsKey;
    lastResetNonce.current = resetNonce;
  }, [bounds, boundsKey, map, resetNonce]);

  return null;
}

export function TrafficMap({
  aircraft,
  overlay,
  selectedAircraftId,
  aircraftLabelDirections,
  onSelect,
  onInspect,
  isMeasureMode,
  measurementPoints,
  onMeasurePick,
}: TrafficMapProps) {
  const [resetViewNonce, setResetViewNonce] = useState(0);
  const selectedAircraft =
    aircraft.find((item) => item.id === selectedAircraftId) ?? null;
  const routeMembershipByPointId = useMemo(() => {
    const memberships = new Map<string, string[]>();
    overlay.routes.forEach((route) => {
      route.waypointIds.forEach((waypointId) => {
        const routeIds = memberships.get(waypointId) ?? [];
        routeIds.push(route.id);
        memberships.set(waypointId, routeIds);
      });
    });
    return memberships;
  }, [overlay.routes]);
  const bounds = buildBounds(aircraft, overlay);
  const boundsKey = buildBoundsKey(aircraft, overlay);
  const center = resolveMapCenter(aircraft, overlay, selectedAircraftId);
  const hasMapContent =
    aircraft.length > 0 ||
    overlay.points.length > 0 ||
    overlay.routes.length > 0 ||
    overlay.airspaces.length > 0;

  if (!hasMapContent) {
    return (
      <div className="traffic-map-shell traffic-map-shell-empty">
        <div>
          <p className="eyebrow">Sector Display</p>
          <p className="traffic-empty-copy">
            No aircraft or scenario overlays are available for the current snapshot.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="traffic-map-shell">
      <TrafficFallback
        aircraft={aircraft}
        overlay={overlay}
        selectedAircraftId={selectedAircraftId}
      />

      <div className="traffic-map-stage">
        <MapContainer
          center={center}
          zoom={6}
          zoomControl={false}
          attributionControl={false}
          dragging={false}
          keyboard={false}
          scrollWheelZoom
          doubleClickZoom
          touchZoom
          className="traffic-map"
        >
          <ZoomControl position="bottomright" />
          <ScaleControl position="bottomleft" />
          <MapRenderController />
          <MapViewportController
            bounds={bounds}
            boundsKey={boundsKey}
            resetNonce={resetViewNonce}
          />

          {overlay.airspaces.map((airspace) =>
            airspace.type === "circle" ? (
              <Circle
                key={airspace.id}
                center={airspace.center}
                radius={airspace.radiusMeters}
                interactive={false}
                pathOptions={{
                  color: "#8fdcff",
                  weight: 2.4,
                  opacity: 0.86,
                  dashArray: "10 8",
                  fillColor: "#0b3e54",
                  fillOpacity: 0.1,
                }}
              >
                <Tooltip sticky>
                  {airspace.name} · {airspace.radiusNm} NM
                </Tooltip>
              </Circle>
            ) : (
              <Polygon
                key={airspace.id}
                positions={airspace.points}
                interactive={false}
                pathOptions={{
                  color: "#8fdcff",
                  weight: 2.4,
                  opacity: 0.86,
                  dashArray: "10 8",
                  fillColor: "#0b3e54",
                  fillOpacity: 0.1,
                }}
              >
                <Tooltip sticky>{airspace.name}</Tooltip>
              </Polygon>
            )
          )}

          {overlay.routes.map((route) => (
            <Polyline
              key={route.id}
              positions={route.path}
              eventHandlers={{
                click: () =>
                  onInspect({
                    type: "route",
                    id: route.id,
                    name: route.name,
                    detail: `${route.waypointIds.length} fixes · ${route.waypointIds.join(" -> ")}`,
                  }),
              }}
              pathOptions={{
                color:
                  route.id === selectedAircraft?.route_id ? "#c9f5ff" : "#4da6cf",
                weight: route.id === selectedAircraft?.route_id ? 4.4 : 2.3,
                opacity: route.id === selectedAircraft?.route_id ? 0.96 : 0.58,
              }}
            >
              <Tooltip sticky>{route.name}</Tooltip>
            </Polyline>
          ))}

          {overlay.points.map((point) => (
            <CircleMarker
              key={point.id}
              center={point.position}
              radius={4}
              eventHandlers={{
                click: () => {
                  if (isMeasureMode) {
                    onMeasurePick({
                      id: point.id,
                      label: point.id,
                      position: point.position,
                      type: "fix",
                    });
                    return;
                  }
                  onInspect({
                    type: "fix",
                    id: point.id,
                    name: point.name,
                    detail: `${point.type} · R${calculateBearingDeg(
                      DEFAULT_CENTER,
                      point.position,
                    )
                      .toFixed(0)
                      .padStart(3, "0")} from center · Routes ${
                      routeMembershipByPointId.get(point.id)?.join(", ") ?? "none"
                    }`,
                    position: point.position,
                  });
                },
              }}
              pathOptions={{
                color: "#092336",
                weight: 1.6,
                fillColor: "#d9f7ff",
                fillOpacity: 0.9,
              }}
            >
              <Tooltip direction="top" offset={[0, -6]}>
                {point.name} · {point.id}
              </Tooltip>
            </CircleMarker>
          ))}

          {aircraft.map((item) => {
            const isSelected = item.id === selectedAircraftId;
            const flowTone = resolveAircraftFlowTone(item.traffic_flow);
            const flowColors = AIRCRAFT_FLOW_COLORS[flowTone];
            const vectorEnd = projectHeadingPoint(
              item.position_dd,
              item.heading_deg,
              isSelected
                ? SELECTED_AIRCRAFT_HEADING_VECTOR_NM
                : AIRCRAFT_HEADING_VECTOR_NM,
            );
            return (
              <Fragment key={`${item.id}-heading-vector`}>
                <Polyline
                  positions={[item.position_dd, vectorEnd]}
                  interactive={false}
                  pathOptions={{
                    color: "#06131d",
                    weight: isSelected ? 7 : 5,
                    opacity: 0.82,
                    lineCap: "round",
                  }}
                />
                <Polyline
                  positions={[item.position_dd, vectorEnd]}
                  interactive={false}
                  pathOptions={{
                    color: isSelected ? "#ffffff" : flowColors.fill,
                    weight: isSelected ? 4 : 2.75,
                    opacity: isSelected ? 1 : 0.96,
                    lineCap: "round",
                  }}
                />
                <CircleMarker
                  center={vectorEnd}
                  radius={isSelected ? 3.5 : 2.5}
                  interactive={false}
                  pathOptions={{
                    color: "#06131d",
                    weight: 1.5,
                    fillColor: isSelected ? "#ffffff" : flowColors.fill,
                    fillOpacity: 1,
                  }}
                />
              </Fragment>
            );
          })}

          {aircraft.map((item) => {
            const isSelected = item.id === selectedAircraftId;
            const flowTone = resolveAircraftFlowTone(item.traffic_flow);
            const flowColors = AIRCRAFT_FLOW_COLORS[flowTone];
            const aircraftLabel = `${item.callsign ?? item.id} | ${formatAircraftLevelLabel(item)}`;
            const labelDirection =
              aircraftLabelDirections[item.id] ??
              resolveDefaultLabelDirection(item.traffic_flow);
            return (
              <Fragment key={item.id}>
                <CircleMarker
                  center={item.position_dd}
                  radius={AIRCRAFT_CLICK_TARGET_RADIUS}
                  eventHandlers={{
                    click: () => {
                      if (isMeasureMode) {
                        onMeasurePick(buildAircraftMeasurementPoint(item));
                        return;
                      }
                      onSelect(item.id);
                    },
                  }}
                  pathOptions={{
                    color: "#ffffff",
                    weight: 1,
                    opacity: 0.02,
                    fillColor: "#ffffff",
                    fillOpacity: 0.02,
                  }}
                />
                <CircleMarker
                  center={item.position_dd}
                  radius={AIRCRAFT_MARKER_RADIUS}
                  eventHandlers={{
                    click: () => {
                      if (isMeasureMode) {
                        onMeasurePick(buildAircraftMeasurementPoint(item));
                        return;
                      }
                      onSelect(item.id);
                    },
                  }}
                  pathOptions={{
                    color: isSelected ? "#071018" : flowColors.stroke,
                    weight: isSelected ? 3 : 2,
                    fillColor: flowColors.fill,
                    fillOpacity: 1,
                  }}
                >
                  <Tooltip
                    key={`${item.id}-${labelDirection}`}
                    permanent
                    direction={labelDirection}
                    offset={resolveLabelOffset(labelDirection)}
                    opacity={1}
                    className={`traffic-map-aircraft-label traffic-map-aircraft-label-${flowTone}`}
                  >
                    {aircraftLabel}
                  </Tooltip>
                </CircleMarker>
              </Fragment>
            );
          })}

          {measurementPoints.length === 2 ? (
            <Polyline
              positions={[
                measurementPoints[0].position,
                measurementPoints[1].position,
              ]}
              interactive={false}
              pathOptions={{
                color: "#ffe08a",
                weight: 3,
                opacity: 0.96,
                dashArray: "8 8",
              }}
            />
          ) : null}
        </MapContainer>
      </div>

      <div className="traffic-map-banner">
        <p className="eyebrow">Sector Display</p>
        <strong>
          {aircraft.length} aircraft · {overlay.routes.length} routes ·{" "}
          {overlay.airspaces.length} sectors
        </strong>
      </div>

      <button
        type="button"
        className="traffic-map-reset"
        onClick={() => setResetViewNonce((currentNonce) => currentNonce + 1)}
      >
        Reset View
      </button>

      {aircraft.length === 0 ? (
        <div className="traffic-map-note">
          No visible traffic in the current filter
        </div>
      ) : null}

      <div className="traffic-map-footer">
        <span>Simulation surface</span>
        <span>
          {selectedAircraft ? `${selectedAircraft.callsign ?? selectedAircraft.id} focused` : "Select an aircraft to focus"}
        </span>
      </div>
    </div>
  );
}
