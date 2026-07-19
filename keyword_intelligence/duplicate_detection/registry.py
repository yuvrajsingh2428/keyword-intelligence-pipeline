"""Registry for managing duplicate detection strategies."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyword_intelligence.duplicate_detection.strategies.base import (
        DuplicateDetectionStrategy,
    )


class DuplicateDetectionRegistry:
    """Registry responsible for registering and ordering detection strategies."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._strategies: list[DuplicateDetectionStrategy] = []

    def register(self, strategy: DuplicateDetectionStrategy) -> None:
        """Register a strategy."""
        self._strategies.append(strategy)

    def get_strategies(self) -> list[DuplicateDetectionStrategy]:
        """Return the list of registered strategies sorted by priority."""
        return sorted(self._strategies, key=lambda s: s.priority)
