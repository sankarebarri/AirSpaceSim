import logging
import logging.handlers
import os
import sys


def setup_logger(name, log_file=None, level=logging.DEBUG):
    """
    Setup a logger with optional file logging and console output.

    :param name: Logger name.
    :param log_file: Optional file to write logs to.
    :param level: Logger level.
    :return: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding='utf-8',
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Reconfigure sys.stdout for UTF-8 if supported.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

# Intentionally configured without a file path by default to avoid import-time
# filesystem side effects. Callers can use setup_logger(..., log_file=...) when needed.
default_logger = setup_logger("airspacesim")
