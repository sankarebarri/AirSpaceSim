# AirSpaceSim Run Workspace UX Spec

This document consolidates the former UI/UX planning files:

- `ui_ux_project_brief.md`
- `ui_ux_run_workspace_spec.md`
- `ui_ux_design.md`

It is the single UX reference for the hosted AirSpaceSim run workspace.

## Status

- [x] Approved as the active hosted UI direction
- [x] Mapped into implementation tasks
- [x] Reflected in the frontend roadmap
- [x] Desktop cockpit layout implemented
- [x] Command history implemented
- [x] Route/fix inspection implemented
- [x] Map measurement tool implemented
- [ ] Tablet/mobile responsive refinement
- [ ] Future event log
- [ ] Future timeline/playback controls

## Product Summary

AirSpaceSim is a simulation and visualization product for aircraft movement in structured airspace.

It supports:

- loading airspace and scenario data
- creating simulation runs
- launching, pausing, resuming, and stopping runs
- observing live aircraft movement
- inspecting routes, waypoints, sectors, and aircraft status
- injecting aircraft dynamically
- changing aircraft speed, flight level, heading, radial, direct-to, and hold behavior
- changing the overall simulation speed
- filtering and inspecting traffic in real time
- exporting trajectory data

The product has two compatible forms:

- a Python simulation package for technical users
- a hosted FastAPI + React web application for interactive use

For UI/UX work, the hosted web app is the primary surface.

## Product Position

AirSpaceSim is not a generic analytics dashboard.

It is closer to:

- a simulation control deck
- a traffic monitoring console
- a scenario exploration tool
- an ATC training workspace

The most important behavior is live spatial understanding:

- where aircraft are
- how they are moving
- how they relate to routes and airspace
- what actions the operator can take next

The run workspace should feel like an operational simulation console, not a long form, report page, or generic card dashboard.

## What The Product Is Not

AirSpaceSim is not:

- a certified air traffic management system
- a safety-critical operational tool
- a public travel map
- a generic BI dashboard
- a casual toy map

It is a simulation-first tool for learning, experimentation, monitoring, operator testing, and demonstration.

## Core User Problem

The user needs to understand a live traffic situation quickly and act without losing spatial context.

The interface must support:

- continuous visual awareness
- fast aircraft selection
- immediate access to high-value controls
- rapid understanding of run status and stream health
- low-friction switching between monitoring and action

## Primary Use Cases

### Run A Live Simulation

The user creates a run, launches it, and watches aircraft move through structured airspace.

### Inspect And Manage Traffic

The user selects aircraft, reviews route and movement details, and tracks active, inbound, outbound, overflight, holding, or finished traffic.

### Inject And Modify Traffic

The user adds aircraft during a run and changes aircraft speed, flight level, heading, radial, direct-to, hold behavior, or simulation speed.

### Explore Scenario Structure

The user understands what routes, waypoints, and sectors exist before or during simulation.

### Export Data

The user exports trajectory data for analysis, testing, or downstream workflows.

## Primary Users

### Simulation Engineer

Wants to:

- run controlled scenarios
- observe behavior
- validate that traffic and routes behave as expected

### Research Or Testing User

Wants to:

- create repeatable conditions
- inspect outputs
- compare behavior across runs later

### Operator, Demo User, Or Student

Wants to:

- understand live state quickly
- interact with traffic intuitively
- use the product without reading technical documentation first
- practice ATC-style actions in a training environment

## Core Domain Concepts

### Scenario

A simulation setup:

- airspace structure
- routes
- points/waypoints
- optional starting aircraft seed data

### Run

One simulation session.

Possible states:

- draft
- running
- paused
- stopped
- completed

### Aircraft

Each aircraft has:

- ID
- callsign
- aircraft type
- route
- position
- speed
- flight level
- vertical mode and rate
- heading
- lateral mode
- traffic flow
- runtime state

### Route

An ordered path through waypoints.

### Waypoint / Point

A named navigation point used to build routes.

### Airspace / Sector

A spatial boundary or region that gives context for aircraft movement.

### Simulation Rate

How fast the simulation advances relative to real time.

### Command

An operator action, such as:

- add aircraft
- set speed
- set flight level
- assign heading
- assign radial
- direct to fix
- hold at fix
- resume navigation
- set simulation speed

### Telemetry / Freshness / Stream Health

Signals that show whether the visible state is current and whether the live session is healthy.

## Current Hosted App Structure

The hosted app has these main areas:

- Overview
- Scenarios
- Runs
- Run Workspace

