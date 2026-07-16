# Collaboration, Progress, And Deployment Design

This file captures how AirSpaceSim can support one-computer use, remote two-player sessions, offline learning, invitations, permissions, and student progress tracking.

## Purpose

AirSpaceSim should work in different real training situations:

- one computer available
- instructor and student in the same room
- instructor and student in different locations
- student practicing alone
- internet unavailable or unreliable
- training organization wants progress records later

The design should stay offline-friendly while making online collaboration possible later.

## Recommended Direction

Build AirSpaceSim as:

```text
offline-first for learning
online-capable for collaboration and records
```

This means:

- solo practice should work locally
- lesson/exercise content should work offline
- a local run should not require cloud login
- online sessions should support remote instructor/student collaboration
- progress records can start local and later sync to an account

## Use Modes

### Single Computer / Shared Screen

Situation:

- one laptop or one desktop is available
- student and instructor sit together
- both use the same screen

How it works:

- student acts as ATCO
- instructor acts as pilot/operator/supervisor
- same run workspace is used
- no account system is required at first

Best for:

- early classroom use
- demos
- local practice
- small training groups

### Same Network / Two Devices

Situation:

- instructor and student are in the same room
- each has a device
- one machine runs the API/server

How it works:

- student opens ATCO view
- instructor opens instructor/pilot view
- both connect to the same run
- state is synchronized through the backend

Best for:

- training rooms
- instructor-led practice
- better role separation without internet hosting

### Online Remote Session

Situation:

- instructor and student are not in the same location
- the app runs on a hosted server

How it works:

- instructor creates a training session
- student joins with an invite link
- instructor joins with instructor permissions
- both see the same authoritative simulation state

Best for:

- remote instruction
- distributed training
- organizations with cloud deployment

### Offline Solo Mode

Situation:

- one student practices alone
- internet may not be available

How it works:

- app runs locally
- simulator acts as virtual pilot
- lessons and exercises are available offline
- progress is stored locally
- progress can sync later if online accounts are added

Best for:

- self-study
- field training
- low-connectivity environments

## Roles

### Student ATCO

Primary learner.

Can:

- view assigned training workspace
- issue allowed ATC commands
- complete lessons and exercises
- view own feedback and debrief

Should not normally be able to:

- inject hidden traffic
- change scenario objectives
- edit scoring rules
- reveal instructor-only notes

### Instructor

Training supervisor.

Can:

- view all traffic and exercise state
- inject aircraft
- pause/resume/reset
- trigger failures or abnormal events
- act as pilot operator
- reveal hints
- mark exercise outcome
- add notes to debrief

### Pilot Operator

Human or virtual pilot role.

Can:

- acknowledge ATCO commands
- read back clearances
- report unable
- request clearance
- simulate pilot-side behavior

In many sessions, the instructor can also act as pilot operator.

### Observer

Read-only participant.

Can:

- view traffic
- view progress if allowed
- observe lesson/exercise flow

Cannot:

- issue commands
- alter scenario
- affect scoring

### Admin

System or organization manager.

Can:

- manage users
- manage templates
- manage lesson/exercise content
- manage permissions
- export records

## Role-Based Views

| Role | Main View | Access |
|---|---|---|
| Student ATCO | ATCO workspace | operational commands and own exercise feedback |
| Instructor | instructor console | all traffic, hidden events, injections, resets, scoring |
| Pilot Operator | pilot/readback panel | assigned aircraft responses and pilot actions |
| Observer | observer workspace | view only |
| Admin | admin console | configuration and records |

## Permissions

Permissions should eventually be enforced by the backend, not only hidden in the frontend.

Student ATCO can:

- assign speed
- assign flight level
- assign heading
- assign radial
- direct to fix
- hold at fix
- resume normal navigation

Instructor can:

- all student commands
- start/pause/resume/stop
- reset run
- reset aircraft
- inject traffic
- trigger weather/failure events
- reveal hints
- edit scenario state
- add debrief notes

Pilot Operator can:

- acknowledge command
- read back
- report unable
- request repeat
- request deviation
- report emergency later

Observer can:

- view only

## Shared State And Synchronization

To make sure all players see the same simulation:

- one authoritative backend owns the run state
- clients send commands to the backend
- backend validates and applies commands
- backend broadcasts updated state to all clients
- clients render backend state, not their own separate simulation truth

