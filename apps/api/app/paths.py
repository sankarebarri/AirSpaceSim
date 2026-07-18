"""Shared filesystem paths for the hosted API."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRSPACES_ROOT = PROJECT_ROOT / "airspaces"
CONTENT_ROOT = PROJECT_ROOT / "content"
