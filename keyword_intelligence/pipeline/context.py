"""Pipeline context state container.

The PipelineContext is the single source of truth for a pipeline execution run.
It holds the current state of the dataset (pandas DataFrame) as it flows
through various stages, as well as configuration and services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

    from keyword_intelligence.config.settings import Settings


class PipelineContext:
    """State container for pipeline execution.

    Carries the pandas DataFrame and pipeline metadata through each stage.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize a new empty pipeline context."""
        self.settings = settings
        self._data: pd.DataFrame | None = None
        self.metadata: dict[str, Any] = {}
        self.errors: list[str] = []

    @property
    def data(self) -> pd.DataFrame:
        """Get the current pipeline dataset."""
        if self._data is None:
            raise RuntimeError("Pipeline data has not been initialized.")
        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        """Set the pipeline dataset."""
        import pandas as pd

        if not isinstance(value, pd.DataFrame):
            raise TypeError("Pipeline data must be a pandas DataFrame.")
        self._data = value

    @property
    def has_data(self) -> bool:
        """Check if the context has loaded data."""
        return self._data is not None

    def add_error(self, error: str) -> None:
        """Add an error message to the context."""
        self.errors.append(error)
