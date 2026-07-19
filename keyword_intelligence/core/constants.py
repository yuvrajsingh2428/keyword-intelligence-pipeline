"""Core application constants and configuration defaults."""

from enum import Enum

PIPELINE_VERSION = "1.0.0"


class AppEnvironment(str, Enum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogFormat(str, Enum):
    """Supported log output formats."""

    CONSOLE = "console"
    JSON = "json"


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StageType(str, Enum):
    """Standard pipeline stage identifiers."""

    LOADER = "LOADER"
    VALIDATOR = "VALIDATOR"
    PREPROCESSOR = "PREPROCESSOR"
    BUSINESS_CONTEXT = "BUSINESS_CONTEXT"
    DUPLICATE_DETECTION = "duplicate_detection"
    SEARCH_VOLUME = "SEARCH_VOLUME"
    AI_CLASSIFICATION = "AI_CLASSIFICATION"
    REPORTING = "REPORTING"
