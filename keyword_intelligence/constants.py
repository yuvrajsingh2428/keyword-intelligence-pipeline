"""Application-wide constants for the Keyword Intelligence Pipeline.

Defines enumerations, string literals, and magic values used across
modules. Using constants from this module (rather than raw strings)
enables IDE autocompletion, refactoring safety, and a single source
of truth for shared values.

Usage:
    from keyword_intelligence.constants import Environment, LogFormat

    if settings.app_env == Environment.PRODUCTION:
        ...
"""

from __future__ import annotations

from enum import StrEnum, unique


@unique
class Environment(StrEnum):
    """Application deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@unique
class LogFormat(StrEnum):
    """Supported log output formats."""

    CONSOLE = "console"
    JSON = "json"


@unique
class LogLevel(StrEnum):
    """Standard Python log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Application Defaults
# ---------------------------------------------------------------------------

DEFAULT_LOG_LEVEL: str = LogLevel.INFO
"""Default log level when not specified via environment."""

DEFAULT_LOG_FORMAT: str = LogFormat.CONSOLE
"""Default log format — human-readable console output."""

DEFAULT_LOG_ROTATION: str = "10 MB"
"""Default log file rotation threshold."""

DEFAULT_LOG_RETENTION: str = "7 days"
"""Default retention period for rotated log files."""

# ---------------------------------------------------------------------------
# File & Directory Names
# ---------------------------------------------------------------------------

LOGS_DIRECTORY: str = "logs"
"""Name of the runtime logs directory."""

LOG_FILE_NAME: str = "app.log"
"""Default log file name within the logs directory."""

ASSETS_DIRECTORY: str = "assets"
"""Name of the static assets directory."""

ENV_FILE: str = ".env"
"""Name of the local environment override file."""

# ---------------------------------------------------------------------------
# UI Constants
# ---------------------------------------------------------------------------

SIDEBAR_TITLE: str = "⚙️ Navigation"
"""Sidebar heading displayed in the Streamlit UI."""

DASHBOARD_TITLE: str = "📊 Dashboard"
"""Main dashboard page title."""

PHASE_LABEL: str = "Phase 1 — Project Foundation"
"""Current implementation phase label."""
