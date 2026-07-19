"""Stage registry for dynamic stage management."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyword_intelligence.pipeline.stage import BaseStage


class StageRegistry:
    """Registry responsible for registering and ordering pipeline stages."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._stages: list[BaseStage] = []

    def register(self, stage: BaseStage) -> None:
        """Register a stage in the pipeline."""
        self._stages.append(stage)

    def clear(self) -> None:
        """Clear all registered stages."""
        self._stages.clear()

    def get_stages(self) -> list[BaseStage]:
        """Return the ordered list of registered stages.

        Currently returns them in the order they were registered.
        Future enhancements could perform dependency-based sorting here.
        """
        return list(self._stages)
