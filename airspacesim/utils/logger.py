"""Logger convenience wrapper for consistent app logger access."""

from airspacesim.utils.logging_config import default_logger


def get_logger():
    """Return the default AirSpaceSim logger."""
    return default_logger
