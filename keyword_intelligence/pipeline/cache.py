"""Cache provider abstraction for pipeline deduplication."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CacheProvider(ABC):
    """Interface for caching pipeline execution results by dataset checksum."""

    @abstractmethod
    def get(self, checksum: str) -> Any | None:
        """Retrieve a cached result by checksum.

        Args:
            checksum: SHA256 checksum of the dataset.

        Returns:
            The cached object if it exists, otherwise None.
        """
        pass

    @abstractmethod
    def put(self, checksum: str, result: Any) -> None:
        """Store a result in the cache by checksum.

        Args:
            checksum: SHA256 checksum of the dataset.
            result: The object to cache.
        """
        pass

    @abstractmethod
    def exists(self, checksum: str) -> bool:
        """Check if a cached result exists for the checksum.

        Args:
            checksum: SHA256 checksum of the dataset.

        Returns:
            True if cached, False otherwise.
        """
        pass
