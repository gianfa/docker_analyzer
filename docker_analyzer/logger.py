"""Central logging configuration for docker_analyzer
This module provides logging setup that can be used across all project modules.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from docker_analyzer.config import (
    DEFAULT_LOG_FORMAT,
    LOG_BACKUP_COUNT,
    LOG_FILE_PATH,
    LOG_LEVEL,
    LOG_MAX_SIZE,
)


def get_logger(name: str, log_to_file: str = LOG_FILE_PATH) -> logging.Logger:
    """
    Configures and returns a logger instance.

    Parameters
    ----------
    name : str
        Name of the logger, typically the __name__ of the module.
    log_to_file : bool, optional
        Whether to log to a file or just to the console (default is False).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create log formatter based on configuration
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler with rotation
    if len(log_to_file) > 0:
        if not Path(LOG_FILE_PATH).parent.is_dir():
            raise ValueError("Log file directory provided is not valid")
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH, maxBytes=LOG_MAX_SIZE, backupCount=LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
