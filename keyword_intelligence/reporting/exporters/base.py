"""Base exporter interface for report output."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from keyword_intelligence.reporting.models import (
    ExporterCapabilities,
    ReportResult,
)


class ReportExporter(ABC):
    """Abstract interface for all report exporters."""

    @property
    @abstractmethod
    def exporter_name(self) -> str:
        """Unique name for this exporter."""

    @property
    @abstractmethod
    def exporter_version(self) -> str:
        """Version of this exporter implementation."""

    @property
    @abstractmethod
    def capabilities(self) -> ExporterCapabilities:
        """Capabilities supported by this exporter."""

    @abstractmethod
    def export(
        self,
        report: ReportResult,
        output_path: Path,
        **kwargs: object,
    ) -> Path:
        """Export the report to the given path.

        Args:
            report: The complete ReportResult to export.
            output_path: Destination file or directory path.
            **kwargs: Additional keyword arguments.

        Returns:
            The path to the exported file.
        """
