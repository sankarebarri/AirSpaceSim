# Glossary

- `Airspace`: Controlled geometric area in the scenario (e.g., circle with center/radius).
- `Waypoint`: Named navigation point with geographic coordinates.
- `Route`: Ordered waypoint sequence identified by route id/name.
- `Flight Plan`: Departure/destination plus route chain used to resolve full waypoint path.
- `Track`: Current aircraft trajectory/state row in `trajectory.v0.1`.
- `Scenario`: Input contract defining airspace context and initial aircraft.
- `Aircraft State`: Runtime snapshot contract focused on current aircraft positions/status.
- `Events`: Idempotent command stream (`ADD_AIRCRAFT`, `SET_SPEED`, etc.).
- `Ingestion Adapter`: Source reader exposing `poll()` and optional `ack()`.
- `Envelope`: Standard JSON wrapper (`schema`, `metadata`, `data`) for contracts.

## Phrase Conventions

- Use explicit units in names: `_kt`, `_ft`, `_fpm`, `_nm`, `_dd`.
- Use `schema.name` + `schema.version` for compatibility decisions.
- Use `canonical` for preferred contracts and `legacy` for compatibility shims only.
- Use `snapshot` for full-state files and `events` for incremental commands.
