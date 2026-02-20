# Contributing to AirSpaceSim

## Development Setup

Supported Python versions: `3.10`, `3.11`, `3.12`.

1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install in editable mode:
```bash
pip install -e .
```

3. Install dev tools:
```bash
pip install -r requirements-dev.txt
```

Offline-constrained editable install:
```bash
pip install --no-build-isolation --no-deps -e .
```

If a fresh offline venv does not contain `setuptools`, use the bootstrap installer:
```bash
python3 scripts/offline_editable_install.py --venv .venv-offline
```

## Project Rules

- Keep backend and UI decoupled.
- Do not make simulation code depend on Leaflet/UI internals.
- Keep JSON contracts backward compatible unless explicitly versioned.
- Prefer deterministic logic and test coverage for behavior changes.

## Test Commands

Run full test suite:
```bash
pytest -q
```

Coverage baseline is enforced by default during test runs.
- Default minimum: `45%` statements in `airspacesim/`
- Override threshold:
```bash
AIRSPACESIM_MIN_COVERAGE=50 pytest -q
```
- Disable enforcement temporarily:
```bash
AIRSPACESIM_ENFORCE_COVERAGE=0 pytest -q
```

Run specific tests:
```bash
pytest -q tests/test_cli_init.py
pytest -q tests/test_aircraft.py
pytest -q tests/test_route_registry.py
```

## Coding Conventions

- Use clear names and small functions.
- Keep units explicit in identifiers (`speed_kt`, `radius_nm`, `altitude_ft`).
- Raise explicit errors for invalid inputs.
- Add tests for new logic and edge cases.

## Contribution Workflow

1. Create a focused branch.
2. Implement changes with tests.
3. Run `pytest -q`.
4. Update documentation (`README.md`, `documentation.md`, or `docs/*`) when behavior changes.
5. Open PR with:
- summary of changes
- test evidence
- migration notes if contracts changed
