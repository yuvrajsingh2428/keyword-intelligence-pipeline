"""Placeholder Google Ads API provider."""

from __future__ import annotations

from keyword_intelligence.search_volume.models import (
    KeywordVolume,
    ProviderCapabilities,
)
from keyword_intelligence.search_volume.providers.base import SearchVolumeProvider


class GoogleAdsProvider(SearchVolumeProvider):
    """Placeholder for future Google Ads API integration."""

    @property
    def provider_name(self) -> str:
        return "google_ads"

    @property
    def provider_version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 10

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            max_batch_size=10000,
            supports_parallel=False,  # often rate-limited rigidly
            supports_retry=True,
            supports_location=True,
            supports_language=True,
            supports_historical_data=True,
        )

    def fetch(self, keywords: list[str]) -> dict[str, KeywordVolume]:
        raise NotImplementedError("Google Ads provider is not yet implemented.")
