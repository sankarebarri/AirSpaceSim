# Interoperability Example

## Goal
Export canonical trajectory output to a CSV file for downstream analytics/audit workflows.

## Inputs
- `data/trajectory.v0.1.json` (produced by simulation runtime)

## Output
- `data/trajectory_export.csv`

## Run

1. Produce trajectory data:
```bash
python3 examples/example_simulation.py --max-wait 5
```

2. Export to CSV:
```bash
python3 examples/interoperability_export.py
```

## CSV columns
- `id`
- `callsign`
- `route_id`
- `status`
- `speed_kt`
- `altitude_ft`
- `vertical_rate_fpm`
- `position_lat`
- `position_lon`
- `updated_utc`
