import sys

from loguru import logger


def setup_logging(level: str = "INFO", async_logging: bool = True):
    """Configure loguru logger.
    Disable backtrace and diagnose for better performance.
    Set log level to DEBUG in development."""

    logger.remove()

    logger.add(
        sys.stderr,
        level=level,
        enqueue=async_logging,
        backtrace=False,
        diagnose=False,
    )

    return logger
