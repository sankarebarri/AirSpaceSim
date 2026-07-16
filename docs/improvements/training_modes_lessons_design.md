# Training Modes, Crew Roles, And Lesson Design

This file captures the training-service, role, solo-learning, and lesson-design ideas for AirSpaceSim.

## Purpose

AirSpaceSim should become more than a traffic movement simulator. It should support different types of ATC training, different crew/player modes, and short lesson-to-exercise learning flows.

The lesson content should support ICAO/OACI-based learning, but it must not replace official courses, instructor teaching, local procedures, or current regulatory documents.

## Standards Reference Direction

Lessons should be designed around current ICAO/OACI concepts and then checked against the latest official material before release.

Reference families to track:

- ICAO Annex 11: Air Traffic Services
- ICAO Doc 4444: Procedures for Air Navigation Services - Air Traffic Management, PANS-ATM
- ICAO Doc 9432: Manual of Radiotelephony
- ICAO Annex 10, Volume II: Communication Procedures
- Local AIP, local ATS manuals, and school-specific procedures when available

Rule for content:

- The app can summarize concepts for training support.
- The app should clearly say when local instructor or local procedure confirmation is required.
- The app should not present itself as the official legal source.

## Control Service Training Types

### Parking / Apron Management

Training focus:

- stand and gate assignment
- startup approval
- pushback sequencing
- towing
- apron route conflicts
- coordination with ground or aerodrome control

Possible exercises:

- sequence multiple pushbacks from nearby stands
- prevent apron route blockage
- assign a stand to an arriving aircraft
- coordinate handoff from apron to aerodrome control

### Aerodrome Control

Training focus:

- taxi clearances
- runway crossings
- line up and wait
- takeoff clearance
- landing clearance
- circuit traffic
- runway occupancy
- go-around or missed approach basics

Possible exercises:

- sequence one arrival and two departures
- avoid runway incursion
- manage taxi crossing traffic
- handle a go-around

### Approach Control

Training focus:

- arrival sequencing
- descent planning
- speed control
- vectoring to final
- holding
- missed approach coordination
- handoff to tower or en-route

Possible exercises:

- sequence arrivals to final
- hold one aircraft and release it later
- manage a late descent request
- vector traffic around weather

### En-Route Control

Training focus:

- route and radial tracking
- flight level assignment
- crossing restrictions
- procedural separation
- speed control
- route deviation
- resume normal navigation
- sector handoff

Possible exercises:

- separate crossing traffic using FL assignment
- assign a radial deviation and resume navigation
- direct an aircraft to a fix
- hold an aircraft at a fix

### Radar Control

Training focus:

- radar identification
- radar vectors
- tactical separation
- heading, speed, and FL instructions
- conflict detection
- short-term prediction
- route rejoin

Possible exercises:

- identify converging traffic
- vector one aircraft for separation
- use speed control to sequence aircraft
- restore an aircraft to route after radar vectoring

## Crew And Player Roles

### Student ATCO

The main learner.

Responsibilities:

- monitor traffic
- issue instructions
- maintain separation
- sequence aircraft
- coordinate handoffs
- complete exercise objectives

### Instructor / Pilot Operator

The human instructor can act as the pilot side and scenario supervisor.

Responsibilities:

- respond to student instructions
- inject new traffic
- create failures or abnormal situations
- pause or reset exercises
- evaluate performance

### Virtual Pilot

The simulator can play the pilot role when the student is alone.

Responsibilities:

- acknowledge valid instructions
- reject impossible or invalid instructions
- execute accepted commands
- provide simple readbacks
- create controlled training friction later, such as readback errors or delayed compliance

## Training Modes

### Two-Person Mode

Roles:

- student: ATCO
- instructor: pilot operator and supervisor

Best for:

- classroom practice
- formal training sessions
- instructor-led assessment

### Solo Guided Mode

Roles:

- student: ATCO
- simulator: virtual pilot and coach

Best for:

- self-learning
- guided exercises
- practice before instructor sessions

Expected behavior:

- the app gives short instructions
- the virtual pilot acknowledges commands
- invalid commands explain why they failed
- hints can appear when the student is stuck
- the exercise ends with a short debrief

### Solo Free Practice Mode

Roles:

- student: ATCO
- simulator: traffic engine and virtual pilot

Best for:

- practicing without scoring
- exploring procedures
- learning aircraft movement effects

Expected behavior:

- no strict lesson flow
- no required objective
- valid commands are applied
- invalid commands are rejected with clear feedback

## Solo Learning Design

One person should be able to learn without needing another person to play the pilot.

To support this, AirSpaceSim needs:

- virtual pilot readbacks
- clear command feedback
- automatic execution of valid instructions
- optional hints
- simple scoring in guided exercises
- replay or debrief later

Example flow:

1. Student selects `DEP01`.
2. Student assigns `Climb FL350`.
3. Virtual pilot responds: `DEP01, climbing FL350`.
4. Aircraft climbs dynamically.
5. If the command is impossible, the virtual pilot responds: `Unable FL350, C208 maximum FL250`.

Future virtual pilot behaviors:

