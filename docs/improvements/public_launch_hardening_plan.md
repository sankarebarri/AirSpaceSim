# Public Launch & Reuse Hardening Plan

Last updated: 2026-07-09

## Goal

Get AirSpaceSim safe to host publicly, and get the redesigned homepage/dashboard
and a cleanly separable `airspacesim` engine in place, without re-doing work
already tracked in `docs/improvements/new-roadmap.md`. This doc is a companion
checklist scoped specifically to the public-launch push, derived from a full
codebase review on 2026-07-08. It does not replace `new-roadmap.md` (still the
source of truth for the FastAPI+React migration itself) — where an item here
overlaps with an existing `new-roadmap.md` Phase 9/10 item, that's noted inline
instead of duplicated.

## Status Model

- `[ ]` not started
- `[~]` in progress
- `[x]` done

## Priority Order

1. **API hardening** (`apps/api`) — gates public launch, mostly done
2. **Homepage & dashboard redesign** (`apps/web`) — active focus
3. Simulation runtime efficiency (cut redundant backend load during live runs)
4. Engine separability (`airspacesim` as a standalone reusable library)
5. Deployment mechanics (containerization, observability — overlaps `new-roadmap.md` Phase 10)

---

## Phase 1: API Hardening (`apps/api`) — ACTIVE

Status: `[~]` in progress — auth, tenant scoping, resource limits, path fix,
and CORS guard landed; persistence/restart-recovery decisions still open.

