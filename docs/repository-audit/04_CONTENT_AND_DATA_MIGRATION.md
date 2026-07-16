# 04 — Content and Data Migration

## 1. Hard-coded scenario and lesson inventory

### In React components (accidental hard-coding per brief)

| Location | Hard-coded values |
|---|---|
| `apps/web/src/pages/CrossingTrafficLearnPage.tsx` | Callsigns `AFR612`, `RAM401`; `TARGET_FLIGHT_LEVEL = 310`; `VISIBLE_ROUTE_IDS = ["X1","X2","A2"]`; label directions per callsign; all 5 stages of lesson copy; `airspace_id: "training_alpha"`, `lesson_id: "enroute_crossing_traffic_intro"` |
| `apps/web/src/pages/HeadingVersusRadialLessonPage.tsx` | Full `lessonSteps` array duplicating `lessons/heading_vs_radial.v1.json`; lesson/airspace ids |
| `apps/web/src/pages/CrossingTraffic*IntroPage.tsx` | Lesson descriptions, next-step wiring |
| `apps/web/src/pages/LearnPage.tsx` | The entire Learn catalogue (one concept) + a dead "Sign in" button |
| `apps/web/src/lib/simulateScenarios.ts` | Simulate registry: slug `gao-sector-traffic`, `airspaceId: "gao_demo"`, aircraft/route counts |
| `apps/web/src/lib/conflict.ts` | `REQUIRED_HORIZONTAL_SEPARATION_NM = 10`, `REQUIRED_VERTICAL_SEPARATION_FT = 1000` — legitimate domain defaults, but duplicated with scenario metadata overrides |
| `apps/web/src/lib/api.ts` | `DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"` (env-overridable — application configuration, acceptable for dev; must not be the production path) |

### In Python

| Location | Values | Classification |
|---|---|---|
| `airspacesim/settings.py` | `AIRSPACE_CENTER = (16.25, -0.03)` (Gao), zoom, speed guardrails, `DEFAULT_SPEED_KNOTS` | Guardrails/speeds = domain constants (fine); centre = environment data leaked into engine config (remove) |
| `airspacesim/cli/commands.py` | `gao_airspace.json` legacy fallbacks | Legacy naming to retire |
| `scripts/seed_hosted_demo.py`, `scripts/start_hosted_dev.py` | Default paths into `airspaces/gao_demo/…`; stable demo session id | Application configuration (update when pack is replaced) |
| `apps/api/app/services/practice_runs.py` | Fallback `aircraft_type "B737"`, `speed_kt 420`, `flight_level 350` for malformed templates | Acceptable defaults; better rejected by validation |

### Already data-driven (preserve the pattern)

- Practice config via `metadata_payload.practice`: `conflict_pair`, `crossing_point`, `required_*_separation`, `visible_route_ids`, `active_commands`, `next` — read by `parsePracticeConfig`. This matches the brief's canonical direction.
- Simulate config via `metadata_payload.simulate`.
- Scenario templates (`airspaces/*/scenarios/*.v1.json`): aircraft, routes, levels, speeds, `appear_after_seconds`.
- Lesson JSONs (`airspaces/training_alpha/lessons/*.v1.json`): objectives, key points, steps, exercise, debrief prompts — **authored but unrendered**; the web app duplicates this content in TSX.

## 2. Gao-specific data (must be removed from public content)

Evidence of real-world derivation:

- `airspacesim/data/scenario_airspace.v1.json`, `map_config.v1.json`, `airspace_data.json`, `airspace_config.json`, `gao_airspace.json`, `scenario.v0.1.json`, `ui_runtime.v1.json`, `render_profile.v1.json`: fixes `ETRUL, PILTI, TESTI, ILDAD, UNOTA, ERGIL, EBVAP, ARGAM, LIPET, OPUGO, LUKNA, TAVIL, BIDUX`; airway identifiers `UA612, UG859, UR971, UM629, UA603, UT365, UR981`; `GAO_VOR`/"Gao Airspace: 60 NM Radius" naming; coordinates centred 16.25 N, 0.03 W.
- `airspaces/gao_demo/`: renamed to "Sahel Control" but keeps the `gao_demo` id, `GAO_VOR` point id, the same real fixes/coordinates, and a scenario literally titled "Gao Sector Traffic".
- `ideas.md` (ignored) references real aerodromes (GAGO Gao, GABS Bamako, GAMB Mopti) confirming the data's operational origin.
- Web/UI references: `simulateScenarios.ts`, user docs (`docs/user/how_to_start_hosted_app.md` "creates a Gao demo run").

The brief's rule: fictional, coherent, realistic naming; do not present real operational data publicly, and do not present fictional data as real. A half-rename ("Sahel Control" over real fixes) satisfies neither.

## 3. Fictional environment migration (DECIDED — 08 Q3)

