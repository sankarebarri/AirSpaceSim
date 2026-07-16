import logging

from airspacesim.utils.logging_config import setup_logger


def test_route_manager_shim_module_is_removed():
    # 0.2.0 removed the airspacesim.routes.route_manager compatibility shim;
    # airspacesim.routes.manager.RouteManager is the only implementation.
    import importlib

    import pytest

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("airspacesim.routes.route_manager")


def test_setup_logger_without_file_has_no_file_handler():
    logger_name = "airspacesim.test.no_file_handler"
    logger = setup_logger(logger_name, log_file=None)
    assert logger.name == logger_name
    assert all(
        not isinstance(handler, logging.FileHandler) for handler in logger.handlers
    )
