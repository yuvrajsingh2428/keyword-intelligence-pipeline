"""Base class for pipeline stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyword_intelligence.core.constants import StageType
    from keyword_intelligence.pipeline.context import PipelineContext


class BaseStage(ABC):
    """Abstract base class for all pipeline stages."""

    @property
    @abstractmethod
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        pass

    @property
    @abstractmethod
    def stage_version(self) -> str:
        """Return the version of the stage."""
        pass

    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the stage logic on the given context.

        Args:
            context: The pipeline context containing the DataFrame.

        Returns:
            The modified pipeline context.

        Raises:
            PipelineError: If the stage fails to execute successfully.
        """
        pass
