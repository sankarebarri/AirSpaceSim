import logging
import logging.handlers
import os
import sys
from datetime import datetime

def setup_logger(name, log_file, level=logging.DEBUG):
    """
    Setup a logger with a RotatingFileHandler and a StreamHandler.
    Reconfigures sys.stdout for UTF-8 and sets the stream handler to INFO level.
    
    :param name: Logger name.
    :param log_file: File to write logs to.
    :param level: Logging level for the file handler.
    :return: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # Rotating File Handler with UTF-8 encoding.
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
        # Reconfigure sys.stdout for UTF-8 if possible.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    
        # Create a stream handler for console output at INFO level.
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    
    return logger

# Create logs directory if it doesn't exist.
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Generate a unique log file name using the current date and time.
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file_name = os.path.join(LOG_DIR, f"simulation_{timestamp}.log")

default_logger = setup_logger("airspacesim", log_file_name)
