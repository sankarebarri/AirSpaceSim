# Sahel Control Airspace

This is the default AirSpaceSim public training airspace package.

It is a fictional medium-complexity en-route sector that uses the same
`airspacesim.scenario_airspace` payload shape that the hosted API already
accepts, so it can be loaded directly by `scripts/seed_hosted_demo.py`.

Package files:

- `package.v1.json`: package manifest for frontend/API discovery later
- `airspace.v1.json`: points, routes, and airspace boundary data
- `scenarios/mixed_traffic_demo.v1.json`: default 25-aircraft training session

Validate the package:

```bash
python3 scripts/validate_airspace_package.py airspaces/gao_demo
```

Run with this package explicitly:

```bash
python3 scripts/seed_hosted_demo.py \
  --airspace airspaces/gao_demo/airspace.v1.json \
  --template airspaces/gao_demo/scenarios/mixed_traffic_demo.v1.json \
  --web-base-url http://127.0.0.1:5174
```
