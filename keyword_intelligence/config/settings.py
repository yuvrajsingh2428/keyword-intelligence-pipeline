"""Application settings with typed environment variable loading.

Uses Pydantic BaseSettings to provide validated, typed access to all
configuration values. Environment variables are loaded from .env files
and the system environment, with sensible defaults for local development.

Usage:
    from keyword_intelligence.config import get_settings

    settings = get_settings()
    print(settings.app_env)
    print(settings.log_level)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory (where .env lives)
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    All settings have sensible defaults for local development. Production
    deployments should override values via environment variables or a
    secrets manager.

    Attributes:
        app_env: The deployment environment identifier.
        app_title: Display title for the application UI.
        debug: Enable debug mode for verbose output and development features.
        log_level: Minimum severity level for log output.
        log_format: Log output format — 'console' for human-readable,
            'json' for structured production logs.
        log_file_enabled: Whether to write logs to the logs/ directory.
        log_rotation: Log file rotation threshold (e.g., '10 MB', '1 day').
        log_retention: How long to keep rotated log files (e.g., '7 days').
    """

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application Core ---
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment identifier.",
    )
    app_title: str = Field(
        default="Keyword Intelligence Pipeline",
        description="Display title for the application UI and metadata.",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode for verbose output.",
    )

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Minimum severity level for log output.",
    )
    log_format: Literal["console", "json"] = Field(
        default="console",
        description="Log output format: 'console' or 'json'.",
    )
    log_file_enabled: bool = Field(
        default=False,
        description="Whether to write logs to the logs/ directory.",
    )
    log_rotation: str = Field(
        default="10 MB",
        description="Log file rotation threshold.",
    )
    log_retention: str = Field(
        default="7 days",
        description="Retention period for rotated log files.",
    )

    @property
    def is_production(self) -> bool:
        """Check if the application is running in production."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if the application is running in development."""
        return self.app_env == "development"

    @property
    def logs_dir(self) -> Path:
        """Return the path to the logs directory."""
        return _PROJECT_ROOT / "logs"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance.

    Uses lru_cache to ensure the settings are loaded and validated
    exactly once during application lifecycle. Call this function
    instead of constructing Settings() directly.

    Returns:
        The validated application settings.
    """
    return Settings()
