import sys

from loguru import logger


def setup_logging(level: str = "INFO", async_logging: bool = True):
    """Configure loguru logger with readable format."""

    logger.remove()

    # Format: timestamp | LEVEL | module:function:line | message
    log_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        level=level,
        format=log_format,
        enqueue=async_logging,
        backtrace=False,
        diagnose=False,
        colorize=True,
    )

    return logger
