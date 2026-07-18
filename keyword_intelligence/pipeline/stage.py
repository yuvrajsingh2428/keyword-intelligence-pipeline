"""Base class for pipeline stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyword_intelligence.pipeline.context import PipelineContext


class BaseStage(ABC):
    """Abstract base class for all pipeline stages."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the stage."""
        pass

    @abstractmethod
    def execute(self, context: PipelineContext) -> None:
        """Execute the stage logic on the given context.

        Args:
            context: The pipeline context containing the DataFrame.

        Raises:
            PipelineError: If the stage fails to execute successfully.
        """
        pass
