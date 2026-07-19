"""Scoring and Aggregation components for AI results."""

from __future__ import annotations

from typing import Any

import pandas as pd
from loguru import logger

from keyword_intelligence.ai_intelligence.models import (
    AIClassificationResult,
    KeywordResponseSchema,
)
from keyword_intelligence.pipeline.context import PipelineContext


class ConfidenceScorer:
    """Calculates the final confidence score for an AI classification."""

    def score(
        self,
        schema: KeywordResponseSchema,
        lookup: dict[str, dict[str, Any]],
        provider: str,
        prompt_version: str,
    ) -> AIClassificationResult:
        """Score the classification and combine metrics.

        Args:
            schema: The validated KeywordResponseSchema.
            lookup: Precomputed dictionary mapping keywords to their row data.
            provider: The provider name.
            prompt_version: The prompt version used.

        Returns:
            The final AIClassificationResult.
        """
        # Default heuristic fallbacks
        heuristic_conf = 100
        duplicate_conf = 100
        sv_conf = 100

        row = lookup.get(schema.keyword, {})

        # Search volume confidence logic:
        if "search_volume" in row and pd.notna(row["search_volume"]):
            sv_conf = 100
        else:
            sv_conf = 50  # Unknown search volume lowers confidence

        # Final calculation formula (example weighting)
        provider_conf = schema.confidence
        final_conf = int((provider_conf * 0.7) + (sv_conf * 0.3))

        # Ensure bounds
        final_conf = max(0, min(100, final_conf))

        return AIClassificationResult(
            keyword=schema.keyword,
            relevant=schema.relevant,
            classification=schema.classification,
            reasoning=schema.reasoning,
            matched_business_fact=schema.matched_business_fact,
            matched_category=schema.matched_category,
            matched_brand=schema.matched_brand,
            matched_product=schema.matched_product,
            provider_confidence=provider_conf,
            final_confidence=final_conf,
            provider_used=provider,
            prompt_version=prompt_version,
        )


class ResultAggregator:
    """Aggregates final AI results back into the pipeline context."""

    def aggregate(
        self, context: PipelineContext, results: list[AIClassificationResult]
    ) -> None:
        """Merge the AI results back into the DataFrame.

        Args:
            context: The pipeline context.
            results: The list of finalized AI classification results.
        """
        if context.data.empty:
            return

        # Convert results to a dictionary for fast lookup
        res_map = {r.keyword: r for r in results}

        def _get_val(kw: str, attr: str) -> str | int | None:
            r = res_map.get(kw)
            return (
                getattr(r, attr).value
                if r and hasattr(getattr(r, attr), "value")
                else getattr(r, attr)
                if r
                else None
            )

        # Map new columns, preserving existing values (e.g. from deterministic filter)
        def _update_col(kw: str, current_val: Any, attr: str) -> Any:
            val = _get_val(kw, attr)
            return val if val is not None else current_val

        context.data["business_relevance"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("business_relevance"), "classification"
            ),
            axis=1,
        )
        context.data["business_reason"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("business_reason"), "reasoning"
            ),
            axis=1,
        )
        context.data["ai_confidence"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("ai_confidence"), "final_confidence"
            ),
            axis=1,
        )

        logger.debug(
            f"Aggregated {len(results)} AI classifications into context dataframe."
        )
