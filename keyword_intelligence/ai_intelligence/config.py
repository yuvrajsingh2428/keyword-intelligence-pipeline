"""Configuration mapping for AI Engine."""

from __future__ import annotations

from keyword_intelligence.config.settings import Settings


class AIEngineConfig:
    """Extracts and validates AI configuration from global Settings."""

    def __init__(self, provider: str, batch_size: int) -> None:
        self.provider = provider
        self.batch_size = batch_size

    @classmethod
    def from_settings(cls, settings: Settings) -> AIEngineConfig:
        """Create AIEngineConfig from global settings."""
        return cls(
            provider=settings.ai_provider,
            batch_size=settings.ai_batch_size,
        )
