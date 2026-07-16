// Separation minima and live-distance helpers for the Learn experience. The
// Learn lesson intentionally teaches the applicable separation minimum
// rather than a CPA-style prediction — this stays a small, honest wrapper
// around real observed positions.

export const REQUIRED_HORIZONTAL_SEPARATION_NM = 10;
export const REQUIRED_VERTICAL_SEPARATION_FT = 1000;

function toRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

function localOffsetNm(
  origin: [number, number],
  point: [number, number],
): { east: number; north: number } {
  const [originLat, originLon] = origin;
  const [lat, lon] = point;
  return {
    north: (lat - originLat) * 60,
    east: (lon - originLon) * 60 * Math.cos(toRadians(originLat)),
  };
}

export function distanceNm(from: [number, number], to: [number, number]): number {
  const offset = localOffsetNm(from, to);
  return Math.hypot(offset.east, offset.north);
}

/**
 * Whether a pair of aircraft is validly separated: either the horizontal
 * minimum or the vertical minimum being satisfied is sufficient — separation
 * is never judged on horizontal distance alone. Shared by Practice's
 * scenario-specific evaluation and Simulate's general monitoring so both
 * apply the exact same definition of "separated".
 */
export function isSeparated(
  horizontalNm: number,
  verticalFt: number,
  requiredHorizontalNm: number,
  requiredVerticalFt: number,
): boolean {
  return horizontalNm >= requiredHorizontalNm || verticalFt >= requiredVerticalFt;
}
