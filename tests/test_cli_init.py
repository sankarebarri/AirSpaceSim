from airspacesim.cli.commands import initialize_project


EXPECTED_FILES = [
    "templates/map.html",
    "static/js/map_renderer.js",
    "static/js/aircraft_simulation.js",
    "static/js/ui_runtime.js",
    "static/css/map_styles.css",
    "static/icons/circle.svg",
    "static/icons/triangle_9.svg",
    "data/airspace_config.json",
    "data/map_config.v1.json",
    "data/airspace_data.json",
    "data/scenario_airspace.v1.json",
    "data/scenario.v0.1.json",
    "data/scenario_aircraft.v1.json",
    "data/inbox_events.v1.json",
    "data/render_profile.v1.json",
    "data/aircraft_data.json",
    "data/aircraft_state.v1.json",
    "data/trajectory.v0.1.json",
    "data/ui_runtime.v1.json",
    "data/aircraft_ingest.json",
    "examples/example_simulation.py",
    "examples/interoperability_export.py",
]


def test_initialize_project_creates_expected_structure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    initialize_project()

    for rel_path in EXPECTED_FILES:
        assert (tmp_path / rel_path).exists(), f"Missing {rel_path}"


def test_initialize_project_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    initialize_project()
    # Run again to ensure existing files are skipped instead of failing.
    initialize_project()

    for rel_path in EXPECTED_FILES:
        assert (tmp_path / rel_path).exists(), f"Missing {rel_path} after second run"


def test_initialized_map_runtime_references_are_coherent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    initialize_project()

    map_html = (tmp_path / "templates/map.html").read_text(encoding="utf-8")
    map_renderer_js = (tmp_path / "static/js/map_renderer.js").read_text(
        encoding="utf-8"
    )
    aircraft_js = (tmp_path / "static/js/aircraft_simulation.js").read_text(
        encoding="utf-8"
    )
    runtime_js = (tmp_path / "static/js/ui_runtime.js").read_text(encoding="utf-8")

    # Avoid duplicate renderer initialization: renderer is imported by aircraft_simulation.js.
    assert "../static/js/map_renderer.js" not in map_html
    assert "../static/js/aircraft_simulation.js" in map_html

    # Core runtime data files used by JS polling/config loading must exist after init.
    assert (tmp_path / "data/airspace_config.json").exists()
    assert (tmp_path / "data/map_config.v1.json").exists()
    assert (tmp_path / "data/aircraft_state.v1.json").exists()
    assert (tmp_path / "data/ui_runtime.v1.json").exists()
    assert (tmp_path / "data/aircraft_data.json").exists()

    # Icon assets required by configured markers/defaults should exist.
    assert (tmp_path / "static/icons/triangle_9.svg").exists()
    assert (tmp_path / "static/icons/circle.svg").exists()
    assert (tmp_path / "static/icons/vor.svg").exists()

    # Sanity checks for deterministic data path resolution from static/js module location.
    assert 'from "./ui_runtime.js"' in map_renderer_js
    assert 'new URL("../../data/", import.meta.url)' in runtime_js
    assert 'new URL("map_config.v1.json", DATA_BASE_URL)' in map_renderer_js
    assert 'new URL("airspace_config.json", DATA_BASE_URL)' in map_renderer_js
    assert 'from "./ui_runtime.js"' in aircraft_js
    assert 'new URL("aircraft_state.v1.json", DATA_BASE_URL)' in aircraft_js
    assert 'new URL("aircraft_data.json", DATA_BASE_URL)' in aircraft_js
