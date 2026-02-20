import ast
from pathlib import Path


FORBIDDEN_IMPORT_PREFIXES = (
    "airspacesim.static",
    "airspacesim.templates",
    "airspacesim.map",
    "flask",
    "django",
    "fastapi",
    "leaflet",
)


def _iter_core_python_files():
    root = Path(__file__).resolve().parents[1] / "airspacesim" / "core"
    for path in root.rglob("*.py"):
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
