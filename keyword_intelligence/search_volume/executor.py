"""Batch execution abstractions for Search Volume API calls."""

from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger

from keyword_intelligence.search_volume.models import KeywordVolume
from keyword_intelligence.search_volume.providers.base import SearchVolumeProvider


class BatchExecutor(ABC):
    """Abstract interface for executing batch requests against a provider."""

    @abstractmethod
    def execute(
        self, provider: SearchVolumeProvider, keyword_batches: list[list[str]]
    ) -> tuple[dict[str, KeywordVolume], list[Exception]]:
        """Execute the batches using the given provider.

        Args:
            provider: The resolved provider to call.
            keyword_batches: Pre-chunked lists of keywords.

        Returns:
            A tuple containing:
            1. Merged dictionary of all resolved KeywordVolumes.
            2. List of exceptions encountered (if any).
        """
        pass


class SequentialBatchExecutor(BatchExecutor):
    """Executes batches one by one synchronously (default for Phase 3B)."""

    def execute(
        self, provider: SearchVolumeProvider, keyword_batches: list[list[str]]
    ) -> tuple[dict[str, KeywordVolume], list[Exception]]:
        """Run batches sequentially."""
        all_results: dict[str, KeywordVolume] = {}
        exceptions: list[Exception] = []

        total_batches = len(keyword_batches)

        for i, batch in enumerate(keyword_batches, 1):
            logger.debug(
                f"Executing batch {i}/{total_batches} ({len(batch)} keywords) via {provider.provider_name}"
            )
            try:
                # The provider is expected to handle its own rate-limit backoffs internally,
                # or we could add a standard backoff here in the future.
                results = provider.fetch(batch)
                all_results.update(results)
            except Exception as e:
                logger.error(
                    f"Batch {i} failed on provider {provider.provider_name}: {e}"
                )
                exceptions.append(e)

        return all_results, exceptions
