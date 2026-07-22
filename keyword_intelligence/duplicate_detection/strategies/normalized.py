"""Normalized match strategy for duplicate detection."""

from __future__ import annotations

import unicodedata

from keyword_intelligence.duplicate_detection.models import DuplicateCandidate
from keyword_intelligence.duplicate_detection.strategies.base import (
    DuplicateDetectionStrategy,
)
from keyword_intelligence.pipeline.context import PipelineContext


class NormalizedStrategy(DuplicateDetectionStrategy):
    """Detects duplicates after heavy text normalization (unicode, spacing, lower).

    Time Complexity: O(N)
    Space Complexity: O(N)
    """

    @property
    def priority(self) -> int:
        return 20

    @property
    def strategy_name(self) -> str:
        return "NormalizedMatch"

    def _normalize(self, text: str) -> str:
        """Apply NFKD unicode normalization, lowercasing, and space collapsing."""
        if not text:
            return ""
        # 1. Unicode NFKD normalization
        norm = unicodedata.normalize("NFKD", str(text))
        # 2. Lowercase and strip
        norm = norm.lower().strip()
        # 3. Collapse whitespace
        import re

        norm = re.sub(r"\s+", " ", norm)
        return norm

    def detect(
        self, context: PipelineContext, exclude_keywords: set[str]
    ) -> list[DuplicateCandidate]:
        if not self.config.normalized_enabled or not context.has_data:
            return []

        df = context.data
        target_col = (
            "normalized_keyword" if "normalized_keyword" in df.columns else "keyword"
        )
        if target_col not in df.columns:
            return []

        # Filter out already resolved keywords
        mask = ~df[target_col].isin(exclude_keywords)
        filtered_df = df[mask].copy()

        if filtered_df.empty:
            return []

        # Create a normalized column for grouping
        filtered_df["_norm_kw"] = filtered_df[target_col].apply(self._normalize)

        # Find groups of identical normalized keywords
        duplicates = filtered_df[
            filtered_df.duplicated(subset=["_norm_kw"], keep=False)
        ]

        candidates: list[DuplicateCandidate] = []

        for norm_kw, group in duplicates.groupby("_norm_kw"):
            original_kws = group[target_col].tolist()
            if len(original_kws) > 1:
                canonical = original_kws[0]
                for i in range(1, len(original_kws)):
                    matched = original_kws[i]
                    if canonical != matched:  # Don't create exact matches here
                        candidates.append(
                            DuplicateCandidate(
                                original_keyword=canonical,
                                matched_keyword=matched,
                                matched_by_strategy=self.strategy_name,
                                confidence=95.0,  # High confidence, but not 100% exact
                                match_type="normalized",
                                explanation=f"Matched after normalization to '{norm_kw}'.",
                            )
                        )

        return candidates
