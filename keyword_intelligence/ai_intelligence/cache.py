"""Caching abstraction for the AI Engine."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from keyword_intelligence.ai_intelligence.models import AIClassificationResult


class AICache(ABC):
    """Abstract interface for caching AI classifications."""

    def generate_key(
        self, company: str, keyword: str, provider: str, prompt_version: str
    ) -> str:
        """Generate a SHA256 deterministic cache key.

        Args:
            company: The company name.
            keyword: The keyword string.
            provider: The provider name.
            prompt_version: The version string of the prompt.

        Returns:
            SHA256 hex digest.
        """
        raw = f"{company}|{keyword}|{provider}|{prompt_version}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @abstractmethod
    def get(self, key: str) -> AIClassificationResult | None:
        """Retrieve the cached classification for a key."""
        pass

    @abstractmethod
    def put(self, key: str, result: AIClassificationResult) -> None:
        """Store the classification for a key in the cache."""
        pass


class InMemoryAICache(AICache):
    """O(1) in-memory cache for AI classifications."""

    def __init__(self) -> None:
        self._cache: dict[str, AIClassificationResult] = {}

    def get(self, key: str) -> AIClassificationResult | None:
        return self._cache.get(key)

    def put(self, key: str, result: AIClassificationResult) -> None:
        self._cache[key] = result
