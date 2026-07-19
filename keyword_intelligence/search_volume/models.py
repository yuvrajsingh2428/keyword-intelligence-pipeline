"""Models for the Search Volume Engine."""

from __future__ import annotations

from typing import Literal

from keyword_intelligence.models.base import AppBaseModel


class ProviderCapabilities(AppBaseModel):
    """Capabilities of a specific search volume provider."""

    max_batch_size: int
    supports_parallel: bool
    supports_retry: bool
    supports_location: bool
    supports_language: bool
    supports_historical_data: bool


class KeywordVolume(AppBaseModel):
    """Search volume metrics for a single keyword."""

    keyword: str
    monthly_volume: int
    competition: Literal["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
    cpc: float
    source: str
    confidence: float


class SearchVolumeStatistics(AppBaseModel):
    """Overall statistics for a search volume execution."""

    total_keywords: int
    resolved_keywords: int
    unresolved_keywords: int
    cache_hits: int
    cache_misses: int
    provider_calls: int
    batches_processed: int
    failed_provider_calls: int
    average_batch_latency_ms: float
    average_provider_latency_ms: float
    provider_success_rate: float
    execution_time_ms: float


class ProviderMetrics(AppBaseModel):
    """Metrics specific to a provider's execution."""

    provider_name: str
    provider_version: str
    batches_processed: int
    keywords_processed: int
    cache_hit_ratio: float
    average_latency_ms: float


class SearchVolumeResult(AppBaseModel):
    """Final output from the Search Volume Engine."""

    keyword_volumes: dict[str, KeywordVolume]
    statistics: SearchVolumeStatistics
    provider_used: str
    execution_metrics: dict[str, ProviderMetrics]
