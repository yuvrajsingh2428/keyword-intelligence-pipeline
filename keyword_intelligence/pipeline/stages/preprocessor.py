"""Preprocessor stage for text normalization using vectorized pandas operations."""

from __future__ import annotations

from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class PreprocessorStage(BaseStage):
    """Normalizes the keyword text data based on pipeline configuration flags."""

    @property
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.PREPROCESSOR

    @property
    def stage_version(self) -> str:
        """Return the version of the stage."""
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Clean and normalize the keyword data according to settings.

        Args:
            context: The pipeline context containing the validated DataFrame.

        Returns:
            The modified pipeline context.
        """
        df = context.data

        if "keyword" not in df.columns:
            context.add_warning(
                self.stage_type.value,
                "NO_KEYWORD_COLUMN",
                "No 'keyword' column found for preprocessing.",
            )
            return context

        df["keyword"] = df["keyword"].fillna("")

        # Normalization (lowercase, whitespace, punctuation, abbreviation expansion)
        # is now handled by the NormalizationStage which runs after PreprocessorStage.

        if context.settings.enable_remove_empty_rows:
            df = df[df["keyword"] != ""]

        if context.settings.enable_deduplication:
            df = df.drop_duplicates(subset=["keyword"])

        df = df.reset_index(drop=True)
        context.data = df

        return context
