"""Validator stage for verifying dataframe schema and renaming columns."""

from __future__ import annotations

from typing import ClassVar

import pandas as pd

from keyword_intelligence.core.constants import StageType
from keyword_intelligence.core.exceptions import SchemaValidationError
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class ValidatorStage(BaseStage):
    """Validates the input dataframe against expected schema aliases."""

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
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.VALIDATOR

    @property
    def stage_version(self) -> str:
        """Return the version of the stage."""
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Validate and map columns in the context data.

        Args:
            context: The pipeline context containing the raw DataFrame.

        Returns:
            The modified pipeline context.

        Raises:
            SchemaValidationError: If the required 'keyword' column is missing.
        """
        df = context.data

        # 1. Drop completely empty rows
        df = df.dropna(how="all")

        raw_columns = df.columns.tolist()
        normalized_columns = [str(c).strip().lower() for c in raw_columns]
        df.columns = pd.Index(normalized_columns)

        # Map aliases to canonical names
        rename_map: dict[str, str] = {}
        for canonical, aliases in self.SCHEMA_ALIASES.items():
            for alias in aliases:
                if alias in normalized_columns:
                    rename_map[alias] = canonical
                    break

        if "keyword" not in rename_map.values():
            error_msg = (
                "Required column 'keyword' (or recognized alias) not found in input. "
                f"Found columns: {raw_columns}"
            )
            context.add_error(
                self.stage_type.value, "MISSING_KEYWORD_COLUMN", error_msg
            )
            raise SchemaValidationError(error_msg)

        # Record warnings for unmapped columns (optional fields dropped)
        unmapped = set(normalized_columns) - set(rename_map.keys())
        if unmapped:
            context.add_warning(
                self.stage_type.value,
                "UNMAPPED_COLUMNS_DROPPED",
                f"Dropped unmapped columns: {unmapped}",
            )

        df = df.rename(columns=rename_map)
        columns_to_keep = list(rename_map.values())
        df = df[columns_to_keep]

        context.data = df

        return context
