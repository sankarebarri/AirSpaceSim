# Long-Term Training Roadmap

This file tracks the major simulator phases after the post-performance improvement work.

## Purpose

Move AirSpaceSim from a traffic movement simulator into a structured ATC training tool.

## Phase 1: Post-Performance Usability

Status: planned in `post_performance_phase_plan.md`.

Main work:

- [x] command feedback and rejection messages
- [x] ruler and separation learning tools
- [ ] better hold behavior
- [x] route and fix inspection
- [x] scenario authoring validation
- [ ] instructor controls
- [x] training documentation updates

## Phase 2: Training Procedures

Goal: create real ATC learning exercises.

Tasks:

- [x] multi-airspace package support
- [x] custom fictional airspace support
- [ ] departure sequencing exercises
- [ ] arrival sequencing exercises
- [ ] overflight coordination exercises
- [ ] radial interception exercises
- [ ] crossing restriction exercises
- [ ] holding instruction exercises
- [ ] vectoring-for-separation exercises
- [ ] resume-navigation exercises
- [ ] direct-to-fix exercises
- [ ] define success and failure conditions for each exercise

## Phase 3: Instructor And Scenario Builder

Goal: let an instructor build, save, and repeat training sessions.

Tasks:

- [ ] create scenarios from the UI
- [ ] edit aircraft callsign, type, route, FL, speed, and appearance time
- [ ] save scenario templates
- [ ] load scenario templates
- [ ] reset a run
- [ ] reset one aircraft
- [ ] add scripted events
- [ ] add instructor notes per scenario

## Phase 4: Radar Procedure Simulation

Goal: add more advanced radar-control features.

Tasks:

- [ ] aircraft-to-aircraft distance tool
- [ ] predicted conflict detection
- [ ] minimum separation checks
- [ ] short-term conflict alerts
- [ ] radar vectoring workflows
- [ ] route rejoin validation
- [ ] altitude crossing prediction
- [ ] configurable separation minima

## Phase 5: Assessment And Debrief

Goal: evaluate student performance and produce useful feedback.

Tasks:

- [ ] record student commands
- [ ] detect late clearances
- [ ] detect missed restrictions
- [ ] detect loss of separation
- [ ] score exercise performance
- [ ] generate debrief summary
- [ ] show replay timeline
- [ ] export training report

## Current Recommendation

Finish the remaining high-value items in `post_performance_phase_plan.md`, then implement `multi_airspace_custom_airspace_design.md`.

Then start Phase 2 with structured ATC exercises, because exercises will define what the scenario builder and assessment tools need to support.
