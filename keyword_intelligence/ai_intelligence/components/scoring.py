"""Scoring and Aggregation components for AI results."""

from __future__ import annotations

from typing import Any

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
        """Score the classification and combine metrics."""
        return AIClassificationResult(
            keyword=schema.keyword,
            relevance=schema.relevance,
            reason=schema.reason,
            search_intent=schema.search_intent,
            category=schema.category,
            confidence=schema.confidence,
            recommended_action=schema.recommended_action,
            provider_used=provider,
            prompt_version=prompt_version,
            processing_method="AI",
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

        # Map new columns for records that were sent to AI
        def _update_col(kw: str, current_val: Any, attr: str) -> Any:
            val = _get_val(kw, attr)
            return val if val is not None else current_val

        context.data["ai_relevance"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("ai_relevance"), "relevance"
            ),
            axis=1,
        )
        context.data["ai_reason"] = context.data.apply(
            lambda row: _update_col(row["keyword"], row.get("ai_reason"), "reason"),
            axis=1,
        )
        context.data["ai_confidence"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("ai_confidence"), "confidence"
            ),
            axis=1,
        )
        context.data["ai_category"] = context.data.apply(
            lambda row: _update_col(row["keyword"], row.get("ai_category"), "category"),
            axis=1,
        )
        context.data["ai_search_intent"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("ai_search_intent"), "search_intent"
            ),
            axis=1,
        )
        context.data["ai_recommended_action"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("ai_recommended_action"), "recommended_action"
            ),
            axis=1,
        )
        context.data["processing_method"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("processing_method"), "processing_method"
            ),
            axis=1,
        )
        context.data["ai_model"] = context.data.apply(
            lambda row: _update_col(row["keyword"], row.get("ai_model"), "model"),
            axis=1,
        )
        context.data["ai_latency"] = context.data.apply(
            lambda row: _update_col(row["keyword"], row.get("ai_latency"), "latency"),
            axis=1,
        )
        context.data["ai_prompt_version"] = context.data.apply(
            lambda row: _update_col(
                row["keyword"], row.get("ai_prompt_version"), "prompt_version"
            ),
            axis=1,
        )

        logger.debug(
            f"Aggregated {len(results)} AI classifications into context dataframe."
        )
