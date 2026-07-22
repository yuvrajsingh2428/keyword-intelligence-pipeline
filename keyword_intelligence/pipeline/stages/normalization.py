"""Pipeline stage adapter for Keyword Normalization."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.core.constants import StageType
from keyword_intelligence.normalization.engine import NormalizationEngine
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class NormalizationStage(BaseStage):
    """Pipeline stage that applies normalization strategies to the keywords."""

    def __init__(self, engine: NormalizationEngine) -> None:
        """Initialize the stage with an engine instance."""
        self.engine = engine

    @property
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.NORMALIZATION

    @property
    def stage_version(self) -> str:
        """Return the version of this stage implementation."""
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the normalization engine."""
        df = context.data

        if "keyword" not in df.columns:
            context.add_warning(
                self.stage_type.value,
                "NO_KEYWORD_COLUMN",
                "No 'keyword' column found for normalization.",
            )
            return context

        logger.info(f"Executing stage {self.stage_type.value}")

        # Preserve the original keyword in a new column
        if "original_keyword" not in df.columns:
            df["original_keyword"] = df["keyword"]

        # Apply normalization and overwrite 'keyword'
        # The engine now returns a NormalizationResult object containing traces and metrics
        normalization_result = self.engine.normalize_series(df["keyword"])

        df["keyword"] = normalization_result.normalized_series
        df["normalized_keyword"] = normalization_result.normalized_series
        df["normalization_trace"] = normalization_result.trace_series

        # Log metrics
        metrics = normalization_result.metrics
        logger.info(
            f"Normalization completed: {metrics.total_processed} processed, "
            f"{metrics.total_modified} modified."
        )
        for strategy, count in metrics.modifications_per_strategy.items():
            logger.debug(f"{strategy}: {count} modifications")

        # Store metrics in context metadata if applicable
        if not hasattr(context, "metadata"):
            context.metadata = {}
        context.metadata["normalization_metrics"] = metrics.model_dump()

        context.data = df
        return context