Basic flow:

```text
Student UI -> command -> API/runtime -> shared run state -> websocket -> all clients
Instructor UI -> event/control -> API/runtime -> shared run state -> websocket -> all clients
Pilot UI -> readback/action -> API/runtime -> shared run state -> websocket -> all clients
```

Important rule:

The frontend should not independently decide that a command succeeded. The backend command result should be the source of truth.

## Invitations

Remote and two-device sessions should use role-specific invite links.

Example links:

```text
Instructor:
https://app/runs/abc123/join?token=instructor-token

Student:
https://app/runs/abc123/join?token=student-token

Observer:
https://app/runs/abc123/join?token=observer-token
```

Invite token should define:

- run/session ID
- role
- permissions
- expiry time
- display name or participant ID
- whether token is single-use or reusable

Early version:

- generate local invite links for a running server
- no full user account required

Later version:

- instructor invites student by email
- student logs in
- progress attaches to student profile

## Student Progress Tracking

Progress tracking is useful for:

- student self-review
- instructor review
- showing improvement over time
- training organization records
- future analytics
- future model training, with consent and privacy controls

Track:

- lessons started
- lessons completed
- exercises attempted
- exercises passed or failed
- score
- commands issued
- command timing
- invalid commands
- rejected commands
- skipped commands
- hints used
- separation losses
- route deviations
- late clearances
- missed restrictions
- instructor notes
- debrief summary

Example progress record:

```json
{
  "student_id": "student_001",
  "lesson_id": "enroute_radial_intercept_intro",
  "exercise_id": "radial_intercept_01",
  "started_at": "2026-05-26T10:00:00Z",
  "completed_at": "2026-05-26T10:08:00Z",
  "result": "passed",
  "score": 86,
  "hints_used": 1,
  "invalid_commands": 2,
  "loss_of_separation_events": 0
}
```

## Command Log

Every training command should eventually record:

- command ID
- run/session ID
- actor ID
- actor role
- aircraft ID
- callsign
- command type
- payload
- result
- reason if rejected/skipped
- timestamp

This supports:

- debrief
- scoring
- progress tracking
- instructor review
- replay

## Data For Model Training

Training data could be valuable later, but privacy must be designed early.

Recommended policy:

- collect progress data for learning records
- collect anonymized analytics only when enabled
- never use identifiable student data for model training without explicit consent
- allow export of personal records
- allow deletion of personal records
- separate training records from research/model-training datasets

Data categories:

- personal progress data
- anonymized command/action data
- scenario performance data
- instructor feedback data
- optional model-training dataset

## Offline Storage

Offline mode should store:

- local lessons completed
- local exercise attempts
- local command logs
- local debriefs
- local scenario templates

Possible file direction:

```text
data/training_progress.v1.json
data/training_sessions.v1.json
data/command_log.v1.json
```

Later, these can sync to a hosted account.

## Future Data Objects

### TrainingSession

Fields:

- session ID
- run ID
- service type
- training mode
- lesson ID
- exercise ID
- participant list
- status
- started at
- ended at

### Participant

Fields:

- participant ID
- user ID if logged in
- display name
- role
- permissions
- joined at

### Invite

Fields:

- token
- session ID
- role
- permissions
- expiry time
- used status

### ProgressRecord

Fields:

- student ID
- lesson ID
- exercise ID
- result
- score
- metrics
- debrief

### CommandLog

Fields:

- command ID
- session ID
- actor ID
- actor role
- command type
- payload
- result
- timestamp

## Recommended Build Order

Do not build the full account system first.

Start with:

1. [ ] Add session role concept, even if local/hardcoded first.
2. [ ] Add command history with actor role.
3. [ ] Add instructor versus student UI capabilities.
4. [ ] Add local progress file for lessons/exercises.
5. [ ] Add invite-link design and token shape.
6. [ ] Add same-network two-device mode.
7. [ ] Add hosted remote session support.
8. [ ] Add user accounts and cloud progress history.

## First Practical Version

The first practical version should support:

- solo free practice
- solo guided practice
- one-computer instructor-led practice
- local command history
- local progress record
- simple role switch in UI

This gives useful training value before building full cloud collaboration.

