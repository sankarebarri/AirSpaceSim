Implement the first structured lesson family for AirSpaceSim:

Separation Fundamentals
→ Traffic Relationships

For this task, fully implement only the Traffic Relationships learning journey and its flows.

The other planned lesson groups should appear in the curriculum structure so they are not forgotten, but they must remain unavailable placeholders with no lesson content yet.

Do not implement Vertical Separation or Horizontal Separation lessons in this task.

Reuse the existing AirSpaceSim Learn architecture, simulation engine, scenario system, visual language, multilingual structure, and generic lesson runners wherever possible.

The main goal is to establish a reusable pattern for a concept family that is broader than one conflict-resolution lesson.

# 1. Curriculum structure

Update the Learn curriculum to contain the following initial structure:

Separation Fundamentals

1. Traffic Relationships
   - available
   - fully implemented in this task

2. Vertical Separation
   - planned
   - no content yet

3. Horizontal Separation
   - planned
   - no content yet

Horizontal Separation may show the following future structure as non-interactive metadata or a concise planned-content preview:

- Lateral Separation
- Longitudinal Separation
  - Same Track
  - Reciprocal Track
  - Crossing Track

Do not build pages, simulations, exercises, or scenario files for the planned groups yet.

The unavailable groups should not look broken.

Use a quiet status such as:

Planned

or:

Coming later

Do not add disabled buttons that appear clickable.

# 2. Learn page organisation

The Learn page should remain calm and minimal.

Show the main family:

Separation Fundamentals

Within it, display the three concept groups:

- Traffic Relationships
- Vertical Separation
- Horizontal Separation

Traffic Relationships should be the only available group.

Suggested description:

Understand how aircraft tracks relate to one another before applying separation.

Vertical Separation description:

Learn how aircraft are separated by assigned and occupied levels.

Status:

Planned

Horizontal Separation description:

Explore lateral and longitudinal separation between aircraft.

Status:

Planned

Do not crowd the page with every future lesson title.

The detailed future hierarchy should live in metadata or inside the planned group page only if that page is useful and lightweight.

# 3. Traffic Relationships concept page

When the user opens Traffic Relationships, show a concept overview.

Title:

Traffic Relationships

Description:

Learn how to recognise same-track, reciprocal-track, crossing-track, and unrelated traffic.

The learning journey should be:

1. Understanding Track
2. Same-Track Traffic
3. Reciprocal-Track Traffic
4. Crossing-Track Traffic
5. Identify the Relationship

Show these as an ordered progression.

The concept page should explain that these relationships are foundational for later longitudinal and conflict-management lessons.

Keep the explanation concise.

Suggested text:

Understanding how aircraft tracks relate is essential before applying many forms of separation.

Do not add detailed separation rules to this concept family.

The focus is traffic geometry and classification.

# 4. Learning journey behaviour

The user should normally move through the lessons in order:

Understanding Track
→ Same Track
→ Reciprocal Track
→ Crossing Track
→ Identify the Relationship

For the current guest experience, do not require authentication.

Progress may be held in frontend state or local browser storage where convenient.

Do not build PostgreSQL persistence or a full progress system in this task.

A user may revisit completed parts from the Traffic Relationships concept page.

# 5. Lesson 1 — Understanding Track

Purpose:

Teach the user what track means and distinguish it from related concepts.

Cover only the essential ideas:

- track is the direction of an aircraft’s path over the ground;
- heading is the direction in which the aircraft is pointed;
- route is the planned or defined path made from route segments or fixes;
- traffic relationship should be determined from the aircraft tracks, not merely from label placement or the direction the symbol appears to face.

Do not turn this into a long theory article.

Use a guided visual demonstration.

Suggested sequence:

## Step 1 — Observe the aircraft

Show one aircraft moving along a visible route.

Teaching text:

The aircraft is following a route across the airspace.

## Step 2 — Show the track

Visually emphasise the aircraft’s actual movement path or track vector.

Teaching text:

Track is the direction of the aircraft’s path over the ground.

## Step 3 — Distinguish route and track

Highlight the route and the current track separately where possible.

Teaching text:

The route is the planned path. The track describes the direction the aircraft is actually travelling.

## Step 4 — Briefly distinguish heading

Use a simple visual difference if the current engine supports it cleanly.

Teaching text:

Heading is the direction the aircraft is pointed. Track is the direction it moves over the ground.

Do not add wind modelling solely for this lesson.

A static or simplified visual distinction is acceptable if necessary.

## Step 5 — Check understanding

Ask one concise conceptual question using the visual state.

Example:

Which element represents the aircraft’s track?

Use the existing interface style.

Do not introduce scores, XP, or badges.

# 6. Lesson 2 — Same-Track Traffic

Purpose:

Teach the user to recognise aircraft travelling along the same general path in the same direction.

Use:

