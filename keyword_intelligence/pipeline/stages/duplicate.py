"""Pipeline stage adapter for Duplicate Detection Engine."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.core.constants import StageType
from keyword_intelligence.duplicate_detection.engine import DuplicateDetectionEngine
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class DuplicateDetectionStage(BaseStage):
    """Pipeline stage that invokes the Duplicate Detection Engine."""

    def __init__(self, engine: DuplicateDetectionEngine) -> None:
        """Initialize the stage with an engine instance."""
        self.engine = engine

    @property
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.DUPLICATE_DETECTION

    @property
    def stage_version(self) -> str:
        """Return the version of this stage implementation."""
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the duplicate detection engine."""
        logger.info(f"Executing stage {self.stage_type.value}")

        result = self.engine.process(context)

        if result.duplicates_removed > 0:
            context.add_warning(
                stage=self.stage_type.value,
                code="DUPLICATES_REMOVED",
                message=f"Removed {result.duplicates_removed} duplicate keywords across {result.statistics.total_duplicate_groups} groups.",
            )

        return context