This is the gate before the API is safe to expose publicly. Auth model chosen:
**anonymous, session-scoped access** — no login/accounts. Each browser client
generates its own id (`crypto.randomUUID()` in `localStorage`) and sends it as
an `X-Airspacesim-Session` header (or `sid` query param for the WebSocket
stream/CSV export, which can't carry custom headers). See
`apps/api/app/session_identity.py`.

### Authentication & authorization

- [x] Decide the launch auth model — anonymous session-scoped, client-generated
      id via header/query param (cookies were rejected: `apps/api`/`apps/web`
      are separate origins, so a session cookie would need `SameSite=None;
      Secure`, HTTPS-only even in dev).
- [x] Implement chosen auth check on all `/api/v1` routes.
- [x] Implement chosen auth check on the `WS /runs/{run_id}/stream` endpoint.
- [x] Add tests asserting unauthenticated/unauthorized requests are rejected
      (`apps/api/tests/test_session_identity.py`).

### Tenant / ownership scoping

- [x] Add an owner/session identifier column to `runs`
      (`apps/api/app/db/models/run.py`).
- [x] Add an owner/session identifier column to `scenarios`
      (`apps/api/app/db/models/scenario.py`).
- [x] Scope `GET /runs` and `GET /runs/{id}` to the requesting owner
      (`apps/api/app/api/v1/routes/runs.py`).
- [x] Scope `GET /scenarios` and `GET /scenarios/{id}` to the requesting owner
      (`apps/api/app/api/v1/routes/scenarios.py`).
- [x] Verify a client cannot read/stop/command another client's run by
      guessing/enumerating its UUID (cross-session access 404s, not 403 —
      doesn't reveal existence).

### Resource limits & abuse prevention

- [x] Cap concurrent live simulation sessions per client (default 3, via
      `RunRepository.count_active_for_session`).
- [x] Cap total concurrent live simulation sessions process-wide (default 50).
- [x] Add rate limiting to `POST /runs` and `POST /runs/practice` (default 10
      creates/minute per session, `apps/api/app/limits.py`).
- [x] Add a request body size limit for free-form JSON fields — global
      `Content-Length` check via `MaxBodySizeMiddleware` (default 256 KB;
      doesn't cover chunked bodies without `Content-Length`, a reverse-proxy
      limit is the real backstop for that, tracked under Phase 5).

### Path handling

- [x] Add the same containment guard used in `resolve_package_file()`
      (`apps/api/app/airspace_packages.py`) to `_get_package_manifest()`
      in `apps/api/app/services/practice_runs.py` via the new
      `resolve_airspace_package_dir()` helper.
- [x] Add a regression test for an `airspace_id` traversal attempt
      (e.g. `../../etc`) — `apps/api/tests/test_services.py`.

### CORS & config

- [x] Enforce a non-wildcard `cors_allowed_origins` at deploy time for
      production. Implemented via a new `environment` setting (default
      `"development"`) rather than the existing `debug` flag — `debug=false`
      turned out to already be the production env example's value too, so it
      wasn't a usable signal. `create_app()` raises `RuntimeError` at startup
      if `environment == "production"` and origins are still `["*"]`.
      Production env example now sets `AIRSPACESIM_API_ENVIRONMENT=production`.

### Persistence posture for launch

- [ ] Confirm SQLite write contention is acceptable at the expected launch
      concurrency (each active run writes a checkpoint roughly every second).
- [ ] Confirm/document backup policy before launch — this item already
      exists in `new-roadmap.md` Phase 10 ("Define SQLite operational
      strategy"); don't duplicate, just confirm it's resolved before go-live.

### Restart recovery behavior

- [ ] Decide and document the product behavior when a run is interrupted by
      an API process restart (currently: checkpoint-only read access, all
      mutation/resume endpoints return 409 permanently for that run —
      `apps/api/app/services/runs.py:146-160`).
- [ ] Surface that state clearly in the web UI once decided (see Phase 2).

### WebSocket streaming (defer unless launch concurrency requires it)

- [ ] Replace the per-connection `asyncio.sleep(0.05)` busy-poll
      (`apps/api/app/api/v1/routes/runs.py:377-383`) with an async-native
      notification mechanism, if connection count at launch scale makes the
      busy-poll a real cost.

### Testing

- [x] Tests for the path-traversal guard above.
- [x] Tests for auth/tenant scoping (can't read/write another owner's data).
- [x] Tests for request size limits and rate limiting.

---

## Phase 2: Homepage & Dashboard Redesign (`apps/web`)

Status: `[~]` in progress — dashboard metrics strip and site-wide footer
landed 2026-07-09 and stay current. The homepage itself was rebuilt twice on
2026-07-09: the CSS-token-based redesign in the "Homepage structure —
brainstorm" section below shipped first, then was **fully superseded same-day**
by a from-scratch design ported from a user-provided HTML/CSS mockup
(`homepage.html` at repo root) — see "Homepage v2" below. The brainstorm
section is kept for its reasoning trail (still valid context on what NOT to
do — fake data, duplicate disclaimers, empty-for-new-visitors sections) but
`HomePage.tsx`/`HomePage.css` now implement v2, not the structure described
there. Visual language reconciliation and shared-component/hook extraction
remain open (explicitly out of scope for this pass, see plan notes).

The run-workspace cockpit (`RunDetailPage`, `TrafficMap`) is solid and should
be preserved as-is. This phase is scoped to the public homepage and a
dashboard concept, not the cockpit.

### Homepage v2 — full redesign from mockup (2026-07-09)

Superseded the CSS-token rebuild below same-day. Source: a complete,
self-contained HTML/CSS/JS mockup the user dropped at repo root
(`homepage.html`) — custom Syne/Inter font pairing, its own navy/blue token
system, animated inline-SVG radar hero, and a real screenshot of the actual
cockpit UI (not a mockup image — extracted from the base64 payload, confirmed
genuine). Ported faithfully to React with these adaptations:

- [x] **Self-contained page, not wrapped in `AppFrame`.** The mockup's nav/
      footer are a distinct marketing-page treatment from the rest of the
      app's shell — `HomePage.tsx` now renders its own nav (with mobile
      drawer state) and footer entirely independent of `AppFrame.tsx`.
- [x] **Scoped CSS, not global.** New `HomePage.css`, every selector scoped
      under `.landing-page` (the mockup's original CSS used bare `h1`/`h2`/
      `a`/`body` selectors that would have silently overridden the rest of
      the app if imported as-is).
- [x] **Custom cursor dropped.** Asked the user; confirmed skip — hiding the
      native cursor site-wide is real accessibility friction (motion
      sensitivity, OS cursor themes, assistive tech) for a purely decorative
      effect. Everything else ported as designed.
- [x] **Copy adapted for the real, accounts-free product.** The mockup's
      "Log in"/"Sign up free" assume an auth system that doesn't exist (the
      product is intentionally anonymous/session-scoped, per Phase 1). Nav
      and CTAs now read "Launch Simulator" → `/runs`; "Log in" dropped
      entirely.
- [x] **Real routing over in-page anchors where a real page exists.**
      "Lessons"/"Scenarios" nav links route to the real `/lessons`/
      `/scenarios` pages rather than scrolling to an in-page anchor (the
      mockup had no on-page section for either). "How it works"/"Airspaces"
      still anchor-scroll since those sections exist on the page itself.
- [x] **Airspaces section uses live data**, same principle as v1 below —
      `listAirspaces()`, not hardcoded cards. Turned out the mockup's
      airspace content (names, difficulty, even most of the stats) already
      matched the real `gao_demo`/`training_alpha` packages closely —
      "Sahel Control" is genuinely the real display name for `gao_demo`,
      not fake as assumed during the v1 brainstorm. Route/aircraft/sector
      counts from the mockup aren't exposed by the current API response
      shape, so the ported card shows Scenarios/Lessons/Service counts
      instead (all real, all already available) rather than fabricating the
      mockup's numbers.
- [x] Extracted the embedded base64 screenshot to a real asset file
      (`apps/web/src/assets/console-preview.jpg`) instead of an inline
      data URI.
- [x] Added the Syne/Inter Google Fonts links to `apps/web/index.html`.
- [x] Fixed the 2 tests that render the homepage (`app.test.tsx`,
      `routes.test.tsx`) to match the new content; removed now-orphaned CSS
      left over from the superseded v1 rebuild (`.landing-hero`, all
      `.radar-*`, `.warning-strip`, `.how-it-works-*`, `.cta-band`, etc. —
      kept `.landing-section-heading` since `HeadingVersusRadialLessonPage.tsx`
      still uses it).
- [ ] `homepage.html` still sits at the repo root as the original source
      reference — not yet deleted, pending user confirmation it's no longer
      needed.

### Homepage structure — brainstorm (2026-07-09), superseded by v2 above

Original proposed structure: Nav → Hero → Warning strip → Skills → Flow →
Airspaces → Lessons → Runs → CTA → Footer (8 content sections). Reviewed
against the actual current `HomePage.tsx` and trimmed to ~5 sections —
mapping and reasoning per section:

- **Nav** — keep as-is. This is an app-with-marketing-front, not a separate
  marketing site, so full nav (Home/Simulation/Lessons/Airspaces/Scenarios)
  is appropriate.
- **Hero** — keep headline/lede/primary CTA. Currently has two
  near-equal-weight CTAs (Launch Simulator / Start a lesson) which dilutes
  the primary action — demote the lesson link to a plain text link under the
  button, not a second button. Also currently has a live stats strip
  (scenario/run counts) crammed into the hero copy — cut it (see "Runs"
  below for why).
- **Warning strip** — currently embedded inside the hero as inline copy
  (`landing-safety-banner`), and a near-duplicate disclaimer also exists at
  the bottom of the page (`landing-disclaimer`). Pull the warning out into
  its own thin full-width strip directly under the hero, and delete the
  bottom duplicate — **one disclaimer, not two**.
- **Skills** ("What You Practice", 4 tiles) and **Flow** ("Training Flow", 3
  steps) — these two sections do overlapping explanatory work (what you'd
  practice vs. how you get there). Merge into one "How it works" section:
  the 3-step flow as the spine, skill call-outs folded in as short
  sub-bullets per step. Cuts a full section without losing content.
- **Airspaces** — keep the section, but it currently renders **hardcoded
  fake content** (`airspaceCards` array in `HomePage.tsx:42-53` — names like
  "Sahel Control" that don't match the real airspace packages on disk,
  `gao_demo` and `training_alpha`). Wire it to the real `listAirspaces()`
  API call instead (already exists, already used on `AirspacesPage.tsx`).
- **Lessons** — currently one hardcoded card, because there is exactly one
  real lesson in the product today. A full dedicated section for one item
  is thin. Fold it into the Airspaces section as a small tag/callout on the
  relevant airspace card, or into the CTA band. Revisit as a real section
  once there are several lessons.
- **Runs** ("Recent Activity") — pulls the visitor's own scenario/run
  counts and recent runs. For any first-time anonymous visitor (which, after
  the Phase 1 session-scoping work, is every new visitor by definition) this
  is **always empty** — dead weight 100% of new visitors see. Cut from the
  public homepage entirely; this content is the natural seed of a real
  dashboard instead (see below) — it belongs on a page you land on *after*
  doing something, not before.
- **CTA** — doesn't exist as its own block today (only the hero's buttons).
  Worth adding: a closing "Ready to work some traffic? Launch the
  simulator." band after the value-prop sections — a legitimate second
  chance to convert scrollers, not redundant with the hero CTA, as long as
  it stays the only other primary CTA on the page.
