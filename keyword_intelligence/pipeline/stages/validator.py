"""Validator stage for verifying dataframe schema and renaming columns."""

from __future__ import annotations

from typing import ClassVar

import pandas as pd
from loguru import logger

from keyword_intelligence.core.exceptions import SchemaValidationError
from keyword_intelligence.models.pipeline import ValidationResult
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class ValidatorStage(BaseStage):
    """Validates the input dataframe against expected schema aliases.

    Maps common aliases (e.g., 'Search Keyword', 'Query') to standard internal
    names (e.g., 'keyword'). Drops completely empty rows and unmapped columns.
    """

    # Mapping of canonical column name to list of acceptable aliases
    SCHEMA_ALIASES: ClassVar[dict[str, list[str]]] = {
        "keyword": ["keyword", "search keyword", "query", "search query"],
        "volume": ["volume", "search volume", "sv", "current search volume"],
        "competition": ["competition", "comp"],
        "cpc": ["cpc", "cost per click"],
        "intent": ["intent", "search intent"],
        "language": ["language", "lang"],
        "country": ["country", "loc", "location"],
        "source": ["source", "src"],
    }

    @property
    def name(self) -> str:
        """Return the name of the stage."""
        return "Validator"

    def execute(self, context: PipelineContext) -> None:
        """Validate and map columns in the context data.

        Args:
            context: The pipeline context containing the raw DataFrame.

        Raises:
            SchemaValidationError: If the required 'keyword' column is missing.
        """
        df = context.data
        initial_rows = len(df)

        # 1. Drop completely empty rows (vectorized)
        df = df.dropna(how="all")
        dropped_empty = initial_rows - len(df)

        # 2. Normalize existing column names to lowercase and strip whitespace
        # This makes alias matching case-insensitive and resilient to trailing spaces.
        raw_columns = df.columns.tolist()
        normalized_columns = [str(c).strip().lower() for c in raw_columns]
        df.columns = pd.Index(normalized_columns)

        # 3. Map aliases to canonical names
        rename_map: dict[str, str] = {}
        for canonical, aliases in self.SCHEMA_ALIASES.items():
            for alias in aliases:
                if alias in normalized_columns:
                    rename_map[alias] = canonical
                    break  # Found the column, move to next canonical field

        # Check for required 'keyword' column
        if "keyword" not in rename_map.values():
            raise SchemaValidationError(
                "Required column 'keyword' (or recognized alias) not found in input. "
                f"Found columns: {raw_columns}"
            )

        # Rename columns
        df = df.rename(columns=rename_map)

        # 4. Drop unmapped columns (we only keep what we know about)
        columns_to_keep = list(rename_map.values())
        df = df[columns_to_keep]

        # Save back to context
        context.data = df

        # Record validation result in metadata
        result = ValidationResult(
            success=True,
            renamed_columns=rename_map,
            dropped_rows=dropped_empty,
        )
        context.metadata["validation_result"] = result
        logger.info(
            f"Validation passed. Mapped columns: {rename_map}. "
            f"Dropped {dropped_empty} empty rows."
        )
