# How To Use The AirSpaceSim Simulation

This guide is for the simulation user. It explains what the controls do and how to use the run workspace. It is not a developer setup guide.

For startup commands, use [docs/user/run_simulation.md](/home/sankarebarri/code/aircore/AirSpaceSim/docs/user/run_simulation.md).

## Main Idea

AirSpaceSim lets you watch aircraft move through an airspace and issue basic ATC-style instructions for learning and practice.

You can:

- view live aircraft on the map
- open short lessons from the Lessons page
- select aircraft and inspect details
- assign speed, flight level, heading, radial, direct-to, and hold instructions
- resume normal navigation
- add traffic during a run
- filter traffic by route, status, flow, callsign, or aircraft ID

## Lessons

Open `Lessons` from the top navigation.

The `Heading Versus Radial` lesson can be used without starting the API or creating a simulation run.

Use the practice panel to:

- compare `H265` against `R265` for 10 seconds
- watch one aircraft drift on heading
- watch another aircraft intercept and follow the radial
- run `Resume Normal Navigation` for 10 seconds
- see both aircraft return to `Route Alpha / R250`

## Opening A Simulation

After the API and web app are running, open the run URL created by the seed script.

Example:

```text
http://127.0.0.1:5174/runs/<run-id>
```

The main screen is the run workspace.

## Map Basics

The map shows:

- aircraft dots
- aircraft labels, usually `CALLSIGN | FL`
- heading vectors showing where each aircraft is facing
- route lines
- fixes and navaids
- the airspace boundary

Click an aircraft dot to select it. If clicking the dot is difficult, use the traffic list on the left.

Use `Reset View` to return the map to the default airspace view.

## Inspect Routes And Fixes

Click a route line or fix on the map to inspect it in the right panel.

Fix inspection shows:

- fix name
- fix type
- radial from GAO VOR
- route membership
- position
- distance from GAO VOR

Route inspection shows:

- route ID
- number of fixes
- fix sequence

## Measure Distance

Use `Measure` in the right panel.

1. Click `Measure`.
2. Click two aircraft, two fixes, or one aircraft and one fix.
3. Read the distance in NM in the measurement card.
4. Click `Clear measurement` to start again.

This is a learning ruler. It helps students estimate separation manually; it does not automatically decide whether separation is valid.

## Aircraft Colors

Aircraft are color coded by traffic flow:

- green: departures / outbound traffic
- red: arrivals / inbound traffic
- brown: overflights / transit traffic

## Selecting Aircraft

Select an aircraft by:

- clicking it on the map
- clicking it in the traffic list

The selected aircraft panel shows:

- aircraft type
- route
- traffic flow
- current flight level
- vertical mode and rate
- speed
- heading
- lateral mode
- GAO DME
- position

## Moving Labels

If labels overlap, select the aircraft and use the label controls:

- Left
- Right
- Top
- Bottom

This only moves that selected aircraft label.

## Assign Speed

Use `Speed`.

1. Select an aircraft.
2. Enter the assigned speed.
3. Click `Assign Speed`.

The aircraft speed updates after the command is applied.

Speed commands must stay within that aircraft type's training performance range.
If the value is outside the range, the command is rejected in Command History.

## Assign Flight Level

Use `Flight Level`.

1. Select an aircraft.
2. Enter the assigned FL.
3. Click `Climb`, `Descend`, or `Maintain`.

The aircraft changes level dynamically based on its aircraft type performance. The label may show a trend like:

```text
DEP01 | FL318 ↑ FL350
```

Flight level commands must stay at or below that aircraft type's maximum FL.

## Assign Heading

Use `Heading`.

1. Select an aircraft.
2. Enter heading degrees, for example `090`.
3. Click `Turn Heading`.

The aircraft turns gradually to that heading and keeps flying that heading until another instruction is given.

Heading is a vector instruction. If you leave the aircraft on a heading, it can keep drifting away from its route.

## Assign Radial

Use `Radial`.

1. Select an aircraft.
2. Enter the radial, for example `265`.
3. Click `Intercept Radial`.

The aircraft turns to intercept the assigned radial. Once it captures the radial line, it tracks along that radial instead of continuing on the intercept heading.

You can assign another radial later, for example `R265` then `R270`.

## Resume Normal Navigation

Use `Resume Nav`.

This tells the aircraft to leave heading/radial/direct/hold behavior and return toward its assigned route.

Important: resume navigation returns to the aircraft route, not to the last assigned radial.

## Direct To

Use `Direct To`.

1. Select an aircraft.
2. Enter a fix ID on its route, for example `GAO_VOR`.
3. Click `Direct To`.

The aircraft proceeds directly to that fix and then continues the route sequence from there.

## Hold

Use `Hold`.

1. Select an aircraft.
2. Enter a hold fix ID on its route.
3. Click `Hold`.

The aircraft proceeds to the fix, slows to its holding speed, and enters hold mode.

Use `Exit Hold` to leave the hold and resume route intercept.

## Add Traffic

Use `Add Traffic`.

Enter:

- aircraft ID
- callsign
- aircraft type
- route ID
- speed
- flight level

Then click `Add Track`.

Aircraft type examples:

- `B737`
- `A320`
- `B738`
- `E190`
- `CRJ9`

## Traffic List And Filters

The traffic list helps you select aircraft when the map is busy.

Use filters for:

- route
- status
- traffic flow
- search text

Search can match:

- aircraft ID
- callsign
- route ID

Use `Clear` to reset filters.

## Run Controls

The top run controls include:

- launch/start
- pause
- resume
- stop
- simulation rate

Simulation rate changes how fast the simulation runs.

Examples:

- `1.0x`: normal speed
- `2.0x`: twice as fast

## Command History

Command History shows recent operator actions.

Each entry shows:

- command action
- aircraft callsign or ID
- command time
- applied, rejected, or skipped status
- rejection reason when available

Use it to confirm that an instruction was accepted or understand why it was not applied.

## What To Watch

During a session, watch:

- aircraft labels and FL changes
- heading vectors
- lateral mode
- GAO DME
- radial cross-track value
- Command History
- connection status

## Current Limits

This is a training simulator under active development.

Current limits:

- not certified for operational ATC use
- hold behavior is simplified
- turn behavior uses aircraft type turn-rate and minimum-radius limits, but procedures are still simplified
- some procedures are still approximations

## Living Document

This file should be updated whenever a new user-facing simulator feature is added or changed.
