"""Detection pipeline for orchestrating strategy execution."""

from __future__ import annotations

import time

from loguru import logger

from keyword_intelligence.duplicate_detection.config import DuplicateDetectionConfig
from keyword_intelligence.duplicate_detection.models import (
    DuplicateCandidate,
    DuplicateDetectionMetrics,
)
from keyword_intelligence.duplicate_detection.registry import DuplicateDetectionRegistry
from keyword_intelligence.pipeline.context import PipelineContext


class DetectionPipeline:
    """Executes registered duplicate detection strategies with early-exit optimization."""

    def __init__(
        self, config: DuplicateDetectionConfig, registry: DuplicateDetectionRegistry
    ) -> None:
        """Initialize the detection pipeline."""
        self.config = config
        self.registry = registry

    def run(
        self,
        context: PipelineContext,
        metrics_map: dict[str, DuplicateDetectionMetrics],
    ) -> list[DuplicateCandidate]:
        """Run all strategies and yield candidates.

        Args:
            context: The pipeline context.
            metrics_map: Dictionary to populate with execution metrics per strategy.

        Returns:
            A consolidated list of all discovered duplicate candidates.
        """
        all_candidates: list[DuplicateCandidate] = []

        # High-confidence matched keywords can be excluded from subsequent expensive strategies
        # (Early-exit optimization)
        resolved_keywords: set[str] = set()

        for strategy in self.registry.get_strategies():
            logger.info(f"Running Duplicate Strategy: {strategy.strategy_name}")
            start_time = time.perf_counter()

            candidates = strategy.detect(context, exclude_keywords=resolved_keywords)

            execution_time = (time.perf_counter() - start_time) * 1000

            if candidates:
                all_candidates.extend(candidates)

                # Update early-exit resolved keywords
                for cand in candidates:
                    if cand.confidence >= self.config.min_confidence:
                        if cand.matched_keyword != cand.original_keyword:
                            resolved_keywords.add(cand.matched_keyword)

            # Record metrics
            avg_conf = (
                sum(c.confidence for c in candidates) / len(candidates)
                if candidates
                else 0.0
            )

            metrics = DuplicateDetectionMetrics(
                candidates_generated=len(candidates),
                matches_found=len(candidates),
                execution_time_ms=execution_time,
                average_confidence=avg_conf,
            )
            metrics_map[strategy.strategy_name] = metrics

            logger.info(
                f"Strategy '{strategy.strategy_name}' finished in {execution_time:.2f}ms. "
                f"Found {len(candidates)} candidates."
            )

        return all_candidates
