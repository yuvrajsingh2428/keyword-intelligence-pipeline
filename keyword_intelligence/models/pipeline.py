"""Pipeline data models for tracking execution state and results."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from keyword_intelligence.models.base import AppBaseModel


class ValidationResult(AppBaseModel):
    """Result of a schema validation operation."""

    success: bool
    missing_columns: list[str] = Field(default_factory=list)
    renamed_columns: dict[str, str] = Field(default_factory=dict)
    dropped_rows: int = 0
    errors: list[str] = Field(default_factory=list)


class PipelineResult(AppBaseModel):
    """End-to-end result of a pipeline execution."""

    success: bool
    stage_results: dict[str, Any] = Field(default_factory=dict)
    total_rows_processed: int = 0
    errors: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
