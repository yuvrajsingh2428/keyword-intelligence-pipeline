"""Configuration management for the Keyword Intelligence Pipeline.

Provides centralized, typed access to all application settings loaded
from environment variables and .env files.

Usage:
    from keyword_intelligence.config import Settings, get_settings

    settings = get_settings()
"""

from keyword_intelligence.config.settings import Settings, get_settings

__all__: list[str] = ["Settings", "get_settings"]
