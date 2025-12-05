#!/usr/bin/env python3
"""
Centralized logging configuration for the SchemesSG data pipeline.
All modules should use this configuration to ensure consistent logging to both terminal and file.
"""

import sys
from datetime import datetime
from pathlib import Path
from loguru import logger

# Global variable to track if logging has been initialized
_logging_initialized = False
_audit_log_file = None

def setup_logging(log_file_name: str = None, log_dir: str = None):
    """
    Setup logging configuration with both terminal and file output.

    Args:
        log_file_name: Custom name for the log file (optional)
        log_dir: Directory to save log files (optional, defaults to current directory)

    Returns:
        str: Path to the created audit log file
    """
    global _logging_initialized, _audit_log_file

    # Remove any existing handlers
    logger.remove()

    # Create audit log filename with timestamp
    if log_file_name:
        audit_log_file = log_file_name
    else:
        now = datetime.now()
        audit_log_file = f"audit_log_{now.strftime('%Y-%m-%d_%H:%M:%S')}.log"

    # Set log directory
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        audit_log_file = str(log_path / audit_log_file)
    else:
        audit_log_file = str(Path.cwd() / audit_log_file)

    # Add terminal handler with colors
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )

    # Add file handler for audit log (no colors in file)
    logger.add(
        audit_log_file,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        backtrace=True,
        rotation="10 MB",  # Rotate if file gets too large
        retention="30 days",  # Keep logs for 30 days
    )

    # Log the audit file location
    logger.info(f"Audit log will be saved to: {audit_log_file}")

    _logging_initialized = True
    _audit_log_file = audit_log_file

    return audit_log_file

def get_audit_log_file():
    """Get the current audit log file path."""
    return _audit_log_file

def is_logging_initialized():
    """Check if logging has been initialized."""
    return _logging_initialized

def ensure_logging_setup():
    """
    Ensure logging is set up. If not initialized, set it up with default settings.
    This is useful for modules that might be imported before logging is explicitly set up.
    If logging is already initialized, do nothing to avoid creating duplicate log files.
    """
    # Check if logging is already initialized by checking if there are any handlers
    if _logging_initialized or len(logger._core.handlers) > 0:
        # Logging is already set up, do nothing to avoid creating duplicate log files
        return

    setup_logging()
