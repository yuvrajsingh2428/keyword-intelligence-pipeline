"""Pipeline data models for tracking execution state, metrics, and errors."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from keyword_intelligence.models.base import AppBaseModel


class DatasetMetadata(AppBaseModel):
    """Metadata detailing the original dataset uploaded into the pipeline."""

    file_name: str = ""
    file_size: int = 0
    file_extension: str = ""
    encoding: str = ""
    checksum: str = ""  # SHA256
    mime_type: str = ""
    total_rows: int = 0
    total_columns: int = 0
    original_column_names: list[str] = Field(default_factory=list)
    detected_schema_version: str | None = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StageMetrics(AppBaseModel):
    """Execution metrics for a single pipeline stage."""

    stage_name: str
    rows_loaded: int = 0
    rows_removed: int = 0
    empty_rows_removed: int = 0
    duplicate_rows_removed: int = 0
    processing_time_ms: float = 0.0
    warnings_count: int = 0
    errors_count: int = 0


class PipelineMetrics(AppBaseModel):
    """Aggregate metrics for the entire pipeline execution."""

    total_time_ms: float = 0.0
    total_rows_processed: int = 0
    total_rows_removed: int = 0
    total_warnings: int = 0
    total_errors: int = 0


class PipelineWarning(AppBaseModel):
    """A structured warning raised during pipeline execution."""

    stage: str
    code: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineError(AppBaseModel):
    """A structured error raised during pipeline execution."""

    stage: str
    code: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineResult(AppBaseModel):
    """End-to-end result produced by the PipelineOrchestrator."""

    execution_id: str
    success: bool
    overall_status: str
    pipeline_version: str
    started_at: datetime
    completed_at: datetime
    total_execution_time_ms: float = 0.0
    total_rows_processed: int = 0

    metadata: DatasetMetadata
    metrics: PipelineMetrics
    stage_metrics: list[StageMetrics] = Field(default_factory=list)
    warnings: list[PipelineWarning] = Field(default_factory=list)
    errors: list[PipelineError] = Field(default_factory=list)
