"""Progress reporter abstractions for pipeline execution UI tracking."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProgressReporter(ABC):
    """Interface for tracking and reporting pipeline progress."""

    @abstractmethod
    def start(self) -> None:
        """Called when the pipeline begins execution."""
        pass

    @abstractmethod
    def update(self, stage: str, percentage: float) -> None:
        """Called to report execution progress.

        Args:
            stage: The name or type of the currently executing stage.
            percentage: A float representing completion (0.0 to 1.0).
        """
        pass

    @abstractmethod
    def finish(self) -> None:
        """Called when the pipeline completes execution."""
        pass


class NullProgressReporter(ProgressReporter):
    """A no-op implementation of ProgressReporter used by default."""

    def start(self) -> None:
        """Do nothing."""
        pass

    def update(self, stage: str, percentage: float) -> None:
        """Do nothing."""
        pass

    def finish(self) -> None:
        """Do nothing."""
        pass
