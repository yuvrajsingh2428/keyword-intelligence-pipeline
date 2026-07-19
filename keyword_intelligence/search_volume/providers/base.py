"""Base provider interface for search volume fetching."""

from __future__ import annotations

from abc import ABC, abstractmethod

from keyword_intelligence.search_volume.models import (
    KeywordVolume,
    ProviderCapabilities,
)


class SearchVolumeProvider(ABC):
    """Abstract interface for a search volume data provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def provider_version(self) -> str:
        """Version of this provider implementation."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Priority of this provider during resolution (lower is higher priority)."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Capabilities supported by this provider."""
        pass

    @abstractmethod
    def fetch(self, keywords: list[str]) -> dict[str, KeywordVolume]:
        """Fetch search volume data for a batch of keywords.

        Args:
            keywords: A batch of keywords up to the provider's max_batch_size.

        Returns:
            A dictionary mapping keywords to their respective KeywordVolume.
            Any keyword missing from the dict is considered unresolved.
        """
        pass
