"""Centralized logging utility for Google Flow Image Generation Automation."""

import os
import sys
import logging
from pathlib import Path

# Base workspace directory
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "execution.log"


def setup_logger(name: str = "flow_automation", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a standardized structured logger.
    
    Ensures zero log file pollution in workspace root by writing exclusively
    to console output and `logs/execution.log`.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger is already initialized
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Formatter for structured logs
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Stream Handler (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Dedicated git-ignored log file inside logs/)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as err:
        sys.stderr.write(f"Warning: Could not create file logger at {LOG_FILE}: {err}\n")

    return logger


# Default logger instance
logger = setup_logger()