The run workspace is the most important screen.

It combines:

- live map/simulation surface
- run status and lifecycle controls
- selected-aircraft details
- operator controls
- traffic filters
- traffic roster
- telemetry and command feedback

## Design Position

The run workspace follows an operations cockpit layout:

- compact command strip at the top
- traffic rail on the left
- dominant simulation surface in the center
- operator rail on the right
- supporting dock at the bottom

This structure is now the hosted desktop default.

## Product Rule

The run workspace must answer these questions within a few seconds:

- what is happening right now
- which aircraft is selected
- where it is
- what route it is on
- what can be done to it
- whether the run is healthy and live
- what changed after the last action

If the screen does not answer those quickly, the UI is failing.

## Desired Product Feel

The ideal product should feel:

- focused
- spatial
- immediate
- operational
- legible under motion
- dense, but not cluttered

It should not feel like:

- a report page
- a form-heavy admin tool
- a dashboard with many equal-weight cards

## Target Desktop Layout

```text
[ Top strip: run name | run status | stream health | sim rate | pause/resume | stop | export ]

[ Left traffic rail ][ Main map / simulation surface                  ][ Right operator rail ]
[ Left traffic rail ][ Main map / simulation surface                  ][ Right operator rail ]
[ Left traffic rail ][ Main map / simulation surface                  ][ Right operator rail ]

[ Bottom dock: filters | roster | command result | compact telemetry ]
```

Recommended desktop proportion:

- left rail: about `18%`
- map: about `56%`
- right rail: about `26%`

Recommended bottom dock height:

- `16%` to `22%` of viewport

Recommended top strip:

- one compact row

## Region Ownership

### Top Strip

Purpose:

- global run awareness
- global run actions

Contains:

- run name
- run status
- runtime status
- stream/connection state
- current simulation rate
- start / pause / resume / stop
- export CSV

Should not contain:

- large paragraph text
- large summary cards
- oversized pills
- secondary telemetry blocks
- add-aircraft shortcut unless a workflow proves it is needed
- quick search, because search belongs near the traffic roster

### Left Traffic Rail

Purpose:

- traffic scanning
- fast selection
- awareness of active traffic

Contains:

- search
- filters
- active aircraft list
- callsign
- route
- key status
- quick values such as FL and speed

Should not contain:

- command forms
- deep aircraft details
- large filter forms

Rule:

This rail is for finding and switching aircraft, not operating them.

### Main Map / Simulation Surface

Purpose:

- live spatial understanding
- route and airspace awareness
- selected-aircraft orientation

Contains:

- moving aircraft
- aircraft labels
- heading vectors
- route overlays
- waypoints
- sector/airspace overlays
- selected-aircraft emphasis
- reset view

Should avoid:

- large diagnostics cards
- verbose explanatory messages
- oversized controls
- on-map freshness badges unless a clear need appears

Rule:

The map is the product center of gravity.

### Right Operator Rail

Purpose:

- act on the selected aircraft
- see the minimum information required to act safely

Contains:

- selected aircraft identity
- type, route, status, and flow
- current speed
- current FL and trend
- heading and assigned heading
- lateral mode, radial, direct-to, hold state
- NRV DME
- position
- label position controls
- speed assignment
- flight level assignment
- heading assignment
- radial assignment
- direct-to
- hold / exit hold
- resume navigation
- add aircraft
- last command result
- error and recovery messaging

Should not contain:

- broad traffic browsing tools
- large passive telemetry panels

Rule:

This rail is contextual and action-first.

### Bottom Dock

Purpose:

- support browsing and filtering without competing with the map

Contains:

- roster support
- filters
- search results
- compact telemetry where useful

Future:

- event log
- timeline / playback controls

Rule:

This area is subordinate and should feel docked, not stacked.

## Information Hierarchy

Priority order:

1. map and selected aircraft
2. global run state and actions
3. selected-aircraft commands
4. traffic scanning and filters
5. telemetry and diagnostics

If two areas compete visually, the lower-priority area should be reduced.

## Map Rules

- [x] The map must occupy the largest share of the screen.
- [x] The map must feel like the central workspace, not a card.
- [x] Overlays must stay small and corner-anchored.
- [x] Selected aircraft must remain obvious.
- [x] The fallback state must look deliberate and secondary to the real map.
- [x] The map must not lose too much area to non-spatial UI.

If the real map engine is unavailable:

- show a compact fallback badge
- preserve traffic orientation if possible
- do not cover the center of the map with explanation text

## Interaction Rules