- **Footer** — doesn't exist today. Add a minimal one: the consolidated
  safety disclaimer (or a short version, if the strip already covers it), a
  link to the repo/docs, maybe a version tag.

**Net recommended structure**: Nav → Hero → Warning strip → How It Works
(merged Skills+Flow) → Airspaces (real data, lesson folded in) → CTA →
Footer. ~5 content sections instead of 8, no section that's empty/fake for a
first-time visitor, one disclaimer instead of two.

- [x] ~~Rebuild `HomePage.tsx` per the structure above~~ — done, then fully
      replaced by Homepage v2 above same day. `HomePage.tsx` no longer has
      this shape.
- [x] Wire the Airspaces section to `listAirspaces()` instead of the
      hardcoded `airspaceCards` array — still true, carried into v2.
- [x] ~~Consolidate the two disclaimers into one warning strip~~ — moot,
      v2's footer legal text is the single disclaimer now.
- [x] Add a real `<footer>` (`AppFrame.tsx`, suppressed on the cockpit page
      via the existing `pageClassName?.includes("cockpit")` check) — this
      `AppFrame` footer still serves every other page; the homepage has its
      own separate footer as of v2 since it no longer uses `AppFrame`.

### Dashboard — decided (2026-07-09)

**Decision: enhance `RunsPage.tsx` into the dashboard.** No new route/nav
item. It directly absorbs the "Recent Activity" content cut from the
homepage (active runs, recent scenarios, quick-resume) plus its existing
run-creation-form-plus-grid role.

