import ast
import sys
from pathlib import Path


FORBIDDEN_IMPORT_PREFIXES = (
    "airspacesim.static",
    "airspacesim.templates",
    "airspacesim.map",
    "apps.api",
    "flask",
    "django",
    "fastapi",
    "sqlalchemy",
    "uvicorn",
    "leaflet",
)

ENGINE_OWNED_PACKAGES = (
    "core",
    "io",
    "routes",
    "simulation",
    "utils",
)


def _iter_core_python_files():
    root = Path(__file__).resolve().parents[1] / "airspacesim" / "core"
    for path in root.rglob("*.py"):
        yield path


def _iter_engine_owned_python_files():
    root = Path(__file__).resolve().parents[1] / "airspacesim"
    yield root / "__init__.py"
    yield root / "settings.py"
    for package_name in ENGINE_OWNED_PACKAGES:
        for path in (root / package_name).rglob("*.py"):
            yield path


def _import_names(node):
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module]
    return []


def test_core_has_no_ui_or_framework_imports():
    violations = []
    for path in _iter_core_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module_name in _import_names(node):
                if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    violations.append((path.name, module_name))
    assert violations == []


def test_engine_owned_modules_have_no_hosted_app_imports():
    violations = []
    for path in _iter_engine_owned_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module_name in _import_names(node):
                if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    violations.append((str(path.relative_to(path.parents[2])), module_name))
    assert violations == []


def test_top_level_engine_import_has_no_hosted_app_dependencies():
    forbidden_loaded_modules = (
        "apps.api",
        "fastapi",
        "sqlalchemy",
        "uvicorn",
    )
    for module_name in list(sys.modules):
        if module_name.startswith(forbidden_loaded_modules):
            sys.modules.pop(module_name, None)

    import airspacesim

    assert airspacesim.AircraftManager is not None
    assert airspacesim.load_scenario_bundle is not None
    assert airspacesim.apply_events_idempotent is not None
    assert not [
        module_name
        for module_name in sys.modules
        if module_name.startswith(forbidden_loaded_modules)
    ]
