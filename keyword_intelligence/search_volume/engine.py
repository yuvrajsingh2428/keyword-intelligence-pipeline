"""Main engine orchestrating the search volume retrieval process."""

from __future__ import annotations

import time

from loguru import logger

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.search_volume.cache import (
    InMemorySearchVolumeCache,
    SearchVolumeCache,
)
from keyword_intelligence.search_volume.config import SearchVolumeConfig
from keyword_intelligence.search_volume.executor import (
    BatchExecutor,
    SequentialBatchExecutor,
)
from keyword_intelligence.search_volume.models import (
    KeywordVolume,
    ProviderMetrics,
    SearchVolumeResult,
    SearchVolumeStatistics,
)
from keyword_intelligence.search_volume.registry import (
    ProviderRegistry,
    ProviderResolver,
)


class SearchVolumeEngine:
    """High-level facade for fetching search volume data.

    Responsibilities:
    - Check cache
    - Batch remaining keywords
    - Respect provider max batch size
    - Call BatchExecutor
    - Aggregate statistics and update context
    """

    def __init__(
        self,
        settings: Settings,
        cache: SearchVolumeCache | None = None,
        registry: ProviderRegistry | None = None,
        executor: BatchExecutor | None = None,
    ) -> None:
        """Initialize the Search Volume Engine with dependencies."""
        self.config = SearchVolumeConfig.from_settings(settings)

        self.cache = cache or InMemorySearchVolumeCache()

        if registry is None:
            # We initialize default registry if none provided
            registry = ProviderRegistry()
            from keyword_intelligence.search_volume.providers.mock import MockProvider
            from keyword_intelligence.search_volume.providers.placeholder_dataforseo import (
                DataForSEOProvider,
            )
            from keyword_intelligence.search_volume.providers.placeholder_google_ads import (
                GoogleAdsProvider,
            )

            registry.register(MockProvider())
            registry.register(GoogleAdsProvider())
            registry.register(DataForSEOProvider())

        self.resolver = ProviderResolver(registry)
        self.executor = executor or SequentialBatchExecutor()

    def process(self, context: PipelineContext) -> SearchVolumeResult:
        """Process the context DataFrame to append search volume data."""
        logger.info("Starting Search Volume Engine.")
        start_time = time.perf_counter()

        if not context.has_data:
            logger.warning("No data found in context. Skipping Search Volume.")
            return self._empty_result()

        keywords = context.data["keyword"].tolist()
        total_kws = len(keywords)

        # 1. Resolve Provider
        provider = self.resolver.resolve(self.config.provider)

        # Determine actual batch size (cannot exceed provider's limit)
        actual_batch_size = min(
            self.config.batch_size, provider.capabilities.max_batch_size
        )
        if actual_batch_size < self.config.batch_size:
            logger.warning(
                f"Configured batch size ({self.config.batch_size}) exceeds provider "
                f"limit ({provider.capabilities.max_batch_size}). Using provider limit."
            )

        # 2. Check Cache
        keywords_to_fetch: list[str] = []
        resolved_volumes: dict[str, KeywordVolume] = {}

        for kw in keywords:
            cached_vol = self.cache.get(kw)
            if cached_vol:
                resolved_volumes[kw] = cached_vol
            else:
                keywords_to_fetch.append(kw)

        cache_hits = len(resolved_volumes)
        cache_misses = len(keywords_to_fetch)

        logger.info(f"Cache check: {cache_hits} hits, {cache_misses} misses.")

        # 3. Batch creation
        batches: list[list[str]] = []
        for i in range(0, len(keywords_to_fetch), actual_batch_size):
            batches.append(keywords_to_fetch[i : i + actual_batch_size])

        # 4. Execute Batches
        batch_start = time.perf_counter()
        fetched_volumes, exceptions = self.executor.execute(provider, batches)
        batch_duration_ms = (time.perf_counter() - batch_start) * 1000

        # Cache the newly fetched results
        for kw, vol in fetched_volumes.items():
            self.cache.put(kw, vol)
            resolved_volumes[kw] = vol

        # 5. Append to Context DataFrame
        # For simplicity and vectorization, we map the columns
        if not context.data.empty:
            context.data["search_volume"] = context.data["keyword"].map(
                lambda k: (
                    resolved_volumes[k].monthly_volume
                    if k in resolved_volumes
                    else None
                )
            )
            context.data["competition"] = context.data["keyword"].map(
                lambda k: (
                    resolved_volumes[k].competition if k in resolved_volumes else None
                )
            )
            context.data["cpc"] = context.data["keyword"].map(
                lambda k: resolved_volumes[k].cpc if k in resolved_volumes else None
            )

        # 6. Collect Statistics
        total_time_ms = (time.perf_counter() - start_time) * 1000
        resolved_count = len(resolved_volumes)
        unresolved_count = total_kws - resolved_count
        failed_calls = len(exceptions)

        batches_processed = len(batches)
        avg_batch_latency = (
            batch_duration_ms / batches_processed if batches_processed > 0 else 0.0
        )
        provider_success_rate = 100.0
        if batches_processed > 0:
            provider_success_rate = (
                (batches_processed - failed_calls) / batches_processed
            ) * 100.0

        stats = SearchVolumeStatistics(
            total_keywords=total_kws,
            resolved_keywords=resolved_count,
            unresolved_keywords=unresolved_count,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            provider_calls=batches_processed,
            batches_processed=batches_processed,
            failed_provider_calls=failed_calls,
            average_batch_latency_ms=avg_batch_latency,
            average_provider_latency_ms=avg_batch_latency,  # In sequential, they are the same
            provider_success_rate=provider_success_rate,
            execution_time_ms=total_time_ms,
        )

        hit_ratio = (cache_hits / total_kws * 100.0) if total_kws > 0 else 0.0

        provider_metrics = ProviderMetrics(
            provider_name=provider.provider_name,
            provider_version=provider.provider_version,
            batches_processed=batches_processed,
            keywords_processed=len(keywords_to_fetch),
            cache_hit_ratio=hit_ratio,
            average_latency_ms=avg_batch_latency,
        )

        logger.info(
            f"Search Volume Engine finished in {total_time_ms:.2f}ms. "
            f"Resolved {resolved_count}/{total_kws} keywords."
        )
        if unresolved_count > 0:
            context.add_warning(
                "SEARCH_VOLUME",
                "UNRESOLVED_KEYWORDS",
                f"Failed to fetch volume for {unresolved_count} keywords.",
            )

        return SearchVolumeResult(
            keyword_volumes=resolved_volumes,
            statistics=stats,
            provider_used=provider.provider_name,
            execution_metrics={provider.provider_name: provider_metrics},
        )

    def _empty_result(self) -> SearchVolumeResult:
        """Helper to return an empty result if no data is present."""
        return SearchVolumeResult(
            keyword_volumes={},
            statistics=SearchVolumeStatistics(
                total_keywords=0,
                resolved_keywords=0,
                unresolved_keywords=0,
                cache_hits=0,
                cache_misses=0,
                provider_calls=0,
                batches_processed=0,
                failed_provider_calls=0,
                average_batch_latency_ms=0.0,
                average_provider_latency_ms=0.0,
                provider_success_rate=100.0,
                execution_time_ms=0.0,
            ),
            provider_used="none",
            execution_metrics={},
        )