- [x] Selecting an aircraft in the rail updates the map and operator rail.
- [x] Selecting an aircraft on the map updates the operator rail.
- [x] Filters affect both the map and traffic rail.
- [x] Global run actions stay visible while browsing traffic.
- [x] Command feedback appears near the command area.
- [x] Side panels and bottom panels scroll internally.
- [x] The page itself stays stable during normal desktop operation.

## Visual Direction

Use:

- dark console base with strong contrast
- clear typography hierarchy
- restrained accent colors
- compact, precise spacing
- subtle grid/radar references only when they support the map

Avoid:

- decorative cyberpunk styling
- glow-heavy neon treatment
- thin unreadable text
- multiple bright accent colors fighting each other
- heavy panel ornamentation

## Color Logic

Use color semantically:

- green: healthy/live/open/running
- amber: caution/paused/waiting
- red: stop/error/destructive
- blue: selected/focused/navigation context
- neutral: passive labels and chrome

Dangerous actions such as `Stop` must be visually separated from normal actions.

## Typography Rules

- Primary values must be readable at a glance.
- Secondary labels should be short and muted.
- Avoid all-caps for large blocks of content.
- Use uppercase sparingly for compact labels or section tags only.
- Numeric readouts such as speed and FL should be highly legible.

## Responsive Strategy

Desktop is the primary rich experience.

Tablet and mobile remain future refinement work:

- [ ] Preserve map-first layout on tablet.
- [ ] Collapse the bottom dock when space is limited.
- [ ] Keep the right panel available as a tabbed or collapsible region.
- [ ] Prioritize map and selected aircraft on mobile.
- [ ] Move operator controls into drawers or sheets on mobile.
- [ ] Show roster and filters as switchable panels on mobile.
- [ ] Keep global run controls accessible without deep scrolling.

## Important States

The UI must clearly handle:

- no run selected
- draft run
- running run
- paused run
- stopped run
- completed run
- stale data
- broken stream / degraded live connection
- empty traffic
- filtered-empty traffic
- fallback map mode

## Completed UX Checklist

- [x] Approved cockpit layout direction.
- [x] Compact top command strip.
- [x] Large center map.
- [x] Left traffic rail.
- [x] Right operator rail.
- [x] Bottom support dock.
- [x] Darker console-like visual tone.
- [x] Reduced document-style page stacking.
- [x] Global run controls at the top.
- [x] Selected-aircraft controls near selected-aircraft details.
- [x] Roster and filters near each other.
- [x] Map remains visible during normal desktop operation.
- [x] Aircraft selection updates the right panel immediately.
- [x] Aircraft selection is visible on the map.
- [x] Stream state is visible without logs.
- [x] Error and command feedback are visible.
- [x] Recent command history is visible near operator actions.
- [x] Fixes and routes can be inspected from the map.
- [x] Aircraft/fix distance can be measured with the map ruler.
- [x] Page feels operational, not decorative.

## Future UX Work

- [ ] Refine responsive behavior for tablet and mobile.
- [ ] Add event log only when command history/debrief requires it.
- [ ] Add timeline/playback controls only when replay becomes a real workflow.
- [ ] Tighten specific visual details after usability issues are identified.

## Deferred To Avoid Bloat

Do not add these unless a clear workflow proves value:

- top-bar add-aircraft shortcut
- top-bar quick search
- on-map freshness/live badge
- decorative visual polish without a specific usability target
- analytics-style cards competing with the map
- high-density telemetry panels before a training workflow needs them

## Design Questions For Future Work

Before adding a UI feature, ask:

- Does it help the user understand live traffic?
- Does it help the user act on selected traffic?
- Does it keep the map central?
- Does it reduce hunting or uncertainty?
- Does it belong in this workspace, or in a lesson/debrief/instructor area?
- Is it needed now, or can it wait until a real training workflow requires it?

## Glossary

### Hosted App

The web-based FastAPI + React version of AirSpaceSim.

### Simulation Surface

The live map area where aircraft, routes, and airspace are visualized.

### Operator Rail

The side panel that holds contextual controls and selected-aircraft details.

### Bottom Dock

The lower panel used for browsing tools such as filters and traffic roster.

### Freshness

How current the visible state is.

### Stream Health

Whether the live connection is open and successfully updating.

### Roster

The list of visible aircraft in the current run.

## Bottom Line

AirSpaceSim is a live aircraft simulation workspace.

Its most important UX requirement is to let a user understand live traffic and act on it without losing spatial context.

The design should treat the map as the core product surface and organize everything else around it.
