"""Exact match strategy for duplicate detection."""

from __future__ import annotations

from keyword_intelligence.duplicate_detection.models import DuplicateCandidate
from keyword_intelligence.duplicate_detection.strategies.base import (
    DuplicateDetectionStrategy,
)
from keyword_intelligence.pipeline.context import PipelineContext


class ExactStrategy(DuplicateDetectionStrategy):
    """Detects exact string match duplicates using vectorized pandas hashing.

    Time Complexity: O(N)
    Space Complexity: O(N)
    """

    @property
    def priority(self) -> int:
        return 10

    @property
    def strategy_name(self) -> str:
        return "ExactMatch"

    def detect(
        self, context: PipelineContext, exclude_keywords: set[str]
    ) -> list[DuplicateCandidate]:
        if not self.config.exact_enabled or not context.has_data:
            return []

        df = context.data
        if "keyword" not in df.columns:
            return []

        # Filter out already resolved keywords
        mask = ~df["keyword"].isin(exclude_keywords)
        filtered_df = df[mask]

        # Use pandas grouping to find exact matches instantly
        duplicates = filtered_df[filtered_df.duplicated(subset=["keyword"], keep=False)]

        candidates: list[DuplicateCandidate] = []

        # Group identical keywords
        for keyword, group in duplicates.groupby("keyword"):
            # Because it's an exact match, they are all the same keyword.
            # We pair the first one as 'original' and the rest as 'matched'.
            kw_str = str(keyword)
            # Actually, every pairwise combination in the group is a match.
            # We just need to link all of them to the first instance to build the component later.
            indices = group.index.tolist()
            if len(indices) > 1:
                # Pair the canonical (first) with the others
                for i in range(1, len(indices)):
                    candidates.append(
                        DuplicateCandidate(
                            original_keyword=kw_str,
                            matched_keyword=kw_str,
                            matched_by_strategy=self.strategy_name,
                            confidence=100.0,
                            match_type="exact",
                            explanation="Exact string match.",
                        )
                    )

        return candidates