- 2 aircraft;
- 2 or 3 visible routes;
- only one route relevant to the relationship;
- clear label placement with no overlap.

The aircraft should follow the same route or common route segment in the same direction.

One aircraft should lead and the other should follow.

Suggested sequence:

## Step 1 — Observe

Teaching text:

Both aircraft are travelling along the same route in the same direction.

## Step 2 — Emphasise direction

Show track vectors or route direction.

Teaching text:

The aircraft share the same general track direction.

## Step 3 — Identify leader and follower

Teaching text:

One aircraft is leading and the other is following.

## Step 4 — Show spacing change

If useful, use different speeds so the learner can see spacing reduce or increase.

Teaching text:

Their relationship remains same track even when the distance between them changes.

Do not teach full longitudinal separation minima yet.

## Step 5 — Confirm classification

Prompt:

These aircraft are on:

- Same track
- Reciprocal track
- Crossing track
- Neither

Correct answer:

Same track

Give a short explanation after selection.

# 7. Lesson 3 — Reciprocal-Track Traffic

Purpose:

Teach the user to recognise aircraft travelling in opposite directions along the same or substantially the same path.

Use:

- 2 aircraft;
- 2 or 3 visible routes;
- one shared route or route segment;
- opposite movement directions;
- non-overlapping aircraft labels.

Suggested sequence:

## Step 1 — Observe

Teaching text:

The aircraft are travelling along the same route in opposite directions.

## Step 2 — Emphasise closure

Show track vectors pointing towards one another.

Teaching text:

Their track directions are opposite and the distance between them is reducing quickly.

## Step 3 — Explain the relationship

Teaching text:

This is reciprocal-track traffic.

Do not introduce detailed reciprocal longitudinal separation rules yet.

## Step 4 — Confirm classification

Prompt:

These aircraft are on:

- Same track
- Reciprocal track
- Crossing track
- Neither

Correct answer:

Reciprocal track

Provide a concise explanation.

# 8. Lesson 4 — Crossing-Track Traffic

Purpose:

Teach the user to recognise aircraft whose tracks intersect or converge at a common crossing point.

Reuse appropriate parts of the existing Crossing Traffic visual work, but do not turn this lesson into the existing conflict-resolution lesson.

This lesson is about classification, not resolving the conflict.

Use:

- 2 aircraft;
- 3 visible routes;
- 2 intersecting routes;
- a third route for visual context;
- clear left/right label placement.

Suggested sequence:

## Step 1 — Observe

Teaching text:

The aircraft are approaching from different directions.

## Step 2 — Show the track relationship

Visually emphasise both tracks and their common crossing point.

Teaching text:

Their tracks intersect at a common point.

## Step 3 — Explain the relationship

Teaching text:

This is crossing-track traffic.

Do not show:

- predicted minimum separation;
- time to minimum separation;
- prescribed resolution;
- conflict countdowns.

This lesson should not ask the learner to climb, descend, or turn.

## Step 4 — Confirm classification

Prompt:

These aircraft are on:

- Same track
- Reciprocal track
- Crossing track
- Neither

Correct answer:

Crossing track

Provide a concise explanation.

# 9. Lesson 5 — Identify the Relationship

Purpose:

Consolidate the family by asking the learner to classify different traffic geometries.

This should be an interactive recognition exercise rather than a full operational control simulation.

Use a small set of deterministic examples.

Suggested examples:

1. same-track pair;
2. reciprocal-track pair;
3. crossing-track pair;
4. diverging or unrelated pair;
5. visually deceptive pair where aircraft are close but their tracks do not form the expected relationship.

Each example should show:

- two aircraft;
- simple route geometry;
- visible track direction;
- readable labels.

Prompt:

What is the traffic relationship?

Options:

- Same track
- Reciprocal track
- Crossing track
- Neither

After the learner selects an answer:

- state whether it is correct;
- briefly explain why;
- visually emphasise the relevant tracks;
- allow the learner to continue.

Do not show a formal score.

At the end, show a concise completion summary such as:

Traffic Relationships complete

You can now identify:

- same-track traffic;
- reciprocal-track traffic;
- crossing-track traffic;
- unrelated traffic.

Primary action:

Continue to Crossing Traffic

or:

Back to Separation Fundamentals

If the existing Crossing Traffic conflict-resolution lesson remains available, link to it as a related next concept.

Make clear that the learner is moving from identifying crossing traffic to managing it.

# 10. Same, reciprocal, and crossing definitions

Do not invent complex numerical thresholds for classifying the relationships in this task unless the existing domain model already contains validated definitions.

For this first implementation, the scenarios are predefined and intentionally constructed to clearly represent their assigned relationship.

The lesson content should explain the geometry in plain language.

However, keep classification metadata in scenario data.

Example:

```yaml
traffic_relationship:
  type: same_track
  aircraft:
    - SKY123
    - JET456