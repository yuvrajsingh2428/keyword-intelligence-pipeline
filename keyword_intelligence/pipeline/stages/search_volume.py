"""Pipeline stage adapter for Search Volume Engine."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage
from keyword_intelligence.search_volume.engine import SearchVolumeEngine


class SearchVolumeStage(BaseStage):
    """Pipeline stage that invokes the Search Volume Engine."""

    def __init__(self, engine: SearchVolumeEngine) -> None:
        """Initialize the stage with an engine instance."""
        self.engine = engine

    @property
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.SEARCH_VOLUME

    @property
    def stage_version(self) -> str:
        """Return the version of this stage implementation."""
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the search volume engine."""
        logger.info(f"Executing stage {self.stage_type.value}")

        result = self.engine.process(context)

        if result.statistics.unresolved_keywords > 0:
            context.add_warning(
                stage=self.stage_type.value,
                code="UNRESOLVED_KEYWORDS",
                message=f"Failed to fetch volume for {result.statistics.unresolved_keywords} keywords.",
            )

        return context
