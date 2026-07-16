# 08 — Open Questions

Only questions that genuinely require the developer's decision; everything answerable from the repository or brief has been answered in documents 01–07.

**Q1 — PyPI compatibility posture.** `airspacesim` 0.1.3 is published. May 0.2.0 make breaking changes (drop `hello.py`, `routes/route_manager.py` shim, `gao_*` settings fallbacks, empty subpackages), or must 0.2.x stay compatible with deprecation warnings and breaks wait for a later release? Are there known external users?

**Q2 — Fate of the legacy static UI and `airspacesim init` workflow.** Keep shipping the static Leaflet UI + dev server inside the engine wheel indefinitely, extract them to a separate compatibility package, or schedule retirement? (`docs/architecture/legacy_static_ui_decision.md` defers this; it now gates the "open-source-ready core" goal and the size of Phase 8.)

**Q3 — Replacement for `gao_demo`.** Approve creating a new fictional FIR (brief's Nerava-style naming) and deleting `airspaces/gao_demo` outright, or must a renamed/regeometried successor keep demo continuity (same scenario slugs) for anyone using current links/seeds? Also confirm: is keeping the Gao-area *coordinates* (with fictional names) acceptable, or should the fictional FIR move to neutral coordinates entirely?

**Q4 — Pack format: stay JSON or adopt YAML.** The brief illustrates YAML packs; the entire existing pipeline (validators, manifests, API, zero Python dependencies in the engine) is JSON. Recommendation: stay JSON. Confirm.

**Q5 — Alembic history.** The API has never been deployed. May the three SQLite-flavoured migrations be squashed into one PostgreSQL-verified baseline, or must the existing revision chain be preserved?

**Q6 — Hosting target.** Docker-compose self-hosting, a PaaS (e.g. Render/Fly/Railway) for API + managed PostgreSQL with static-hosted frontend, or single-server? This decides Phase 7 deliverables (Dockerfiles vs platform configs vs both).

**Q7 — Auth mechanism.** Email+password with server-side sessions, or an OAuth provider (Google) only, or both? The brief says "minimal"; either satisfies it, but the choice affects `SECRET_KEY`/redirect env vars and the local-test-account documentation.

**Q8 — `dashboard.html`.** This untracked root file is a full standalone console design mock. Is it the intended visual direction for the run workspace (then archive under `docs/frontend/` as a design artefact), or disposable (then it's a delete candidate)?

**Q9 — French content authorship.** Should FR translations be drafted by the implementer for your review (you appear to be a francophone-region domain expert), or will you supply/validate the French lesson copy? This affects Phase 5 scheduling.

**Q10 — Simulate summary persistence for guests.** When run summaries move server-side (Phase 2), should guest run history remain listable only within the anonymous browser session (current behaviour), or be pruned after a retention period? Affects the `runs` table growth policy and rate-limit tuning.
