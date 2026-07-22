"""Application settings with typed environment variable loading.

Uses Pydantic BaseSettings to provide validated, typed access to all
configuration values. Environment variables are loaded from .env files
and the system environment, with sensible defaults for local development.

Usage:
    from keyword_intelligence.config import get_settings

    settings = get_settings()
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory (where .env lives)
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

# Determine active environment for configuration layering
_ACTIVE_ENV = os.getenv("APP_ENV", "development").lower()
_ENV_FILES = (
    str(_PROJECT_ROOT / ".env"),
    str(_PROJECT_ROOT / f".env.{_ACTIVE_ENV}"),
)


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
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Search Volume ---
    search_volume_provider: str = Field(
        default="mock",
        description="Provider to use for fetching search volume",
    )
    search_volume_batch_size: int = Field(
        default=500,
        description="Default batch size for search volume requests",
    )

    # --- AI Intelligence ---
    ai_provider: str = Field(
        default="mock",
        description="Provider to use for AI classification",
    )
    ai_batch_size: int = Field(
        default=100,
        description="Default batch size for AI classification requests",
    )
    ai_model: str = Field(
        default="gemini-3.5-flash",
        description="AI model to use for classification",
    )
    ai_timeout: float = Field(
        default=60.0,
        description="Timeout in seconds for AI API requests",
    )
    google_gemini_api_key_1: str | None = Field(
        default=None,
        description="API key 1 for Google Gemini",
    )
    google_gemini_api_key_2: str | None = Field(
        default=None,
        description="API key 2 for Google Gemini",
    )
    google_gemini_api_key_3: str | None = Field(
        default=None,
        description="API key 3 for Google Gemini",
    )
    google_gemini_api_key_4: str | None = Field(
        default=None,
        description="API key 4 for Google Gemini",
    )
    google_gemini_api_key_5: str | None = Field(
        default=None,
        description="API key 5 for Google Gemini",
    )
    open_router_api_key: str | None = Field(
        default=None,
        description="API key for OpenRouter",
    )
    open_router_base_url: str = Field(
        default="https://openrouter.ai/api/v1/chat/completions",
        description="Base URL for OpenRouter API",
    )
    open_router_model: str = Field(
        default="google/gemini-2.5-flash",
        description="Model to use for OpenRouter fallback",
    )
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama REST API base URL",
    )

    # --- Business Context ---
    business_context_provider: str = Field(
        default="website",
        description="Provider for business context gathering",
    )
    business_context_max_pages: int = Field(
        default=15,
        description="Maximum number of pages to fetch per website",
    )
    business_context_crawl_timeout: float = Field(
        default=15.0,
        description="Timeout per HTTP request during context collection",
    )
    business_context_cache_ttl_hours: int = Field(
        default=24,
        description="How long to cache the generated business profile",
    )
    business_context_min_family_confidence: float = Field(
        default=2.0,
        description="Minimum confidence threshold for product families",
    )
    business_context_min_brand_confidence: float = Field(
        default=1.0,
        description="Minimum confidence threshold for brands",
    )
    business_context_min_alias_confidence: float = Field(
        default=1.0,
        description="Minimum confidence threshold for aliases",
    )
    business_context_min_synonym_confidence: float = Field(
        default=1.0,
        description="Minimum confidence threshold for synonyms",
    )

    # --- Reporting ---
    report_format: str = Field(
        default="json",
        description="Default export format: csv, excel, json.",
    )
    report_output_dir: str = Field(
        default="reports",
        description="Directory for exported report files.",
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

    # --- Pipeline & Orchestration ---
    stop_on_error: bool = Field(
        default=True,
        description="Whether to halt the pipeline immediately when a stage fails.",
    )
    max_stage_retries: int = Field(
        default=3,
        description="Maximum number of times to retry a failing pipeline stage.",
    )
    retry_delay_ms: int = Field(
        default=1000,
        description="Delay in milliseconds between stage retries.",
    )

    # --- Preprocessing ---
    enable_lowercase: bool = Field(
        default=True,
        description="Convert keywords to lowercase during preprocessing.",
    )
    enable_trim_whitespace: bool = Field(
        default=True,
        description="Trim leading and trailing whitespace from keywords.",
    )
    enable_deduplication: bool = Field(
        default=True,
        description="Drop exact duplicate keywords during preprocessing.",
    )
    enable_remove_empty_rows: bool = Field(
        default=True,
        description="Remove rows with empty keywords during preprocessing.",
    )
    enable_normalize_spaces: bool = Field(
        default=True,
        description="Replace multiple interior spaces with a single space.",
    )

    # --- Duplicate Detection ---
    duplicate_exact_enabled: bool = Field(
        default=True,
        description="Enable exact match duplicate detection.",
    )
    duplicate_normalized_enabled: bool = Field(
        default=True,
        description="Enable normalized match duplicate detection.",
    )
    duplicate_fuzzy_enabled: bool = Field(
        default=True,
        description="Enable fuzzy match duplicate detection.",
    )
    duplicate_semantic_enabled: bool = Field(
        default=False,
        description="Enable semantic match duplicate detection (placeholder).",
    )
    duplicate_fuzzy_threshold: float = Field(
        default=90.0,
        description="Minimum similarity score (0-100) for fuzzy matching.",
    )
    duplicate_max_group_size: int = Field(
        default=50,
        description="Maximum number of keywords allowed in a single duplicate group.",
    )
    duplicate_min_confidence: float = Field(
        default=80.0,
        description="Minimum final confidence score to combine a duplicate group.",
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
