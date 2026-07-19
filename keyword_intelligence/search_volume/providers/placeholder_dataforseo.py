"""Placeholder DataForSEO API provider."""

from __future__ import annotations

from keyword_intelligence.search_volume.models import (
    KeywordVolume,
    ProviderCapabilities,
)
from keyword_intelligence.search_volume.providers.base import SearchVolumeProvider


class DataForSEOProvider(SearchVolumeProvider):
    """Placeholder for future DataForSEO API integration."""

    @property
    def provider_name(self) -> str:
        return "dataforseo"

    @property
    def provider_version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 20

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            max_batch_size=1000,
            supports_parallel=True,
            supports_retry=True,
            supports_location=True,
            supports_language=True,
            supports_historical_data=False,
        )

    def fetch(self, keywords: list[str]) -> dict[str, KeywordVolume]:
        raise NotImplementedError("DataForSEO provider is not yet implemented.")
