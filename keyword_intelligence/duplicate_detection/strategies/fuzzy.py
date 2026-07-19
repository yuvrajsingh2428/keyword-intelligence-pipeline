"""Fuzzy match strategy using Rapidfuzz with blocking to avoid O(N^2)."""

from __future__ import annotations

from rapidfuzz import fuzz, process

from keyword_intelligence.duplicate_detection.models import DuplicateCandidate
from keyword_intelligence.duplicate_detection.strategies.base import (
    DuplicateDetectionStrategy,
)
from keyword_intelligence.duplicate_detection.strategies.blocking import PrefixBlocking
from keyword_intelligence.pipeline.context import PipelineContext


class FuzzyStrategy(DuplicateDetectionStrategy):
    """Detects duplicates using high-performance fuzzy matching (cdist).

    Utilizes BlockingStrategies to reduce the search space from O(N^2)
    to roughly O(N * (bucket_size)), making it viable for 50k+ datasets.
    """

    @property
    def priority(self) -> int:
        return 30

    @property
    def strategy_name(self) -> str:
        return "FuzzyMatch"

    def detect(
        self, context: PipelineContext, exclude_keywords: set[str]
    ) -> list[DuplicateCandidate]:
        if not self.config.fuzzy_enabled or not context.has_data:
            return []

        df = context.data
        if "keyword" not in df.columns:
            return []

        # Filter out already resolved keywords
        mask = ~df["keyword"].isin(exclude_keywords)
        keywords = df.loc[mask, "keyword"].tolist()

        if not keywords:
            return []

        # Use PrefixBlocking for robust fuzzy matching blocks
        blocker = PrefixBlocking(prefix_length=1)
        blocks = blocker.create_blocks(keywords)

        candidates: list[DuplicateCandidate] = []
        threshold = self.config.fuzzy_threshold

        # Compare within blocks (and adjacent blocks if needed, but for Phase 3A
        # intra-block is sufficient and guarantees scaling).
        for length_key, block_keywords in blocks.items():
            if len(block_keywords) < 2:
                continue

            # We need to find pairs within this block.
            # Rapidfuzz process.cdist handles all-to-all fast if needed, or we can use extract
            # We iterate and use `extract` to find matches above the threshold.

            # Since extract checks against a list, we iteratively pop or just check all
            # and ignore self-matches.

            # For 50k rows, if buckets are small, this is extremely fast.
            # If buckets are huge (e.g. 5000 strings of length 15), extract is highly optimized in C++.

            # We convert block to a set to remove exact duplicates inside the block first (handled by ExactStrategy anyway).
            unique_kws = list(set(block_keywords))
            visited: set[str] = set()

            for i, kw in enumerate(unique_kws):
                if kw in visited:
                    continue

                # Search the remaining items, skipping ones already matched
                search_space = [x for x in unique_kws[i + 1 :] if x not in visited]
                if not search_space:
                    continue

                # extract returns a list of tuples: (matched_string, score, index)
                results = process.extract(
                    kw,
                    search_space,
                    scorer=fuzz.ratio,
                    score_cutoff=threshold,
                    limit=None,  # Get all matches above threshold
                )

                for matched_kw, score, _ in results:
                    visited.add(matched_kw)
                    candidates.append(
                        DuplicateCandidate(
                            original_keyword=kw,
                            matched_keyword=matched_kw,
                            matched_by_strategy=self.strategy_name,
                            confidence=score,
                            match_type="fuzzy",
                            explanation=f"Fuzzy ratio similarity: {score:.1f}%.",
                        )
                    )

        return candidates
