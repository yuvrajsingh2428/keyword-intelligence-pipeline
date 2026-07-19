"""Configuration mapping for Search Volume Engine."""

from __future__ import annotations

from keyword_intelligence.config.settings import Settings


class SearchVolumeConfig:
    """Extracts and validates search volume configuration from global Settings."""

    def __init__(self, provider: str, batch_size: int) -> None:
        self.provider = provider
        self.batch_size = batch_size

    @classmethod
    def from_settings(cls, settings: Settings) -> SearchVolumeConfig:
        """Create SearchVolumeConfig from global settings."""
        return cls(
            provider=settings.search_volume_provider,
            batch_size=settings.search_volume_batch_size,
        )
