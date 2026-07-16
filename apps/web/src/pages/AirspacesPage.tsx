import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { AppFrame } from "../components/AppFrame";
import { listAirspaces } from "../lib/api";
import { formatLabel } from "../lib/format";
import type { AirspacePackageSummary } from "../types/api";

function defaultScenarioPath(airspace: AirspacePackageSummary): string | null {
  const defaultScenario = airspace.scenarios.find(
    (scenario) => scenario.id === airspace.default_scenario,
  );
  return defaultScenario?.path ?? airspace.scenarios[0]?.path ?? null;
}

export function AirspacesPage() {
  const airspacesQuery = useQuery({
    queryKey: ["airspaces"],
    queryFn: listAirspaces,
  });
  const airspaces = airspacesQuery.data?.items ?? [];

  return (
    <AppFrame pageClassName="catalog-page-shell">
      <section className="catalog-hero">
        <div>
          <p className="eyebrow">Airspaces</p>
          <h1>Select the training environment before loading traffic.</h1>
          <p>
            Airspaces define fixes, routes, boundaries, scenarios, and lessons.
            The list is read from package manifests so custom airspaces can use
            the same structure.
          </p>
        </div>
        <div className="catalog-hero-actions">
          <Link to="/runs" className="button-primary">
            Open Simulation
          </Link>
          <Link to="/lessons" className="button-secondary">
            Browse Lessons
          </Link>
        </div>
      </section>

      {airspacesQuery.isError ? (
        <section className="content-card">
          <p className="error-panel">Could not load airspace packages.</p>
        </section>
      ) : null}

      <section className="catalog-grid catalog-grid-two">
        {airspacesQuery.isPending ? (
          <article className="catalog-card">
            <p className="eyebrow">Loading</p>
            <h2>Reading airspace packages...</h2>
          </article>
        ) : null}

        {!airspacesQuery.isPending && airspaces.length === 0 ? (
          <article className="catalog-card">
            <p className="eyebrow">No Packages</p>
            <h2>No airspace package manifests were found.</h2>
            <p>Add `package.v1.json` under `airspaces/&lt;airspace_id&gt;/`.</p>
          </article>
        ) : null}

        {airspaces.map((airspace) => (
          <article className="catalog-card airspace-card" key={airspace.id}>
            <div className="catalog-card-header">
              <div>
                <p className="eyebrow">{airspace.id}</p>
                <h2>{airspace.name}</h2>
              </div>
              <span className="status-pill status-running">
                {formatLabel(airspace.package_type)}
              </span>
            </div>
            <p>{airspace.description}</p>
            <div className="catalog-facts">
              <div>
                <span>Service</span>
                <strong>{airspace.service_types.map(formatLabel).join(", ")}</strong>
              </div>
              <div>
                <span>Difficulty</span>
                <strong>{formatLabel(airspace.difficulty)}</strong>
              </div>
              <div>
                <span>Scenarios</span>
                <strong>{airspace.scenarios.length}</strong>
              </div>
              <div>
                <span>Lessons</span>
                <strong>{airspace.lessons.length}</strong>
              </div>
            </div>
            <div className="catalog-actions">
              <Link to="/runs" className="button-primary button-compact">
                Open Simulator
              </Link>
              {defaultScenarioPath(airspace) ? (
                <span className="catalog-note">Includes a ready-to-run training scenario</span>
              ) : (
                <span className="catalog-note">Custom traffic can be loaded through the API</span>
              )}
            </div>
          </article>
        ))}
      </section>
    </AppFrame>
  );
}
