"""Pipeline context state container."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from keyword_intelligence.business_context.models import BusinessProfile
from keyword_intelligence.models.pipeline import (
    DatasetMetadata,
    PipelineError,
    PipelineMetrics,
    PipelineWarning,
    StageMetrics,
)

if TYPE_CHECKING:
    import pandas as pd

    from keyword_intelligence.config.settings import Settings


class PipelineContext:
    """State container for pipeline execution.

    Carries the pandas DataFrame, metadata, and structured warnings/errors
    through each stage of the pipeline.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize a new empty pipeline context."""
        self.settings = settings
        self.execution_id = str(uuid.uuid4())
        self._data: pd.DataFrame | None = None
        self.business_profile: BusinessProfile | None = None

        self.dataset_metadata = DatasetMetadata()
        self.pipeline_metrics = PipelineMetrics()
        self.stage_metrics: list[StageMetrics] = []

        self.warnings: list[PipelineWarning] = []
        self.errors: list[PipelineError] = []

    @property
    def data(self) -> pd.DataFrame:
        """Get the current pipeline dataset."""
        if self._data is None:
            raise RuntimeError("Pipeline data has not been initialized.")
        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        """Set the pipeline dataset."""
        import pandas as pd

        if not isinstance(value, pd.DataFrame):
            raise TypeError("Pipeline data must be a pandas DataFrame.")
        self._data = value

    @property
    def has_data(self) -> bool:
        """Check if the context has loaded data."""
        return self._data is not None

    def add_warning(self, stage: str, code: str, message: str) -> None:
        """Add a structured warning to the context."""
        self.warnings.append(PipelineWarning(stage=stage, code=code, message=message))
        self.pipeline_metrics.total_warnings += 1

    def add_error(self, stage: str, code: str, message: str) -> None:
        """Add a structured error to the context."""
        self.errors.append(PipelineError(stage=stage, code=code, message=message))
        self.pipeline_metrics.total_errors += 1
