"""Deterministic mock provider for search volume."""

from __future__ import annotations

import hashlib
import time

from keyword_intelligence.search_volume.models import (
    KeywordVolume,
    ProviderCapabilities,
)
from keyword_intelligence.search_volume.providers.base import SearchVolumeProvider


class MockProvider(SearchVolumeProvider):
    """Mock provider that generates deterministic search volume using MD5 hashing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def provider_version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 100

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            max_batch_size=1000,
            supports_parallel=True,
            supports_retry=True,
            supports_location=False,
            supports_language=False,
            supports_historical_data=False,
        )

    def fetch(self, keywords: list[str]) -> dict[str, KeywordVolume]:
        """Generate deterministic results based on keyword hash."""
        # Simulate small network latency (e.g. 5ms per batch) for metrics
        time.sleep(0.005)

        results: dict[str, KeywordVolume] = {}

        for kw in keywords:
            # Create a stable integer from the string using MD5
            hash_val = int(hashlib.md5(kw.encode("utf-8")).hexdigest(), 16)

            # Deterministic Volume (10 - 500,000)
            volume = 10 + (hash_val % 499990)

            # Deterministic Competition
            comp_mod = hash_val % 100
            if comp_mod < 30:
                competition = "LOW"
            elif comp_mod < 70:
                competition = "MEDIUM"
            else:
                competition = "HIGH"

            # Deterministic CPC (0.05 - 50.00)
            cpc = 0.05 + ((hash_val % 4995) / 100.0)

            results[kw] = KeywordVolume(
                keyword=kw,
                monthly_volume=volume,
                competition=competition,  # type: ignore[arg-type]
                cpc=round(cpc, 2),
                source="mock",
                confidence=100.0,
            )

        return results