- [x] Add an at-a-glance summary strip to `RunsPage.tsx` (Scenarios / Active
      runs / Total runs — `.dashboard-metrics`, sourced from the page's
      existing `runsQuery`/`scenariosQuery` data, no new API calls). The
      existing create-run form and run card grid below serve the
      quick-resume role already, so no separate mini-list was added.
- [ ] Design for the eventual existence of auth/login (even if not required
      at launch) so the dashboard doesn't need a rework later.

### Shared components

- [ ] Extract shared primitives out of duplicated inline page markup:
      Card, StatusPill, EmptyState (currently reimplemented per-page; see
      `apps/web/src/pages/*.tsx`).
- [ ] Extract shared data-fetching hooks (`useRuns`, `useScenarios`, etc.)
      out of page components into `apps/web/src/hooks/` (currently empty).

### Styling

- [x] **Decision: keep hand-written CSS.** No framework migration, still
      true as of v2. `apps/web/src/styles/index.css` picked up a
      `--space-xs`..`--space-xl` spacing scale during v1 (still there, still
      used by `RunsPage`/`AppFrame`) — not retrofit across the whole file,
      longer-term follow-up.
- [x] **v2 superseded the "scope, don't merge" resolution with a cleaner
      split: the homepage now has its own entirely separate token system**
      (`HomePage.css`, scoped under `.landing-page` — Syne/Inter fonts, navy/
      blue palette) that doesn't share tokens with `index.css` at all. This
      is a deliberate marketing-page-vs-app-interior split (same pattern as
      Stripe/Linear/Vercel), not an oversight — worth remembering that
      `--accent`/`--space-md`/etc. from `index.css` don't apply inside
      `.landing-page`, and vice versa. Full site-wide token reconciliation
      for the rest of the app remains open, out of scope for this pass.
- [x] **Decision: homepage is mobile-first.** The cockpit (`RunDetailPage`)
      stays desktop-first as already speced. v2 ships this via the mockup's
      own `768px`/`480px` breakpoints (`HomePage.css`), separate from
      `index.css`'s breakpoint scale.

### Cleanup for public visibility

- [x] Remove the raw API host debug display (`.api-pill` in `AppFrame.tsx`).
- [ ] Add a broader accessibility pass (aria labels, focus states) across
      `src/` — this pass only covers the new markup added to `HomePage.tsx`/
      `RunsPage.tsx`/`AppFrame.tsx` (landmark elements, heading hierarchy,
      `role="note"` on the warning strip); a full site-wide audit of the
      other pages remains open.

### Auth UI

- [x] Wire the client-generated session id into the frontend so the app keeps
      working against the now-required header (`apps/web/src/lib/session.ts`,
      `apps/web/src/lib/api.ts`) — no login UI needed, auth model is anonymous.
- [ ] If a real accounts model is ever added post-launch, add login UI and
      protected-route handling in `apps/web/src/app/routes.tsx` then.

### Testing

- [x] Fixed 2 pre-existing broken assertions in `app.test.tsx` and
      `routes.test.tsx` that rendered the old (already-stale) homepage
      content — in scope since this pass rewrites the exact page they render.
