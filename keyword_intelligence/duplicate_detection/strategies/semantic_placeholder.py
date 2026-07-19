"""Semantic match strategy placeholder for future LLM integration."""

from __future__ import annotations

from keyword_intelligence.duplicate_detection.models import DuplicateCandidate
from keyword_intelligence.duplicate_detection.strategies.base import (
    DuplicateDetectionStrategy,
)
from keyword_intelligence.pipeline.context import PipelineContext


class SemanticStrategy(DuplicateDetectionStrategy):
    """Semantic matching stub for Phase 3A.

    Will be fully implemented in a future phase using Embeddings or LLMs.
    """

    @property
    def priority(self) -> int:
        return 40

    @property
    def strategy_name(self) -> str:
        return "SemanticMatch"

    def detect(
        self, context: PipelineContext, exclude_keywords: set[str]
    ) -> list[DuplicateCandidate]:
        if not self.config.semantic_enabled or not context.has_data:
            return []

        # Placeholder implementation returning no matches.
        return []
