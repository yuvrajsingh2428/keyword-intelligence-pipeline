"""Caching abstraction for Search Volume Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from keyword_intelligence.search_volume.models import KeywordVolume


class SearchVolumeCache(ABC):
    """Abstract interface for caching search volume data."""

    @abstractmethod
    def get(self, keyword: str) -> KeywordVolume | None:
        """Retrieve the cached volume for a keyword.

        Args:
            keyword: The keyword string.

        Returns:
            The KeywordVolume if found, else None.
        """
        pass

    @abstractmethod
    def put(self, keyword: str, volume: KeywordVolume) -> None:
        """Store the volume for a keyword in the cache.

        Args:
            keyword: The keyword string.
            volume: The KeywordVolume to cache.
        """
        pass

    @abstractmethod
    def contains(self, keyword: str) -> bool:
        """Check if a keyword exists in the cache.

        Args:
            keyword: The keyword string.

        Returns:
            True if cached, False otherwise.
        """
        pass


class InMemorySearchVolumeCache(SearchVolumeCache):
    """O(1) in-memory cache for search volume metrics."""

    def __init__(self) -> None:
        """Initialize the in-memory dictionary cache."""
        self._cache: dict[str, KeywordVolume] = {}

    def get(self, keyword: str) -> KeywordVolume | None:
        """Retrieve from the internal dictionary."""
        return self._cache.get(keyword)

    def put(self, keyword: str, volume: KeywordVolume) -> None:
        """Store in the internal dictionary."""
        self._cache[keyword] = volume

    def contains(self, keyword: str) -> bool:
        """Check the internal dictionary keys."""
        return keyword in self._cache
