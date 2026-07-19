"""Base strategy interface for duplicate detection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyword_intelligence.duplicate_detection.config import DuplicateDetectionConfig
    from keyword_intelligence.duplicate_detection.models import DuplicateCandidate
    from keyword_intelligence.pipeline.context import PipelineContext


class DuplicateDetectionStrategy(ABC):
    """Abstract strategy for detecting duplicate keywords."""

    def __init__(self, config: DuplicateDetectionConfig) -> None:
        """Initialize the strategy with configuration."""
        self.config = config

    @property
    @abstractmethod
    def priority(self) -> int:
        """Execution priority (lower runs first)."""
        pass

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Unique identifier for this strategy."""
        pass

    @abstractmethod
    def detect(
        self, context: PipelineContext, exclude_keywords: set[str]
    ) -> list[DuplicateCandidate]:
        """Detect duplicate candidates in the dataset.

        Args:
            context: The pipeline context containing the DataFrame.
            exclude_keywords: Keywords that have already been matched with
                              high confidence and can be excluded to save time.

        Returns:
            A list of newly discovered duplicate candidates.
        """
        pass
