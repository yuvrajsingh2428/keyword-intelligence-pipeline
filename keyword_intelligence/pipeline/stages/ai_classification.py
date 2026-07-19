"""Pipeline stage adapter for AI Classification Engine."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.ai_intelligence.engine import AIEngine
from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class AIClassificationStage(BaseStage):
    """Pipeline stage that invokes the AI Classification Engine."""

    def __init__(self, engine: AIEngine) -> None:
        """Initialize the stage with an engine instance."""
        self.engine = engine

    @property
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.AI_CLASSIFICATION

    @property
    def stage_version(self) -> str:
        """Return the version of this stage implementation."""
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the AI intelligence engine."""
        logger.info(f"Executing stage {self.stage_type.value}")

        self.engine.process(context)

        return context