1. **Design one canonical fictional FIR** (brief suggests e.g. "Nerava FIR": fixes NARVO, LUMEK, SAVEN, TIRGO, MOKRA, DEVAN, RIKOS; routes A1/B12/T45/UL602/UM731) at **neutral fictional coordinates** — a similar geographic *scale* is acceptable, but the environment must not reconstruct the Gao operational environment or reuse its geometry, fix names, airway designators, VOR identifiers, or frequencies.
2. **Delete `airspaces/gao_demo`** after all references are migrated (no slug/seed/link compatibility required — decided). Port the *roles* of `mixed_traffic_demo` and `gao_sector_traffic` onto new fictional scenarios with fictional callsigns (existing callsigns `AFR612`, `RAM401`, `UA612SIM` are real-airline styled — replace per brief examples like `NVR231`, `SKL842`). Tag the repo before deletion so the old pack survives in history.
3. **Keep `training_alpha`** as the beginner classroom pack (already fictional names); re-centre it to neutral coordinates in the same phase for coherence with the Q3 decision (it currently sits on the Gao centre).
4. **Replace `airspacesim/data/*.json` seed content** with a small fictional sample so `airspacesim init` and the PyPI package ship no Gao-derived data; retire `gao_airspace.json` and the `gao_*` fallbacks in `settings.py`/`cli/commands.py` (deprecation note in CHANGELOG).
5. **Update in the same change**: `scripts/seed_hosted_demo.py`, `start_hosted_dev.py`, `simulateScenarios.ts`, user docs, tests that assert on route/fix names, and `settings.AIRSPACE_CENTER` (becomes per-environment data).
6. Add the disclaimer line ("fictional training environment — not for operational use") to pack metadata and the site footer.

## 4. Environment-pack structure (target)

Current manifest format (`package.v1.json` + `airspace.v1.json` + `scenarios/` + `lessons/`) is already close to the brief's pack concept. Evolve rather than replace:

```text
airspaces/<pack-id>/
├── package.v1.json        # manifest: id, name, type, version(NEW), difficulty,
│                          # training_modes, default_scenario, map defaults,
│                          # scenarios[], lessons[]/concepts[](NEW)
├── airspace.v1.json       # points, routes, airspaces (sectors), reference
├── scenarios/*.v1.json    # canonical scenario definitions
└── lessons/*.v1.json      # concept/lesson definitions incl. steps
```

Gaps to close vs the brief:
- **No `version` field** on packs or scenarios today → add `version` (semver) and record `scenario_template_id`+version on runs (the DB already stores a `metadata_payload`; extend it).
- Scenario templates use `schema.name: airspacesim.demo_template` → promote to a named, versioned `airspacesim.scenario` schema with a validator in `io/contracts.py` (validators exist for airspace/aircraft payloads but not for the template shape; `scripts/validate_airspace_package.py` covers part of this and should move to shared code).
- Frequencies, aerodromes, runways, navaid metadata: manifest supports only points/routes/airspaces → extend incrementally when a lesson needs them (do not build speculatively).
- YAML vs JSON: **DECIDED (08 Q4) — JSON stays canonical.** The brief's YAML examples were illustrative; evolve the existing JSON manifests, validators, schemas, and tests. A future user-friendly template may generate canonical JSON.

## 5. Scenario schema migration

1. Freeze current template shape as `scenario_template v1` and write the validator (unique ids/callsigns, route existence against the pack, level/speed ranges via `performance_database`, command whitelist, `appear_after_seconds ≥ 0`).
2. Add `version`, `mode`, `concept`/`family` metadata fields per the brief's canonical example; keep execution data language-neutral.
3. Move Practice/Simulate metadata blocks (`practice`, `simulate`) into the documented schema (they exist ad hoc today).
4. Engine-side: honour `appear_after_seconds`/`entry_time_seconds` inside `Simulation.step()` (see 03 §5) so a scenario file fully determines a run.
5. Plain-language validation errors: pattern already good in API HTTP details; extend to the validator ("Aircraft AFR612 references route X9, but X9 does not exist in training_alpha").

## 6. Translation migration

Current state: **no i18n anywhere** (verified: no i18n library, no locale files; all strings inline in TSX).

**DECIDED (08 Q9)**: the implementer drafts the French translations; the owner reviews and validates aviation and lesson terminology. Ordinary navigation/account/button/product translations are drafted normally. Operational simulation commands remain English-only.

Path:
1. Introduce an i18n library (react-i18next or equivalent — one library, decided once) with `locales/en/`, `locales/fr/` resource files and stable keys (`home.learn.title`, `concepts.crossing_traffic.title`, `lessons.same_track.observe.text`).
2. Extract existing UI strings to `en` keys first (behaviour-neutral), then add `fr`.
3. Lesson/concept JSON: switch display fields to `title_key`/`description_key` (or `{en,fr}` structured fields — pick one convention repo-wide; brief allows either, keys preferred for scale).
4. Operational command layer (`MAINTAIN`, `CLIMB`, `DESCEND`, `TURN LEFT/RIGHT`, `HEADING`, `FLIGHT LEVEL`, `SPEED`, command console, aircraft labels) stays English — mark these components as intentionally untranslated.
5. Language switcher `EN | FR`; guest preference in localStorage (pattern already exists for learn progress), profile field later with auth.
6. Do not duplicate scenario files per language (execution data stays language-neutral — already true).
