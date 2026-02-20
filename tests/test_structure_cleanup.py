import logging

from airspacesim.routes.manager import RouteManager as CanonicalRouteManager
from airspacesim.routes.route_manager import RouteManager as ShimRouteManager
from airspacesim.utils.logging_config import setup_logger


def test_route_manager_shim_points_to_canonical_class():
    assert ShimRouteManager is CanonicalRouteManager


def test_setup_logger_without_file_has_no_file_handler():
    logger_name = "airspacesim.test.no_file_handler"
    logger = setup_logger(logger_name, log_file=None)
    assert logger.name == logger_name
    assert all(not isinstance(handler, logging.FileHandler) for handler in logger.handlers)
