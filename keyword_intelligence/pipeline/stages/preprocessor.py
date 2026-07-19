"""Preprocessor stage for text normalization using vectorized pandas operations."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class PreprocessorStage(BaseStage):
    """Normalizes the keyword text data using vectorized pandas operations.

    Operations applied to the 'keyword' column:
    - Unicode normalization (NFKC) via regex/str methods (if needed)
    - Lowercasing
    - Stripping leading/trailing whitespace
    - Replacing multiple interior spaces with a single space
    - Dropping rows that become empty after cleaning
    """

    @property
    def name(self) -> str:
        """Return the name of the stage."""
        return "Preprocessor"

    def execute(self, context: PipelineContext) -> None:
        """Clean and normalize the keyword data.

        Args:
            context: The pipeline context containing the validated DataFrame.
        """
        df = context.data
        initial_rows = len(df)

        if "keyword" not in df.columns:
            logger.warning("No 'keyword' column found for preprocessing.")
            return

        # 1. Fill NaNs with empty string to avoid AttributeError in string operations
        df["keyword"] = df["keyword"].fillna("")

        # 2. Lowercase and strip edges
        df["keyword"] = df["keyword"].str.lower().str.strip()

        # 3. Replace multiple interior spaces with a single space
        df["keyword"] = df["keyword"].str.replace(r"\s+", " ", regex=True)

        # 4. Drop rows that became empty after cleaning
        # Using vectorized boolean indexing
        df = df[df["keyword"] != ""]

        # 5. Drop duplicates after normalization (exact matches)
        # This is a basic exact match deduplication, more advanced deduplication
        # will happen in Phase 3.
        df = df.drop_duplicates(subset=["keyword"])

        # Reset index after drops
        df = df.reset_index(drop=True)

        dropped_rows = initial_rows - len(df)

        # Save back to context
        context.data = df

        logger.info(
            f"Preprocessing complete. Cleaned {len(df)} rows, dropped {dropped_rows} "
            "(empty or exact duplicates)."
        )
