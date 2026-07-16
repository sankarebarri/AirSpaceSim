# Focused build prompt: Traffic Relationships

Implement:

```text
Separation Fundamentals
└── Traffic Relationships
    ├── Understanding Track
    ├── Same-Track Traffic
    ├── Reciprocal-Track Traffic
    ├── Crossing-Track Traffic
    └── Identify the Relationship
```

Keep visible but unavailable:

- Vertical Separation;
- Horizontal Separation;
- Lateral Separation;
- Longitudinal Separation: Same, Reciprocal, and Crossing Track.

Do not implement those planned areas yet.

## Requirements

- Use the shared AirSpaceSim engine.
- Use fictional environment data.
- Use no more than three routes per example.
- Use two aircraft per classification example.
- Prevent label overlap with scenario-configurable placement.
- Use a wide readable lesson panel.
- Support English and French.
- Keep execution data language-neutral.
- Create no bespoke React page per lesson.
- Use reusable observation, highlight, classification, and completion activities.
- Do not show prediction metrics.
- Do not ask for operational resolution commands in the relationship lessons.
- Do not assign formal scores.

## Lesson flow

### Understanding Track

Explain route, track, heading, and direction of movement through a guided visual demonstration.

### Same-Track Traffic

Show two aircraft on the same route or common segment in the same direction. Identify leader and follower. Demonstrate that spacing may change while the classification remains same track.

### Reciprocal-Track Traffic

Show two aircraft on the same or substantially same path in opposite directions. Make the closure visually obvious.

### Crossing-Track Traffic

Show two aircraft on intersecting routes and emphasise the common crossing point. Teach classification only.

### Identify the Relationship

Present deterministic examples and ask:

- Same track
- Reciprocal track
- Crossing track
- Neither

After each answer:

- indicate correctness;
- explain why;
- highlight the relevant geometry.

At completion, offer:

- back to Traffic Relationships;
- back to Separation Fundamentals;
- continue to the existing Crossing Traffic management lesson.

Traffic Relationships teaches recognition. Crossing Traffic teaches management.