- [x] Fixed `components.test.tsx`'s `AppFrame` test, which asserted the
      removed API-host debug pill. The cockpit-suppression test added here
      was later deleted (2026-07-09) once `RunDetailPage` stopped using
      `AppFrame` entirely — see the cockpit redesign section below.
- [x] Added the `/api/v1/airspaces` fetch mock to tests that render
      `HomePage` (it now calls `listAirspaces()`).
- [ ] `routes.test.tsx`'s "renders airspace packages from the API" test has
      a separate, pre-existing, unrelated failure (`AirspacesPage.tsx` no
      longer renders a CLI template hint the test still checks for) — not
      touched by this phase, left open.

### Live Run Cockpit Redesign (`RunDetailPage`) — 2026-07-09

A third mockup (`dashboard.html` at repo root) redesigned the **live run
console**, not `RunsPage`'s dashboard above — a dense, dark, IBM-Plex-Mono
ATC-console aesthetic. Cross-referenced against the real, working
`RunDetailPage.tsx` (WebSocket streaming, 8 operator commands, lifecycle
controls, CSV export, filters, measure tool) and `TrafficMap.tsx` before
touching anything. Two mock elements had no real backing and were dropped
per user decision: the ATIS strip (fake weather/runway data — no such model
exists) and conflict/proximity detection (not computed server-side).

- [x] Rebuilt `RunDetailPage.tsx` with the new topbar/traffic-panel/tabbed
      detail-panel/transcript-log layout, preserving all existing
      WS-streaming, query, and command-mutation logic verbatim.
- [x] `TrafficMap.tsx` required **zero logic changes** — it already
      self-renders its own HUD/reset/footer chrome, only needed new CSS
      rules scoped under the page's new wrapper class.
- [x] Added real features the mock implied but didn't have live-data backing
      for elsewhere: a session elapsed-timer from `run.started_at`, a
      click-to-edit sim-rate control, a Hold/Resume topbar toggle, and
      toast notifications for command/lifecycle results — all wired to
      existing handlers, no backend changes.
- [x] Dropped mock elements with no real backing: ATIS strip, squawk code
      fields (`ADD_AIRCRAFT` has no such field), and the free-text
      "type a command" log input (bypasses real command validation).
- [x] `RunDetailPage` no longer wraps in `AppFrame` — its own topbar/footer
      fully replace the app nav for this page, matching the precedent set
      by the homepage redesign (a focused operational console shouldn't
      carry marketing-style nav). Removed the now-dead `isCockpit` /
      footer-suppression branch from `AppFrame.tsx` (confirmed: no other
      page ever passed `pageClassName` containing `"cockpit"`).
- [x] New scoped `RunDetailPage.css` (same `.console-page`-scoped pattern as
      `HomePage.css`), and removed the orphaned CSS this replaced
      (`.console-panel`, `.run-workspace-console`, `.traffic-rail`,
      `.operator-rail`, `.cockpit-*`, and ~15 other classes confirmed via
      full-source search to have zero remaining references) —
      `index.css` went from 3551 to 2275 lines. A handful of dead
      mixed-selector CSS fragments may remain where an orphaned class was
      comma-joined with a still-used one in the original file; harmless,
      not chased further given the effort/risk tradeoff for a cosmetic
      cleanup.
- [x] Updated `run-detail.test.tsx`: the 6 command forms moved behind a new
      "Clearances" tab (tests now click it first) and several elements
      needed real heading/label semantics added (run name, "Tracks",
      selected aircraft callsign, "Command History") to keep passing
      `getByRole("heading", ...)`/`getByLabelText(...)` queries — same
      underlying functionality, verified end to end, all 3 tests pass.

---

## Phase 3: Simulation Runtime Efficiency

Status: `[ ]` not started — brainstormed 2026-07-09, not yet implemented.

Goal: make sure an active simulation run isn't generating more backend load
than it needs to, especially per-operator-action. Not launch-blocking, but
cheap to fix and compounds with concurrent runs.

### Confirmed, concrete issue

- [ ] **Redundant REST calls on every operator command.** In
      `apps/web/src/pages/RunDetailPage.tsx`, both `commandMutation` and
      `lifecycleMutation` call `queryClient.invalidateQueries` for
      `["runs"]`, `["run", runId]`, and `["run", runId, "state"]` in
      `onSuccess` — unconditionally, on every single command (`SET_SPEED`,
      `SET_FL`, heading assignment, everything). This forces 3 REST
      round-trips after each command. But the WebSocket message handler a
      few lines above already patches the same query cache directly via
      `queryClient.setQueryData` when the backend pushes
      `run_state.snapshot`/`run_state.updated` events. So whenever the
      WebSocket is connected (the normal case), every operator command
      triggers three REST calls that duplicate what the socket is about to
      push anyway. Fix: skip the `invalidateQueries` calls when
      `streamStatus === "open"`; keep them only as the fallback path when
      the WebSocket isn't connected.

