# Aircraft Performance Plan

## Goal

Use aircraft type codes in scenarios and templates, then resolve aircraft behavior from a shared performance database.

Example template aircraft:

```json
{
  "id": "AC901",
  "callsign": "DEP01",
  "aircraft_type": "B737",
  "route_id": "UA612",
  "flight_level": 290,
  "appear_after_seconds": 0
}
```

## Performance Database

Implemented file:

```text
airspacesim/data/aircraft_performance.v1.json
```

Initial aircraft types:

- [x] `B737`
- [x] `B738`
- [x] `A320`
- [x] `A332`
- [x] `B772`
- [x] `E190`
- [x] `CRJ9`
- [x] `AT72`
- [x] `DH8D`
- [x] `C208`

## Profile Sections

Each aircraft type should include:

- [x] identity: name/display name and wake category
- [x] speed: default cruise speed, min clean speed, max operating speed
- [x] vertical: climb/descent rates and max climb/descent rates
- [x] turning: turn rate, bank angle, minimum turn radius
- [x] holding: holding speed and leg timing
- [x] navigation: waypoint capture radius and route intercept behavior
- [x] limits: max FL
- [x] limits: min/max speed and max altitude guardrails in runtime behavior

Example shape:

```json
{
  "B737": {
    "name": "Boeing 737",
    "wake_category": "M",
    "engine_type": "jet",
    "speed": {
      "default_cruise_kt": 450,
      "holding_kt": 230,
      "acceleration_kt_per_sec": 1.5,
      "deceleration_kt_per_sec": 2.0
    },
    "vertical": {
      "default_climb_fpm": 1800,
      "default_descent_fpm": 2000,
      "service_ceiling_fl": 410
    },
    "turning": {
      "standard_rate_deg_per_sec": 3.0,
      "default_bank_deg": 25,
      "max_bank_deg": 30,
      "min_turn_radius_nm": 2.5
    }
  }
}
```

## Commands To Support Later

- [x] `SET_SPEED`
- [x] `SET_FL`
- [x] `ASSIGN_HEADING`
- [x] `ASSIGN_RADIAL`
- [x] `ASSIGN_RADIAL_DEVIATION` legacy offset helper
- [x] `INTERCEPT_ROUTE`
- [x] `DIRECT_TO`
- [x] `RESUME_ROUTE`
- [x] `HOLD_AT_FIX`
- [x] `EXIT_HOLD`
- [x] `REROUTE`

## Lateral Control Modes

Heading and radial deviation must be modeled separately.

- [x] Heading mode: aircraft turns to an assigned heading and continues on that heading until another instruction changes the lateral mode.
- [x] Radial intercept mode: aircraft turns to intercept the assigned radial line, for example `R265`.
- [x] Radial tracking mode: after capture, aircraft tracks along the assigned radial instead of continuing on the intercept heading.
- [x] Route intercept mode: aircraft turns back toward the active route after `RESUME_ROUTE`.
- [x] Direct-to mode: aircraft proceeds directly to a named waypoint/fix, then continues through the route sequence from that point when applicable.
- [x] Hold mode: aircraft flies a protected holding pattern at a fix using type-specific holding speed and turn behavior.

Operational distinction:

- A heading is a vector. If the controller does not give another instruction, the aircraft keeps drifting away from the route.
- A radial assignment is route-aware. It should represent a controlled offset/intercept used for separation or weather avoidance, with the expectation that the aircraft can return to the route.
- Aircraft may have the same heading while belonging to different routes.
- Aircraft on the same route/radial should share the same radial line or route geometry.

Radial deviation behavior should support:

- [x] assigned deviation angle, for example `15° left of route` or `15° right of route`
- [x] assigned radial or bearing from a fix/VOR, for example GAO radial
- [x] intercept angle to assigned radial
- [x] radial capture tolerance in NM
- [x] route capture tolerance in NM
- [x] automatic switch from radial intercept to radial tracking after radial capture
- [x] automatic switch back to route mode after route capture
- [x] UI display of lateral state, for example `R265`, `Route Intercept`, or `On route`

## Implementation Phases

1. [x] Add aircraft performance database JSON.
2. [x] Add `aircraft_type` to templates and seeded aircraft.
3. [x] Validate template aircraft types against the database.
4. [x] Store and return aircraft type in runtime state.
5. [x] Show aircraft type in the selected aircraft panel.
6. [x] Use vertical performance for dynamic climb/descent to assigned FL.
7. [x] Use turning performance for assigned headings.
8. [x] Use route/radial performance for radial deviation and route intercept.
9. [x] Use holding performance for hold procedures.

## Current Status

The first implementation slice is complete:

- [x] templates and seeded aircraft carry `aircraft_type`
- [x] live state returns aircraft type and target FL
- [x] selected aircraft panel shows type, vertical mode, rate, and target level
- [x] map labels show current FL with climb/descent trend, for example `DEP01 | FL318 ↑ FL350`
- [x] `SET_FL` now sets a target level and uses the aircraft type profile to climb or descend dynamically

Remaining work is focused on route rejoin behavior and procedural holds.

- [x] assigned headings
- [x] turn-rate handling
- [x] radius-aware turn geometry refinement
- [x] radial deviation behavior
- [x] route intercept behavior, initial active-route-target behavior
- [x] direct-to behavior
- [x] resume-route behavior
- [x] hold-at-fix behavior
- [x] exit-hold behavior
