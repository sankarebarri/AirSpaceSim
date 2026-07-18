"""Structured logging for the hosted API.

Key=value single-line records so logs are grep-able locally and parseable
by hosted log pipelines without extra dependencies:

    2026-07-18T16:00:00+0000 level=INFO logger=app.services.retention msg="..."
"""

from __future__ import annotations

import logging

_FORMAT = '%(asctime)s level=%(levelname)s logger=%(name)s msg="%(message)s"'
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once with a structured formatter."""

    resolved_level = getattr(logging, str(level).upper(), logging.INFO)
    logging.basicConfig(
        level=resolved_level,
        format=_FORMAT,
        datefmt=_DATE_FORMAT,
        force=True,
    )
    # Uvicorn's error logger propagates fine; keep access logs at the same
    # level so request lines appear in hosted logs too.
    logging.getLogger("uvicorn.access").setLevel(resolved_level)
