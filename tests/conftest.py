import ast
import os
import sys
from pathlib import Path


MIN_BASELINE_COVERAGE_PERCENT = float(os.getenv("AIRSPACESIM_MIN_COVERAGE", "45.0"))
ENFORCE_COVERAGE = os.getenv("AIRSPACESIM_ENFORCE_COVERAGE", "1") != "0"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = (PROJECT_ROOT / "airspacesim").resolve()

TRACKED_FILES = {}
EXECUTED_LINES = {}


def _statement_lines(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    lines = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and hasattr(node, "lineno"):
            lines.add(node.lineno)
    return lines


def _build_tracked_files():
    tracked = {}
    for path in PACKAGE_ROOT.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        tracked[str(path.resolve())] = _statement_lines(path)
    return tracked


def _trace(frame, event, arg):
    if event != "line":
        return _trace
    filename = str(Path(frame.f_code.co_filename).resolve())
    if filename not in TRACKED_FILES:
        return _trace
    EXECUTED_LINES.setdefault(filename, set()).add(frame.f_lineno)
    return _trace


def pytest_sessionstart(session):
    TRACKED_FILES.clear()
    TRACKED_FILES.update(_build_tracked_files())
    EXECUTED_LINES.clear()


def pytest_runtest_setup(item):
    if ENFORCE_COVERAGE:
        sys.settrace(_trace)


def pytest_runtest_teardown(item, nextitem):
    if ENFORCE_COVERAGE:
        sys.settrace(None)


def pytest_sessionfinish(session, exitstatus):
    if not ENFORCE_COVERAGE:
        return

    total_lines = 0
    covered_lines = 0
    for filename, statements in TRACKED_FILES.items():
        total_lines += len(statements)
        covered_lines += len(statements.intersection(EXECUTED_LINES.get(filename, set())))

    coverage_percent = (covered_lines / total_lines * 100.0) if total_lines else 100.0
    terminal = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminal:
        terminal.write_line(
            f"airspacesim baseline coverage: {coverage_percent:.2f}% ({covered_lines}/{total_lines} statements)"
        )

    if coverage_percent < MIN_BASELINE_COVERAGE_PERCENT:
        session.exitstatus = 1
        if terminal:
            terminal.write_line(
                f"ERROR: baseline coverage {coverage_percent:.2f}% is below required {MIN_BASELINE_COVERAGE_PERCENT:.2f}%"
            )