- readback error
- delayed compliance
- unable due performance
- request weather deviation
- request descent
- request direct routing
- emergency report
- radio congestion simulation

## Lesson And Exercise Model

AirSpaceSim should use a short lesson followed by immediate simulator practice.

Each training topic should have:

1. Short lesson
2. Guided demonstration
3. Practice exercise
4. Debrief

### Short Lesson

Purpose:

- teach one concept only
- stay short, usually 2-5 minutes
- use visuals and examples
- support classroom learning, not replace it

Content examples:

- what is a radial
- heading versus radial
- what is vertical separation
- how to issue a flight level instruction
- holding basics
- speed control basics

### Guided Demonstration

Purpose:

- show the technique before asking the student to perform it

Examples:

- aircraft intercepts R265
- aircraft resumes normal navigation
- aircraft climbs from FL290 to FL350
- aircraft enters a hold at GAO_VOR

### Practice Exercise

Purpose:

- let the student perform the action
- check whether the objective was achieved

Examples:

- assign a radial and then resume navigation
- climb one aircraft for separation
- direct an aircraft to GAO_VOR
- hold an aircraft until another aircraft has passed

### Debrief

Purpose:

- show what happened
- identify correct actions
- identify missed actions
- link back to the lesson

Possible debrief items:

- commands issued
- time to act
- final separation
- route deviation
- altitude compliance
- invalid commands

## Lesson Types

### Concept Lessons

Examples:

- flight level
- radial
- heading
- procedural separation
- holding pattern
- DME

### Technique Lessons

Examples:

- assign heading
- assign radial
- direct to fix
- resume normal navigation
- assign speed
- assign climb or descent

### Standards And Phraseology Lessons

Examples:

- standard ATC phraseology
- readback expectations
- clearance structure
- separation minima concepts
- transition altitude and transition level concepts

These lessons must be reviewed against current ICAO/OACI references and local procedures before being treated as training material.

### Visual Interpretation Lessons

Examples:

- reading aircraft labels
- understanding heading vectors
- reading route lines
- interpreting convergence
- estimating distance from GAO VOR

### Scenario Briefing Lessons

Examples:

- objective briefing
- traffic situation
- airspace constraints
- expected method
- exercise success criteria

## First Lesson Candidates

Start with en-route because the current simulator already supports most of it.

1. [ ] Reading Aircraft Labels
2. [x] Heading Versus Radial
3. [ ] Flight Level Assignment
4. [ ] Speed Control
5. [ ] Resume Normal Navigation
6. [ ] Direct To A Fix
7. [ ] Holding Basics
8. [ ] Procedural Separation Basics
9. [ ] Conflict Resolution Introduction

## Suggested Lesson File Shape

Example:

```json
{
  "id": "enroute_radial_intercept_intro",
  "title": "Radial Interception",
  "service_type": "enroute",
  "level": "beginner",
  "duration_minutes": 4,
  "learning_objectives": [
    "Understand the difference between heading and radial",
    "Assign an intercept radial",
    "Resume normal navigation after deviation"
  ],
  "standards_reference": [
    "ICAO Annex 11",
    "ICAO Doc 4444",
    "ICAO Doc 9432"
  ],
  "lesson_steps": [
    {
      "type": "text",
      "title": "What is a radial?",
      "body": "Short student-facing explanation goes here."
    },
    {
      "type": "visual",
      "asset": "radial_intercept_diagram"
    },
    {
      "type": "sim_demo",
      "scenario_template": "radial_intercept_demo"
    }
  ],
  "exercise_id": "enroute_radial_intercept_exercise_01"
}
```

## Suggested App Flow

Top-level training navigation:

- Learn
- Practice
- Debrief

Example screen:

```text
Lesson: Radial Interception

[Learn] [Watch Demo] [Start Exercise]
```

Design rules:

- lesson screens should be short
- use diagrams and map visuals
- avoid long textbook pages
- always end with a practice action
- keep references visible but not overwhelming

## Data Model Direction

Future objects:

- TrainingServiceType
- TrainingMode
- Lesson
- Exercise
- ScenarioTemplate
- AssessmentRule
- Debrief
- VirtualPilotResponse

## Recommended Build Order

1. [ ] Add training service type metadata to scenario templates.
2. [ ] Add training mode metadata: `two_person`, `solo_guided`, `solo_free_practice`.
3. [x] Create first lesson format.
4. [x] Create first 5 en-route lessons.
5. [x] Link first lesson to an exercise.
6. [x] Add frontend-only practice for the first lesson.
7. [ ] Add a simple Learn / Practice / Debrief UI flow.
8. [x] Add `Open Live Simulator Practice` button after backend practice-run launch exists.
9. [ ] Add virtual pilot readbacks for accepted and rejected commands.
10. [ ] Add basic debrief summary.

## Recommended Starting Point

Start with:

- service type: en-route control
- mode: solo guided
- lesson: heading versus radial
- exercise: assign radial, monitor capture, resume normal navigation

Reason:

The simulator already supports aircraft movement, FL changes, speed changes, radial interception, direct-to, holds, and resume navigation. En-route solo guided training is the shortest path from the current simulator to a real learning product.
