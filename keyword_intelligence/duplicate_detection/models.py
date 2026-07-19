"""Data models for duplicate detection."""

from __future__ import annotations

from pydantic import Field

from keyword_intelligence.models.base import AppBaseModel


class DuplicateCandidate(AppBaseModel):
    """Represents a potential duplicate match between two keywords."""

    original_keyword: str
    matched_keyword: str
    matched_by_strategy: str
    confidence: float
    match_type: str  # e.g., 'exact', 'fuzzy', 'normalized'
    explanation: str


class DuplicateGroup(AppBaseModel):
    """Represents a group of duplicate keywords reduced to a canonical keyword."""

    canonical_keyword: str
    duplicates: list[str] = Field(default_factory=list)
    confidence: float


class DuplicateDetectionMetrics(AppBaseModel):
    """Execution metrics for a specific detection strategy."""

    comparisons_performed: int = 0
    candidates_generated: int = 0
    matches_found: int = 0
    execution_time_ms: float = 0.0
    average_confidence: float = 0.0


class DuplicateStatistics(AppBaseModel):
    """Aggregate statistics across all duplicate detection operations."""

    total_keywords: int = 0
    total_duplicate_groups: int = 0
    total_duplicates: int = 0
    duplicates_removed: int = 0
    exact_matches: int = 0
    normalized_matches: int = 0
    fuzzy_matches: int = 0
    semantic_matches: int = 0
    execution_time_ms: float = 0.0


class DuplicateDetectionResult(AppBaseModel):
    """The final result of the duplicate detection engine."""

    duplicate_groups: list[DuplicateGroup] = Field(default_factory=list)
    duplicates_removed: int = 0
    statistics: DuplicateStatistics = Field(default_factory=DuplicateStatistics)
    execution_metrics: dict[str, DuplicateDetectionMetrics] = Field(
        default_factory=dict
    )
