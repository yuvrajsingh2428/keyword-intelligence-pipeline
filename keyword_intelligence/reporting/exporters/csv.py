"""CSV report exporter."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from keyword_intelligence.reporting.exporters.base import ReportExporter
from keyword_intelligence.reporting.models import (
    ExporterCapabilities,
    ReportResult,
)


class CSVExporter(ReportExporter):
    """Exports the keyword dataset as a flat CSV file.

    Columns exported:
    keyword, relevance, category, intent, quality,
    ai_confidence, search_volume, duplicate_status.
    """

    @property
    def exporter_name(self) -> str:
        """Unique name for this exporter."""
        return "csv"

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
            supported_extensions=[".csv"],
            supports_streaming=True,
            supports_large_files=True,
        )

    def export(
        self,
        report: ReportResult,
        output_path: Path,
        **kwargs: Any,
    ) -> Path:
        """Export keyword data as CSV.

        Args:
            report: The complete report result.
            **kwargs: Additional keyword arguments (dataframe).
            output_path: File path to write to.

        Returns:
            The path to the written CSV file.
        """
        start = time.perf_counter()
        df: pd.DataFrame = kwargs.get("dataframe", pd.DataFrame())

        csv_path = output_path.with_suffix(".csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(csv_path, index=False, encoding="utf-8")

        duration_ms = (time.perf_counter() - start) * 1000
        size_bytes = csv_path.stat().st_size
        logger.info(
            f"CSVExporter: wrote {len(df)} rows "
            f"({size_bytes:,} bytes) in {duration_ms:.1f}ms "
            f"-> {csv_path}"
        )
        return csv_path
