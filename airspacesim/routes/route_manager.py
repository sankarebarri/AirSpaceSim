"""Compatibility wrapper for the canonical RouteManager implementation.

`airspacesim.routes.manager.RouteManager` is the canonical implementation.
This module remains as a thin import shim for backward compatibility.
"""

from airspacesim.routes.manager import RouteManager

__all__ = ["RouteManager"]
