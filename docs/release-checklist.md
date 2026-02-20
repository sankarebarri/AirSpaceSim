# Release Checklist

## Before Version Bump

- [ ] Roadmap-critical items for target milestone are complete.
- [ ] Contract changes are versioned and documented.
- [ ] `README.md` and `documentation.md` reflect current behavior.
- [ ] `CHANGELOG.md` updated under `[Unreleased]`.

## Validation

- [ ] Full tests pass:
  - `pytest -q`
- [ ] Packaging artifacts build:
  - `python3 setup.py sdist bdist_wheel`
- [ ] Wheel contains required runtime assets (templates/static/data).
- [ ] Fresh install smoke test:
  - `pip install --no-index --find-links dist airspacesim`
- [ ] `airspacesim init` works in fresh directory.

## Release Preparation

- [ ] Move `[Unreleased]` entries to new version heading in `CHANGELOG.md`.
- [ ] Update version in `pyproject.toml` and any mirrored metadata.
- [ ] Tag release in VCS.
- [ ] Publish artifacts.

## Post-Release

- [ ] Create a new `[Unreleased]` section in `CHANGELOG.md`.
- [ ] Update roadmap status where applicable.

