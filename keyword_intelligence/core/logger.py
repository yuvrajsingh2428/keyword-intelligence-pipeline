"""Logger factory for the Keyword Intelligence Pipeline.

Provides a single import point for obtaining named loggers. All modules
should use get_logger() instead of importing loguru.logger directly,
ensuring consistent logger naming and future flexibility.

Usage:
    from keyword_intelligence.core.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Processing started", keyword_count=42)
"""

from __future__ import annotations

from loguru import logger as _loguru_logger


def get_logger(name: str) -> _loguru_logger.__class__:  # type: ignore[name-defined]
    """Create a contextualized logger instance.

    Returns a Loguru logger bound with the given module name. This
    provides consistent log context across the application and serves
    as an abstraction layer over the underlying logging library.

    Args:
        name: The logger name, typically __name__ of the calling module.

    Returns:
        A Loguru logger instance bound with the module context.
    """
    return _loguru_logger.bind(module_name=name)
