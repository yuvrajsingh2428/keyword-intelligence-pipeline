"""JSON report exporter."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from loguru import logger

from keyword_intelligence.reporting.exporters.base import ReportExporter
from keyword_intelligence.reporting.models import (
    ExporterCapabilities,
    ReportResult,
)


class JSONExporter(ReportExporter):
    """Exports the entire ReportResult as a serialised JSON file."""

    @property
    def exporter_name(self) -> str:
        """Unique name for this exporter."""
        return "json"

    @property
    def exporter_version(self) -> str:
        """Version of this exporter."""
        return "1.0.0"

    @property
    def capabilities(self) -> ExporterCapabilities:
        """Capabilities of this exporter."""
        return ExporterCapabilities(
            exporter_name=self.exporter_name,
            exporter_version=self.exporter_version,
            supported_extensions=[".json"],
            supports_streaming=False,
            supports_large_files=True,
        )

    def export(
        self,
        report: ReportResult,
        output_path: Path,
        **kwargs: Any,
    ) -> Path:
        """Export the full report as JSON.

        Args:
            report: The complete report result.
            output_path: File path to write to.
            **kwargs: Additional keyword arguments.

        Returns:
            The path to the written JSON file.
        """
        start = time.perf_counter()
        json_path = output_path.with_suffix(".json")
        json_path.parent.mkdir(parents=True, exist_ok=True)

        payload = report.model_dump(mode="json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)

        duration_ms = (time.perf_counter() - start) * 1000
        size_bytes = json_path.stat().st_size
        logger.info(
            f"JSONExporter: wrote {size_bytes:,} bytes "
            f"in {duration_ms:.1f}ms -> {json_path}"
        )
        return json_path
