"""Loguru logging setup."""

import sys

from loguru import logger


def setup_logging(debug: bool = True) -> None:
    logger.remove()
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
    )
