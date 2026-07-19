"""Blocking strategy interface for fuzzy matching optimization."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BlockingStrategy(ABC):
    """Interface for bucketing keywords to avoid O(n^2) comparisons."""

    @abstractmethod
    def create_blocks(self, keywords: list[str]) -> dict[str, list[str]]:
        """Group keywords into blocks that should be compared against each other.

        Args:
            keywords: The list of keywords to block.

        Returns:
            A dictionary mapping block keys to a list of keywords in that block.
        """
        pass


class PrefixBlocking(BlockingStrategy):
    """Blocks keywords by their first N characters.

    Time Complexity: O(N) to build blocks.
    Space Complexity: O(N).
    """

    def __init__(self, prefix_length: int = 1) -> None:
        self.prefix_length = prefix_length

    def create_blocks(self, keywords: list[str]) -> dict[str, list[str]]:
        blocks: dict[str, list[str]] = {}
        for kw in keywords:
            if not kw:
                continue
            key = kw[: self.prefix_length].lower()
            blocks.setdefault(key, []).append(kw)
        return blocks


class LengthBlocking(BlockingStrategy):
    """Blocks keywords by string length window (e.g. +/- 1 char).

    Keywords of length L are placed in block L, but during matching
    we must compare block L with blocks L, L-1, L+1. For simplicity,
    this implementation just returns strict length buckets, and the
    strategy will handle the windowing.

    Time Complexity: O(N) to build blocks.
    Space Complexity: O(N).
    """

    def create_blocks(self, keywords: list[str]) -> dict[str, list[str]]:
        blocks: dict[str, list[str]] = {}
        for kw in keywords:
            if not kw:
                continue
            key = str(len(kw))
            blocks.setdefault(key, []).append(kw)
        return blocks
