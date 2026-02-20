"""Configuration helpers for JSON file loading and path resolution."""

import json
from pathlib import Path


def resolve_first_existing_path(*candidates):
    """Return first existing path from candidates or None."""
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    return None


def load_json(path):
    """Load a JSON file using UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
