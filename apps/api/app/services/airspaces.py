"""Airspace package discovery service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..airspace_packages import (
    normalize_package_manifest,
    package_manifest_paths,
    read_json_object,
)
from ..paths import AIRSPACES_ROOT


def list_airspace_packages(airspaces_root: Path = AIRSPACES_ROOT) -> list[dict[str, Any]]:
    """Return normalized package manifests from the configured airspaces root."""

    packages = []
    for manifest_path in package_manifest_paths(airspaces_root):
        manifest = read_json_object(manifest_path)
        if manifest is None:
            continue
        normalized = normalize_package_manifest(manifest, manifest_path.parent)
        if normalized is not None:
            packages.append(normalized)
    return packages
