# Post-Performance Phase Improvement Plan

This file tracks the next simulator improvements after completing the aircraft performance phase.

## Goal

Make AirSpaceSim better as an ATC learning tool, not only a movement simulator.

## Recommended Order

1. [x] Command feedback and rejection messages
   - Show clear UI messages when a command is rejected.
   - Example: `C208 cannot climb above FL250`.
   - Example: `Speed 300 kt exceeds C208 training limit`.
   - Show accepted commands in green.
   - Show rejected commands in red.
   - Show skipped commands in neutral/amber.
   - Keep a small command history, ideally the last 5-10 commands.
   - Include callsign or aircraft ID, command type, timestamp, and result.
   - Make backend rejection reasons more user-friendly when possible.
   - Update `docs/user/how_to_use_app.md` after this is implemented.

   Implementation checklist:

   - [x] Use backend command result messages for performance-limit rejections.
   - [x] Add helper formatting for command result text in the web app.
   - [x] Replace the single latest-command monitor with a compact command history.
   - [x] Add clear success/rejected/skipped visual states.
   - [x] Add tests for command history display.
   - [x] Update user documentation.

2. [x] Separation learning tools
   - Add an optional ruler tool.
   - Let students measure distance between two aircraft.
   - Let students measure distance from a fix or VOR.
   - Keep automatic conflict detection for a later phase.

3. [ ] Better hold behavior
   - Replace the current simplified hold with a racetrack hold.
   - Include inbound course, outbound leg time, left/right turns, and fix capture.

4. [x] Route and fix inspection
   - Click a route or fix to show details.
   - Show fix name, route membership, radial, and distance from GAO VOR.
   - Help students understand radial and route structure.

5. [ ] Scenario authoring improvements
   - [x] Improve template validation.
   - [x] Detect duplicate callsigns.
   - [x] Detect unknown routes.
   - [x] Detect invalid aircraft types.
   - [x] Detect speed or FL values outside aircraft performance limits.
   - [x] Add `--validate-only` for checking templates without creating a run.
   - [x] Validate the built-in demo plan before API calls.
   - [x] Add multi-airspace template validation from `multi_airspace_custom_airspace_design.md`.
   - Add beginner, mixed traffic, and high workload templates.

6. [ ] Instructor controls
   - Improve traffic injection controls.
   - Add run reset or aircraft reset behavior.
   - Add label visibility controls for busy scenarios.
   - Defer save/load run state until session recovery and debrief needs are clearer.

7. [ ] Training documentation
   - Keep updating `docs/user/how_to_use_app.md`.
   - Add example exercises:
     - assign heading
     - intercept radial
     - resume normal navigation
     - direct to a fix
     - hold at a fix

8. [x] Lesson-to-simulator launch
   - [x] Add a frontend `Open Live Simulator Practice` button when the backend can create practice runs from lesson IDs.
   - [x] The button should launch the correct airspace and scenario template without asking end users to run `scripts/seed_hosted_demo.py`.
   - [x] Keep lesson practice useful without the backend, then offer live traffic practice as an optional next step.

## Next Immediate Task

Add full custom-airspace authoring documentation before better hold behavior.

Reason: command-line multi-airspace support and a fictional `training_alpha` package are now in place. The next step is documenting how a user creates their own package before we attach hold procedures to airspace packages.
