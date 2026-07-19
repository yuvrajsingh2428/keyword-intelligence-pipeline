"""Strongly-typed report models for the Reporting Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from keyword_intelligence.business_context.models import BusinessProfile
from keyword_intelligence.models.base import AppBaseModel

# ---------------------------------------------------------------------------
# Analytics sub-models
# ---------------------------------------------------------------------------


class DatasetStatistics(AppBaseModel):
    """Dataset-level keyword statistics."""

    total_keywords: int = 0
    unique_keywords: int = 0
    duplicate_keywords: int = 0
    removed_keywords: int = 0


class RelevanceDistribution(AppBaseModel):
    """AI relevance classification breakdown."""

    relevant: int = 0
    irrelevant: int = 0
    uncertain: int = 0


class IntentDistribution(AppBaseModel):
    """User intent classification breakdown."""

    informational: int = 0
    commercial: int = 0
    transactional: int = 0
    navigational: int = 0
    unknown: int = 0


class CategoryDistribution(AppBaseModel):
    """Category classification breakdown."""

    counts: dict[str, int] = Field(default_factory=dict)


class QualityDistribution(AppBaseModel):
    """Quality classification breakdown."""

    good: int = 0
    weak: int = 0
    spam: int = 0
    duplicate: int = 0
    unknown: int = 0


class SearchVolumeStatistics(AppBaseModel):
    """Search volume statistics for the dataset."""

    average_volume: float = 0.0
    median_volume: float = 0.0
    min_volume: float = 0.0
    max_volume: float = 0.0
    total_with_volume: int = 0
    total_without_volume: int = 0
    top_keywords: list[dict[str, Any]] = Field(
        default_factory=list,
    )


class PipelineTimingStatistics(AppBaseModel):
    """Pipeline execution timing statistics."""

    total_execution_time_ms: float = 0.0
    stage_timings: dict[str, float] = Field(
        default_factory=dict,
    )
    cache_hit_ratios: dict[str, float] = Field(
        default_factory=dict,
    )
    provider_usage: dict[str, str] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------------------------
# Report summary models
# ---------------------------------------------------------------------------


class ExecutiveSummary(AppBaseModel):
    """High-level executive report for stakeholders."""

    title: str = "Keyword Intelligence Report"
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )
    total_keywords_analysed: int = 0
    relevant_keywords: int = 0
    irrelevant_keywords: int = 0
    average_confidence: float = 0.0
    top_category: str = ""
    dominant_intent: str = ""
    pipeline_health: str = "HEALTHY"
    warnings_count: int = 0
    errors_count: int = 0


class TechnicalSummary(AppBaseModel):
    """Detailed technical summary for engineers."""

    execution_id: str = ""
    pipeline_version: str = ""
    stages_executed: list[str] = Field(
        default_factory=list,
    )
    timing: PipelineTimingStatistics = Field(
        default_factory=PipelineTimingStatistics,
    )
    dataset: DatasetStatistics = Field(
        default_factory=DatasetStatistics,
    )
    warnings: list[dict[str, str]] = Field(
        default_factory=list,
    )
    errors: list[dict[str, str]] = Field(
        default_factory=list,
    )


class AnalyticsSummary(AppBaseModel):
    """Computed analytics across all classification dimensions."""

    dataset: DatasetStatistics = Field(
        default_factory=DatasetStatistics,
    )
    relevance: RelevanceDistribution = Field(
        default_factory=RelevanceDistribution,
    )
    intent: IntentDistribution = Field(
        default_factory=IntentDistribution,
    )
    categories: CategoryDistribution = Field(
        default_factory=CategoryDistribution,
    )
    quality: QualityDistribution = Field(
        default_factory=QualityDistribution,
    )
    search_volume: SearchVolumeStatistics = Field(
        default_factory=SearchVolumeStatistics,
    )


class PipelineSummary(AppBaseModel):
    """Combined pipeline state and metadata."""

    execution_id: str = ""
    pipeline_version: str = ""
    total_rows_processed: int = 0
    timing: PipelineTimingStatistics = Field(
        default_factory=PipelineTimingStatistics,
    )


# ---------------------------------------------------------------------------
# Top-level report result
# ---------------------------------------------------------------------------


class ReportResult(AppBaseModel):
    """Complete report produced by the ReportEngine."""

    executive: ExecutiveSummary = Field(
        default_factory=ExecutiveSummary,
    )
    business_profile: BusinessProfile | None = None
    technical: TechnicalSummary = Field(
        default_factory=TechnicalSummary,
    )
    analytics: AnalyticsSummary = Field(
        default_factory=AnalyticsSummary,
    )
    pipeline: PipelineSummary = Field(
        default_factory=PipelineSummary,
    )
    exported_files: list[str] = Field(
        default_factory=list,
    )


# ---------------------------------------------------------------------------
# Exporter capability model
# ---------------------------------------------------------------------------


class ExporterCapabilities(AppBaseModel):
    """Describes the capabilities of a report exporter."""

    exporter_name: str
    exporter_version: str
    supported_extensions: list[str] = Field(
        default_factory=list,
    )
    supports_streaming: bool = False
    supports_large_files: bool = False
