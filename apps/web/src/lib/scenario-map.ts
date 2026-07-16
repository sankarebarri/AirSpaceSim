import type { ScenarioResponse } from "../types/api";

const NM_TO_METERS = 1852;

export interface ScenarioMapPoint {
  id: string;
  name: string;
  type: string;
  position: [number, number];
}

export interface ScenarioMapRoute {
  id: string;
  name: string;
  waypointIds: string[];
  path: [number, number][];
}

export type ScenarioMapAirspace =
  | ScenarioMapCircleAirspace
  | ScenarioMapPolygonAirspace;

export interface ScenarioMapCircleAirspace {
  type: "circle";
  id: string;
  name: string;
  centerPointId: string;
  center: [number, number];
  radiusNm: number;
  radiusMeters: number;
}

export interface ScenarioMapPolygonAirspace {
  type: "polygon";
  id: string;
  name: string;
  points: [number, number][];
}

export interface ScenarioMapOverlay {
  points: ScenarioMapPoint[];
  routes: ScenarioMapRoute[];
  airspaces: ScenarioMapAirspace[];
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function asPositiveNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value > 0
    ? value
    : null;
}

function readPosition(value: unknown): [number, number] | null {
  if (!Array.isArray(value) || value.length < 2) {
    return null;
  }

  const [latitude, longitude] = value;
  if (
    typeof latitude !== "number" ||
    !Number.isFinite(latitude) ||
    typeof longitude !== "number" ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  return [latitude, longitude];
}

function readPointPosition(value: unknown): [number, number] | null {
  const pointRecord = asRecord(value);
  const coordRecord = asRecord(pointRecord?.coord);
  return readPosition(coordRecord?.dd);
}

export function parseScenarioMapOverlay(
  scenario: ScenarioResponse | null | undefined,
): ScenarioMapOverlay {
  const airspaceEnvelope = asRecord(scenario?.airspace_payload);
  const dataRecord = asRecord(airspaceEnvelope?.data);
  const rawPoints = asRecord(dataRecord?.points);

  const points: ScenarioMapPoint[] = Object.entries(rawPoints ?? {}).flatMap(
    ([pointId, pointValue]) => {
      const pointRecord = asRecord(pointValue);
      const position = readPointPosition(pointRecord);
      if (!position) {
        return [];
      }

      return [
        {
          id: pointId,
          name: asString(pointRecord?.name) ?? pointId,
          type: asString(pointRecord?.type) ?? "point",
          position,
        },
      ];
    },
  );

  const pointsById = new Map(points.map((point) => [point.id, point]));

  const routes: ScenarioMapRoute[] = Array.isArray(dataRecord?.routes)
    ? dataRecord.routes.flatMap((routeValue, index) => {
        const routeRecord = asRecord(routeValue);
        const waypointIds = Array.isArray(routeRecord?.waypoint_ids)
          ? routeRecord.waypoint_ids.filter(
              (value): value is string => typeof value === "string" && Boolean(value),
            )
          : [];
        const path = waypointIds
          .map((waypointId) => pointsById.get(waypointId)?.position ?? null)
          .filter(
            (position): position is [number, number] => position !== null,
          );

        if (path.length < 2) {
          return [];
        }

        const routeId =
          asString(routeRecord?.id) ?? `route-${index + 1}`;

        return [
          {
            id: routeId,
            name: asString(routeRecord?.name) ?? routeId,
            waypointIds,
            path,
          },
        ];
      })
    : [];

  const airspaces: ScenarioMapAirspace[] = Array.isArray(dataRecord?.airspaces)
    ? dataRecord.airspaces.flatMap((airspaceValue, index) => {
        const airspaceRecord = asRecord(airspaceValue);
        const airspaceType = asString(airspaceRecord?.type) ?? "circle";
        const airspaceId =
          asString(airspaceRecord?.id) ?? `airspace-${index + 1}`;
        const airspaceName = asString(airspaceRecord?.name) ?? airspaceId;

        if (airspaceType === "polygon") {
          const polygonPoints = Array.isArray(airspaceRecord?.points)
            ? airspaceRecord.points
                .map((position) => readPosition(position))
                .filter(
                  (position): position is [number, number] => position !== null,
                )
            : [];

          if (polygonPoints.length < 3) {
            return [];
          }

          return [
            {
              type: "polygon",
              id: airspaceId,
              name: airspaceName,
              points: polygonPoints,
            },
          ];
        }

        const centerPointId = asString(airspaceRecord?.center_point_id);
        const radiusNm = asPositiveNumber(airspaceRecord?.radius_nm);

        if (!centerPointId || radiusNm === null) {
          return [];
        }

        const centerPoint = pointsById.get(centerPointId);
        if (!centerPoint) {
          return [];
        }

        return [
          {
            type: "circle",
            id: airspaceId,
            name: airspaceName,
            centerPointId,
            center: centerPoint.position,
            radiusNm,
            radiusMeters: radiusNm * NM_TO_METERS,
          },
        ];
      })
    : [];

  return {
    points,
    routes,
    airspaces,
  };
}

/**
 * Restricts an overlay to a fixed set of route ids (and only the waypoints
 * those routes use). Useful when a scenario's aircraft only exercise a
 * handful of routes out of a shared airspace's wider route network.
 */
export function filterOverlayByRouteIds(
  overlay: ScenarioMapOverlay,
  routeIds: string[],
): ScenarioMapOverlay {
  const routes = overlay.routes.filter((route) => routeIds.includes(route.id));
  const visiblePointIds = new Set(routes.flatMap((route) => route.waypointIds));
  const points = overlay.points.filter((point) => visiblePointIds.has(point.id));
  return { points, routes, airspaces: overlay.airspaces };
}
