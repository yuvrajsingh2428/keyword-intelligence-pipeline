"""Main engine for orchestrating duplicate detection."""

from __future__ import annotations

import time

from loguru import logger

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.duplicate_detection.canonicalization import (
    CanonicalizationService,
)
from keyword_intelligence.duplicate_detection.config import DuplicateDetectionConfig
from keyword_intelligence.duplicate_detection.models import (
    DuplicateDetectionMetrics,
    DuplicateDetectionResult,
    DuplicateStatistics,
)
from keyword_intelligence.duplicate_detection.pipeline import DetectionPipeline
from keyword_intelligence.duplicate_detection.registry import DuplicateDetectionRegistry
from keyword_intelligence.duplicate_detection.scorer import DuplicateScorer

# Built-in strategies
from keyword_intelligence.duplicate_detection.strategies.exact import ExactStrategy
from keyword_intelligence.duplicate_detection.strategies.fuzzy import FuzzyStrategy
from keyword_intelligence.duplicate_detection.strategies.normalized import (
    NormalizedStrategy,
)
from keyword_intelligence.duplicate_detection.strategies.semantic_placeholder import (
    SemanticStrategy,
)
from keyword_intelligence.pipeline.context import PipelineContext


class DuplicateDetectionEngine:
    """High-level facade for duplicate detection."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the engine with configuration and defaults."""
        self.config = DuplicateDetectionConfig.from_settings(settings)

        # Initialize internal components
        self.registry = DuplicateDetectionRegistry()
        self.pipeline = DetectionPipeline(self.config, self.registry)
        self.canonicalizer = CanonicalizationService(self.config)
        self.scorer = DuplicateScorer()

        self._register_default_strategies()

    def _register_default_strategies(self) -> None:
        """Register the built-in strategies."""
        self.registry.register(ExactStrategy(self.config))
        self.registry.register(NormalizedStrategy(self.config))
        self.registry.register(FuzzyStrategy(self.config))
        self.registry.register(SemanticStrategy(self.config))

    def process(self, context: PipelineContext) -> DuplicateDetectionResult:
        """Run the full duplicate detection process.

        Args:
            context: PipelineContext containing the DataFrame.

        Returns:
            DuplicateDetectionResult containing groups, statistics, and metrics.
        """
        # Logging removed
        start_time = time.perf_counter()

        initial_rows = len(context.data) if context.has_data else 0

        # 1. Run Pipeline
        metrics_map: dict[str, DuplicateDetectionMetrics] = {}
        raw_candidates = self.pipeline.run(context, metrics_map)

        # 2. Score Candidates
        scored_candidates = self.scorer.score_candidates(raw_candidates)

        # 3. Canonicalize Groups
        duplicate_groups = self.canonicalizer.process_candidates(
            scored_candidates, context.data if context.has_data else None
        )

        # 4. Filter DataFrame
        duplicates_removed = 0
        if context.has_data:
            if "status" not in context.data.columns:
                context.data["status"] = "ACTIVE"

            # 4a. Exact duplicates
            target_col_exact = (
                "normalized_keyword"
                if "normalized_keyword" in context.data.columns
                else "keyword"
            )
            is_dup = context.data.duplicated(subset=[target_col_exact], keep="first")
            context.data.loc[is_dup, "status"] = "DUPLICATE"
            exact_removed = is_dup.sum()

            # 4b. Normalized/Fuzzy duplicates
            to_remove = set()
            for group in duplicate_groups:
                for dup in group.duplicates:
                    if dup != group.canonical_keyword:
                        to_remove.add(dup)

            target_col = (
                "normalized_keyword"
                if "normalized_keyword" in context.data.columns
                else "keyword"
            )
            mask = context.data[target_col].isin(to_remove)
            context.data.loc[mask, "status"] = "DUPLICATE"

            duplicates_removed = exact_removed + len(to_remove)
            # Logging removed

        total_time_ms = (time.perf_counter() - start_time) * 1000

        # Build stats
        exact_count = sum(1 for c in scored_candidates if c.match_type == "exact")
        norm_count = sum(1 for c in scored_candidates if c.match_type == "normalized")
        fuzzy_count = sum(1 for c in scored_candidates if c.match_type == "fuzzy")
        semantic_count = sum(1 for c in scored_candidates if c.match_type == "semantic")

        stats = DuplicateStatistics(
            total_keywords=initial_rows,
            total_duplicate_groups=len(duplicate_groups),
            total_duplicates=len(raw_candidates),
            duplicates_removed=duplicates_removed,
            exact_matches=exact_count,
            normalized_matches=norm_count,
            fuzzy_matches=fuzzy_count,
            semantic_matches=semantic_count,
            execution_time_ms=total_time_ms,
        )

        # Logging removed

        return DuplicateDetectionResult(
            duplicate_groups=duplicate_groups,
            duplicates_removed=duplicates_removed,
            statistics=stats,
            execution_metrics=metrics_map,
        )
