# Multi-Airspace And Custom Airspace Design

This file captures the direction for supporting multiple real, adapted, and fictional training airspaces in AirSpaceSim.

## Goal

AirSpaceSim should not be tied to one built-in airspace.

Each run should eventually be based on:

```text
airspace package + scenario template + optional lesson/exercise
```

This allows the same simulator to support:

- Gao demo airspace
- other real or adapted airspaces
- fictional classroom airspaces
- simplified beginner airspaces
- service-specific airspaces for apron, aerodrome, approach, en-route, and radar training

## Core Principle

An airspace should be loaded as data, not hardcoded into the simulator.

The simulator should validate the selected airspace, then load routes, fixes, boundaries, holding patterns, and default map settings from that selected package.

## Airspace Package Shape

Recommended folder shape:

```text
airspaces/
  gao_demo/
    package.v1.json
    airspace.v1.json
    scenarios/
    holds.v1.json
    README.md

  training_alpha/
    package.v1.json
    airspace.v1.json
    scenarios/
    lessons/
    holds.v1.json
    README.md
```

Each package should define:

- package manifest
- stable airspace ID
- display name
- source type
- center/default map view
- fixes and navaids
- routes
- airspace boundaries
- sectors or zones
- holding patterns
- optional notes for students/instructors

The manifest file is:

```text
airspaces/<airspace_id>/package.v1.json
```

It lists the package ID, display name, package type, service types, difficulty, training modes, default scenario, scenario files, and lesson files.

## Source Types

Every airspace package should declare its origin.

Examples:

```json
"source_type": "fictional"
```

```json
"source_type": "real_world_adapted"
```

```json
"source_type": "real_world_reference"
```

This prevents confusion between training data and operational data.

## Geometry Types

Airspaces are not all circular. The data model should support multiple boundary shapes.

### Circle

Useful for simple TMA or beginner training areas.

```json
{
  "id": "GAO_TMA_85",
  "name": "Gao TMA 85 NM",
  "type": "circle",
  "center_point_id": "GAO_VOR",
  "radius_nm": 85
}
```

### Polygon

Useful for fictional or real adapted boundaries.

```json
{
  "id": "ALPHA_TMA",
  "name": "Alpha TMA",
  "type": "polygon",
  "points": [
    [16.8, -1.2],
    [17.4, 0.1],
    [16.6, 1.0],
    [15.4, 0.5],
    [15.2, -0.8]
  ]
}
```

### Sector Or Arc

Useful later for real ATS boundaries.

```json
{
  "id": "ABC_SECTOR_WEST",
  "name": "ABC West Sector",
  "type": "sector",
  "center_point_id": "ABC_VOR",
  "inner_radius_nm": 20,
  "outer_radius_nm": 85,
  "start_radial": 240,
  "end_radial": 30
}
```

Recommended implementation order:

1. [x] Circle
2. [x] Polygon validation
3. [ ] Sector/arc rendering and validation

## Example Fictional Airspace

```json
{
  "schema": {
    "name": "airspacesim.airspace_package",
    "version": "1.0"
  },
  "metadata": {
    "id": "training_alpha",
    "name": "Training Alpha Airspace",
    "source_type": "fictional",
    "country": "Training",
    "notes": "Fictional airspace for beginner procedural training."
  },
  "map": {
    "default_center": [16.25, -0.03],
    "default_zoom_nm": 85
  },
  "points": [
    {
      "id": "ALP_VOR",
      "name": "Alpha VOR",
      "type": "navaid",
      "position": [16.25, -0.03]
    },
    {
      "id": "FIX01",
      "name": "FIX01",
      "type": "fix",
      "position": [16.8, 0.4]
    },
    {
      "id": "FIX02",
      "name": "FIX02",
      "type": "fix",
      "position": [15.9, -0.7]
    }
  ],
  "routes": [
    {
      "id": "A1",
      "name": "Alpha One",
      "waypoint_ids": ["ALP_VOR", "FIX01", "FIX02"]
    }
  ],
  "airspaces": [
    {
      "id": "ALPHA_TMA",
      "name": "Alpha TMA",
      "type": "polygon",
      "points": [
        [16.8, -1.2],
        [17.4, 0.1],
        [16.6, 1.0],
        [15.4, 0.5],
        [15.2, -0.8]
      ]
    }
  ]
}
```

## Scenario Relationship

Scenario templates should declare which airspace they require.

Example:

```json
{
  "airspace_id": "training_alpha",
  "aircraft": [
    {
      "id": "AC901",
      "callsign": "DEP01",
      "aircraft_type": "B737",
      "route_id": "A1",
      "speed_kt": 410,
      "flight_level": 290
    }
  ]
}
```

Validation should check that:

- the declared airspace exists
- every scenario route exists in that airspace
- every route fix exists in that airspace
- every hold fix or hold pattern exists in that airspace
- every aircraft type exists in the aircraft performance database

## Lesson Relationship

Lessons should declare compatible airspaces or compatible airspace families.

Example:

```json
{
  "id": "enroute_heading_vs_radial_intro",
  "compatible_airspaces": ["gao_demo", "training_alpha"],
  "exercise": {
    "scenario_template": "mixed_traffic_demo.v1.json"
  }
}
```

The same lesson concept can later have different exercises for different airspaces.

## Loading Flow

Short-term command-line flow:

```bash
python3 scripts/seed_hosted_demo.py \
  --airspace airspaces/training_alpha/airspace.v1.json \
  --template templates/training_alpha_beginner.v1.json
```

Long-term app flow:

1. Select training service.
2. Select airspace.
3. Select lesson or scenario.
4. Validate the package/template combination.
5. Start the run.

## Custom Airspace Support

Users should be able to add their own airspace package, including a fictional airspace for learning.

Custom airspaces should be accepted if they pass validation. They do not need to represent real-world procedures.

The app should support:

- real-world airspace
- adapted real-world airspace
- fictional training airspace
- simplified classroom airspace

## Validation Rules

An airspace package should fail validation if:

- metadata ID or name is missing
- point IDs are duplicated
- coordinates are invalid
- route IDs are duplicated
- route waypoint IDs do not exist
- a circle boundary has no valid center or radius
- a polygon boundary has fewer than 3 points
- a sector boundary has invalid radius or radial values
- a hold references an unknown fix
- a scenario references routes outside the selected airspace
- a lesson references a missing scenario template

Package validation command:

```bash
python3 scripts/validate_airspace_package.py airspaces/training_alpha
```

## Implementation Checklist

1. [x] Define `airspaces/<airspace_id>/airspace.v1.json` package format.
2. [x] Move Gao demo airspace into an airspace package.
3. [x] Add `--airspace` option to `scripts/seed_hosted_demo.py`.
4. [x] Validate selected scenario templates against the selected airspace.
5. [x] Add polygon boundary rendering to the map.
6. [x] Add a fictional `training_alpha` package for classroom testing.
7. [x] Add run docs for using a custom airspace package.
8. [x] Add `scripts/validate_airspace_package.py`.
9. [x] Add `package.v1.json` manifests for built-in packages.
10. [x] Add an Airspaces page in the web app that lists available package manifests.
11. [ ] Add full docs for creating a custom airspace from scratch.
12. [ ] Later: add package validation and preview actions to the Airspaces page.

## Recommended Starting Point

Command-line support is now available for Gao and Training Alpha.

Next:

- add full custom-airspace authoring documentation
- add sector/arc support when real airspace boundaries require it
- keep the web UI unchanged until the data model is stable
