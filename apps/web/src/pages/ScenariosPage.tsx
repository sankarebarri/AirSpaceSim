import { useQuery } from "@tanstack/react-query";

import { AppFrame } from "../components/AppFrame";
import { listScenarios } from "../lib/api";
import { describeError, formatTimestamp } from "../lib/format";

function countCollection(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

export function ScenariosPage() {
  const scenariosQuery = useQuery({
    queryKey: ["scenarios"],
    queryFn: listScenarios,
  });

  const scenarios = scenariosQuery.data?.items ?? [];

  return (
    <AppFrame>
      <section className="hero-card">
        <p className="eyebrow">Scenarios</p>
        <h1>Scenario Library</h1>
        <p className="hero-copy">
          Review the saved traffic plans available for live simulator sessions.
        </p>
      </section>

      {scenariosQuery.isError ? (
        <section className="content-card">
          <p className="error-panel">{describeError(scenariosQuery.error)}</p>
        </section>
      ) : scenariosQuery.isPending ? (
        <section className="content-card">
          <p className="empty-state">Loading scenario inventory…</p>
        </section>
      ) : scenarios.length === 0 ? (
        <section className="content-card">
          <p className="empty-state">
            No scenarios are stored yet. The backend can still fall back to the
            packaged default contracts when a run starts without one.
          </p>
        </section>
      ) : (
        <section className="card-grid">
          {scenarios.map((scenario) => {
            const airspaceEnvelope = scenario.airspace_payload as Record<string, unknown>;
            const aircraftEnvelope = scenario.aircraft_payload as Record<string, unknown>;
            const airspaceData = (airspaceEnvelope["data"] ??
              {}) as Record<string, unknown>;
            const aircraftData = (aircraftEnvelope["data"] ??
              {}) as Record<string, unknown>;
            const routeCount = countCollection(airspaceData.routes);
            const pointCount = countCollection(airspaceData.points);
            const aircraftCount = countCollection(aircraftData.aircraft);

            return (
              <article key={scenario.id} className="content-card scenario-card">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Scenario</p>
                    <h2>{scenario.name}</h2>
                  </div>
                  <span className="status-pill">{scenario.slug}</span>
                </div>
                <p className="card-copy">
                  {scenario.description ?? "No description provided."}
                </p>
                <div className="table-list">
                  <div className="data-pair">
                    <span>Routes</span>
                    <strong>{routeCount}</strong>
                  </div>
                  <div className="data-pair">
                    <span>Points</span>
                    <strong>{pointCount}</strong>
                  </div>
                  <div className="data-pair">
                    <span>Training aircraft</span>
                    <strong>{aircraftCount}</strong>
                  </div>
                  <div className="data-pair">
                    <span>Updated</span>
                    <strong>{formatTimestamp(scenario.updated_at)}</strong>
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </AppFrame>
  );
}
