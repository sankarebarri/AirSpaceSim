# Product vision and non-negotiables

## Product vision

AirSpaceSim is an interactive aviation learning and simulation platform and a reusable technical foundation.

The hosted web app is one consumer of the engine. The same engine should eventually support:

- fictional training sectors;
- different airports and airspace environments;
- approach and en-route simulations;
- user-created scenarios;
- batch experiments;
- conflict-detection research;
- AI and ML research;
- replay and debrief tools;
- other frontends.

## Current public structure

### Learn

Guided learning through the simulation itself.

Typical sequence:

> Explain → Show → Do → Observe → Understand the result.

### Practice

Scenario-based application with reduced assistance.

Practice may use scenario-specific objectives such as establishing separation before a defined crossing point and maintaining it through the encounter.

### Simulate

Free control of predefined traffic.

It uses general engine separation monitoring, not narrow Practice completion rules. The summary is factual and is not a competency assessment.

## Non-negotiables

1. Learn, Practice, and Simulate use the same core engine.
2. Built-in scenarios are deterministic and reproducible.
3. New lessons are data-driven, not one React page per lesson.
4. Public content uses a fictional, realistic training environment instead of Gao operational data.
5. Guests can use public Learn, Practice, and solo Simulate.
6. Authentication primarily adds persistence.
7. Scenario-specific Practice evaluation stays outside the general separation monitor.
8. The core engine is independently packageable and testable.
9. No production secrets or hard-coded localhost URLs.
10. No user-facing predicted minimum separation or time-to-minimum-separation in the current foundational lessons.

## Do not

- create separate movement or physics logic per mode;
- bury scenarios inside UI components;
- translate operational command words into French;
- store every simulation frame in PostgreSQL;
- count one continuous loss of separation once per tick;
- expose broken controls to make the UI appear advanced;
- use user-facing names such as Point A, Route Alpha, or Airspace Alpha;
- couple the engine to FastAPI, SQLAlchemy, browser APIs, or authentication.
