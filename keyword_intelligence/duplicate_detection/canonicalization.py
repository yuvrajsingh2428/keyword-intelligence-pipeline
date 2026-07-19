"""Service for resolving overlapping groups and selecting canonical keywords."""

from __future__ import annotations

import pandas as pd
from loguru import logger

from keyword_intelligence.duplicate_detection.config import DuplicateDetectionConfig
from keyword_intelligence.duplicate_detection.models import (
    DuplicateCandidate,
    DuplicateGroup,
)


class CanonicalizationService:
    """Service to process raw duplicate candidates into definitive DuplicateGroups."""

    def __init__(self, config: DuplicateDetectionConfig) -> None:
        """Initialize with duplicate detection configuration."""
        self.config = config

    def process_candidates(
        self, candidates: list[DuplicateCandidate], original_data: pd.DataFrame | None
    ) -> list[DuplicateGroup]:
        """Convert a list of raw candidates into canonicalized DuplicateGroups.

        Args:
            candidates: All candidates discovered by strategies.
            original_data: The dataset context for metric ties (e.g. search volume).

        Returns:
            A list of non-overlapping DuplicateGroups.
        """
        if not candidates:
            return []

        # Graph approach: Build connected components to resolve overlaps.
        # We represent edges between canonical_keyword and matched_keyword.
        import typing

        import networkx as nx

        G: typing.Any = nx.Graph()

        for cand in candidates:
            # Only process if it meets min confidence
            if cand.confidence >= self.config.min_confidence:
                # Add edge with confidence as weight
                # In networkx, adding an edge automatically adds the nodes if they don't exist
                G.add_edge(
                    cand.original_keyword, cand.matched_keyword, weight=cand.confidence
                )

        duplicate_groups: list[DuplicateGroup] = []

        # Extract connected components (overlapping groups)
        components = list(nx.connected_components(G))

        for component in components:
            if len(component) < 2:
                continue

            keywords = list(component)

            # Enforce max group size (if exceeded, we just take the highest connected nodes,
            # but for simplicity we'll just slice the group or warn. For Phase 3A, we slice.)
            if len(keywords) > self.config.max_group_size:
                logger.warning(
                    f"Duplicate group size ({len(keywords)}) exceeds max "
                    f"({self.config.max_group_size}). Truncating."
                )
                keywords = keywords[: self.config.max_group_size]

            # Choose canonical: The simplest heuristic for Phase 3A is shortest string,
            # or most common. If we had volume, we would use it. We'll use length for now.
            canonical = min(keywords, key=len)

            # Average confidence of edges in this subgraph
            subgraph = G.subgraph(keywords)
            edges = list(subgraph.edges(data=True))
            if edges:
                avg_confidence = sum(d["weight"] for u, v, d in edges) / len(edges)
            else:
                avg_confidence = 100.0

            # The rest are duplicates
            duplicates = [k for k in keywords if k != canonical]

            duplicate_groups.append(
                DuplicateGroup(
                    canonical_keyword=canonical,
                    duplicates=duplicates,
                    confidence=avg_confidence,
                )
            )

        return duplicate_groups
