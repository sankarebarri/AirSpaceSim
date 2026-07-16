# Curriculum, content architecture, and languages

## Curriculum structure

```text
Service
  → Family
    → Concept
      → Learn
      → Practice stages
      → Related simulations
```

Initial family:

```text
En-route
└── Separation Fundamentals
    ├── Traffic Relationships
    │   ├── Understanding Track
    │   ├── Same-Track Traffic
    │   ├── Reciprocal-Track Traffic
    │   ├── Crossing-Track Traffic
    │   └── Identify the Relationship
    ├── Vertical Separation — Planned
    └── Horizontal Separation — Planned
        ├── Lateral Separation
        └── Longitudinal Separation
            ├── Same Track
            ├── Reciprocal Track
            └── Crossing Track
```

Only Traffic Relationships is implemented in this content phase.

## Generic content components

Prefer reusable runners and activities:

- ConceptPage;
- LearnRunner;
- PracticeRunner;
- SimulationRunner;
- ObservationStep;
- HighlightStep;
- ClassificationStep;
- CommandStep;
- CompletionStep.

Do not create a bespoke React page for every lesson.

## Traffic Relationships

### Understanding Track

Teach route, track, heading, and direction of movement. Do not add wind simulation only for this lesson.

### Same Track

Two aircraft share the same route or common segment in the same direction. Show leader and follower. Spacing may change without changing the relationship.

### Reciprocal Track

Two aircraft use the same or substantially same path in opposite directions. Make closure visually clear.

### Crossing Track

Two tracks intersect at a common point. This lesson teaches classification, not conflict resolution.

### Identify the Relationship

Use deterministic examples for:

- same track;
- reciprocal track;
- crossing track;
- neither.

Provide immediate concise explanation and visual emphasis. No formal score.

The existing Crossing Traffic lesson remains a related next concept: Traffic Relationships teaches recognition; Crossing Traffic teaches management.

## Languages

Initial languages:

- English;
- French.

Translate:

- homepage;
- navigation;
- curriculum;
- concept pages;
- lesson explanations;
- Practice introductions;
- assistance;
- help;
- account pages;
- suitable summaries.

Keep operational simulation commands in English:

- MAINTAIN;
- CLIMB;
- DESCEND;
- TURN LEFT;
- TURN RIGHT;
- HEADING;
- FLIGHT LEVEL;
- SPEED.

Use central translation resources and stable keys, for example:

```text
home.learn.title
families.separation_fundamentals.title
concepts.traffic_relationships.title
lessons.same_track.observe.text
```

Scenario geometry and execution data remain language-neutral.

Guests store language locally. Signed-in users may persist it in their profile. Fallback to English.