### Related, lower priority (already partially known)

- [ ] WebSocket loop busy-polls every 50ms per connection instead of
      blocking on a real notification (`apps/api/app/api/v1/routes/runs.py`,
      already flagged in Phase 1's deferred WebSocket item — same root
      cause, listed here too since it's part of the same "cost per
      connection" concern).
- [ ] Every state publish sends the full aircraft list, not a diff — fine
      at today's aircraft counts, won't stay free as counts grow.
- [ ] Simulation ticks (and publishes) 4x/second per active run regardless
      of whether any client tab is even focused — consider throttling via
      the Page Visibility API for backgrounded tabs, or only publishing when
      the snapshot actually changed.
- [ ] Checkpoint writes hit SQLite roughly once/second per active run
      (cross-referenced from Phase 1's persistence-posture item — same
      underlying cost, tracked once there under "Persistence posture").

---

## Phase 4: Engine Separability (`airspacesim` as a standalone library)

Status: `[ ]` not started

Not launch-blocking for the web app (`apps/api` already works around the
coupling by monkeypatching `save_aircraft_data`), but required before
`airspacesim` can be cleanly reused in another project.

- [ ] Make `Settings` instance-based instead of a global singleton
      (`airspacesim/settings.py:142`); thread an explicit settings instance
      through `AircraftManager.__init__` instead of importing the module-level
      `settings` object from `aircraft.py`, `aircraft_manager.py`,
      `scenario_runner.py`.
- [ ] Promote a public single-step method on `AircraftManager` (currently
      only the private `_step_all_aircraft`,
      `airspacesim/simulation/aircraft_manager.py:476`) matching what
      `docs/architecture/engine_boundary.md:147` already documents as the
      public API.
- [ ] Make simulation persistence an injectable `TrajectorySink` (the
      protocol already exists in `airspacesim/core/interfaces.py` but isn't
      wired into `AircraftManager`) instead of the hardcoded
      `save_aircraft_data()` calls inside `events.py` and the tick loop.
- [ ] Remove or clearly relocate dead/unused modules from the pip package:
      `airspacesim/routes/manager.py` + `airspacesim/routes/processor.py`
      (unused by the runtime — `scenario_runner` builds routes inline
      instead), `airspacesim/map/marker_manager.py` +
      `airspacesim/map/renderer.py` (zero internal references).
- [ ] Move/exclude legacy UI-serving code from the installable package:
      `airspacesim/templates/`, `airspacesim/static/`, `dev_server.py`,
      `airspacesim/cli/commands.py`'s UI-bootstrap parts — already flagged
      as a known issue in `docs/architecture/engine_boundary.md`.
- [ ] Clean up emoji-laden log messages in `aircraft_manager.py` (e.g.
      `"🛫 Starting simulation..."`) — minor, but a real inconsistency for a
      library meant to be embedded in other projects' logs.
- [ ] Add a test proving two independent `AircraftManager` instances (with
      different settings) can run concurrently in one process.

---

## Phase 5: Deployment Mechanics

Status: `[ ]` not started

Overlaps `new-roadmap.md` Phase 10 ("Deployment and First Hosted Release") —
this section exists here only to keep the public-launch checklist complete in
one place; treat `new-roadmap.md` Phase 10 as authoritative and check items
off there.

- [ ] Container build for `apps/api`.
- [ ] Frontend serving strategy for `apps/web` (reverse proxy vs. static
      hosting).
- [ ] Structured logs / request logging / error reporting hooks.
- [ ] Verify first hosted release criteria in `new-roadmap.md` Phase 10.

---

## Notes

- This doc assumes the engine/app separation, data-contract split, and
  UI/backend decoupling decisions in `docs/adr/0001`–`0004` and
  `docs/architecture/engine_boundary.md` — don't relitigate those here.
- Training modes, multi-airspace authoring, and collaboration/multiplayer
  (see `docs/improvements/training_modes_lessons_design.md`,
  `docs/improvements/multi_airspace_custom_airspace_design.md`,
  `docs/improvements/collaboration_progress_and_deployment_design.md`) are
  explicitly out of scope for this push — real scope-creep risk if pulled
  forward before Phase 1–2 here ship.
