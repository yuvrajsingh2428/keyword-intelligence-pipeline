"""Configuration adapter for Duplicate Detection Engine."""

from __future__ import annotations

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.models.base import AppBaseModel


class DuplicateDetectionConfig(AppBaseModel):
    """Localized configuration for the Duplicate Detection Engine."""

    exact_enabled: bool = True
    normalized_enabled: bool = True
    fuzzy_enabled: bool = True
    semantic_enabled: bool = False

    fuzzy_threshold: float = 90.0
    max_group_size: int = 50
    min_confidence: float = 80.0

    @classmethod
    def from_settings(cls, settings: Settings) -> DuplicateDetectionConfig:
        """Create engine config from the global application settings."""
        return cls(
            exact_enabled=settings.duplicate_exact_enabled,
            normalized_enabled=settings.duplicate_normalized_enabled,
            fuzzy_enabled=settings.duplicate_fuzzy_enabled,
            semantic_enabled=settings.duplicate_semantic_enabled,
            fuzzy_threshold=settings.duplicate_fuzzy_threshold,
            max_group_size=settings.duplicate_max_group_size,
            min_confidence=settings.duplicate_min_confidence,
        )
