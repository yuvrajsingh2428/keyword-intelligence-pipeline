"""Pipeline stage adapter for the Reporting Engine."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage
from keyword_intelligence.reporting.engine import ReportEngine


class ReportingStage(BaseStage):
    """Pipeline stage that invokes the Reporting Engine."""

    def __init__(self, engine: ReportEngine) -> None:
        """Initialise the stage with a ReportEngine.

        Args:
            engine: The configured ReportEngine instance.
        """
        self.engine = engine

    @property
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.REPORTING

    @property
    def stage_version(self) -> str:
        """Return the version of this stage."""
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the reporting engine.

        Args:
            context: The pipeline context.

        Returns:
            The unmodified pipeline context.
        """
        logger.info(f"Executing stage {self.stage_type.value}")
        self.engine.generate(context)
        return context
