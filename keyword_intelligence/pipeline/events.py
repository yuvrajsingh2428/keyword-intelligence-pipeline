"""Pipeline event listeners for hooks and callbacks."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyword_intelligence.core.constants import StageType
    from keyword_intelligence.models import PipelineResult
    from keyword_intelligence.pipeline.context import PipelineContext


class PipelineEventListener(ABC):
    """Interface for hooking into pipeline lifecycle events."""

    def before_pipeline(self, context: PipelineContext) -> None:
        """Invoked before the pipeline orchestrator begins running stages."""
        pass

    def after_pipeline(self, result: PipelineResult) -> None:
        """Invoked after the pipeline completes, regardless of success/failure."""
        pass

    def before_stage(self, stage_type: StageType, context: PipelineContext) -> None:
        """Invoked just before a specific stage begins execution."""
        pass

    def after_stage(self, stage_type: StageType, context: PipelineContext) -> None:
        """Invoked immediately after a specific stage completes execution successfully."""
        pass

    def on_error(
        self, stage_type: StageType, error: Exception, context: PipelineContext
    ) -> None:
        """Invoked when an exception is caught during stage execution."""
        pass
