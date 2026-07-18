"""Centralized logging configuration using Loguru.

Configures Loguru sinks based on application settings:
- Console sink: Always active. Human-readable in development, JSON in production.
- File sink: Optional. Rotated and retained based on settings.

Usage:
    This module is called once at application startup. Individual modules
    should use the logger factory in keyword_intelligence.core.logger.

    from keyword_intelligence.config.logging_config import setup_logging
    setup_logging(settings)
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from loguru import logger

from keyword_intelligence.constants import LOG_FILE_NAME

if TYPE_CHECKING:
    from keyword_intelligence.config.settings import Settings


# Loguru format strings
_CONSOLE_FORMAT: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

_JSON_FORMAT: str = (
    '{{"timestamp":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
    '"level":"{level}",'
    '"module":"{module}",'
    '"function":"{function}",'
    '"line":{line},'
    '"message":"{message}"}}'
)


def setup_logging(settings: Settings) -> None:
    """Configure application logging based on settings.

    Removes all default Loguru handlers and configures new sinks
    based on the application settings. Should be called exactly
    once during application startup.

    Args:
        settings: The validated application settings instance.
    """
    # Remove default Loguru handler to start clean
    logger.remove()

    # --- Console Sink (always active) ---
    if settings.log_format == "json":
        logger.add(
            sys.stderr,
            format=_JSON_FORMAT,
            level=settings.log_level,
            colorize=False,
            serialize=False,  # We use our own JSON format string
        )
    else:
        logger.add(
            sys.stderr,
            format=_CONSOLE_FORMAT,
            level=settings.log_level,
            colorize=True,
        )

    # --- File Sink (optional) ---
    if settings.log_file_enabled:
        log_file = settings.logs_dir / LOG_FILE_NAME

        # Ensure logs directory exists
        settings.logs_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_file),
            format=_CONSOLE_FORMAT,
            level=settings.log_level,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression="zip",
            encoding="utf-8",
        )

    logger.info(
        "Logging configured",
        level=settings.log_level,
        format=settings.log_format,
        file_enabled=settings.log_file_enabled,
    )
