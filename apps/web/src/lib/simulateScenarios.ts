// Small static registry of predefined Simulate scenarios. Deliberately not
// backend-driven — the MVP has one working simulation, and a hardcoded list
// matches the existing pattern already used for Learn concepts.

export interface SimulateScenarioDescriptor {
  slug: string;
  title: string;
  description: string;
  airspaceId: string;
  scenarioId: string;
  aircraftCount: number;
  routeCount: number;
  mode: string;
}

export const SIMULATE_SCENARIOS: SimulateScenarioDescriptor[] = [
  {
    slug: "gao-sector-traffic",
    title: "Gao Sector Traffic",
    description:
      "A small en-route traffic simulation with several aircraft entering, crossing, and leaving the sector.",
    airspaceId: "gao_demo",
    scenarioId: "gao_sector_traffic",
    aircraftCount: 4,
    routeCount: 3,
    mode: "Solo",
  },
];

export function getSimulateScenario(slug: string): SimulateScenarioDescriptor | null {
  return SIMULATE_SCENARIOS.find((item) => item.slug === slug) ?? null;
}
