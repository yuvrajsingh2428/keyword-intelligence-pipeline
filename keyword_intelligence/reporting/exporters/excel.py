"""Excel report exporter using openpyxl."""

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


class ExcelExporter(ReportExporter):
    """Exports a multi-sheet Excel workbook.

    Sheets:
    - Summary: Executive and technical summary rows.
    - Keywords: Full keyword dataset.
    - Statistics: Analytics distributions.
    - Pipeline Metrics: Stage timings and provider info.
    """

    @property
    def exporter_name(self) -> str:
        """Unique name for this exporter."""
        return "excel"

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
            supported_extensions=[".xlsx"],
            supports_streaming=False,
            supports_large_files=True,
        )

    def export(
        self,
        report: ReportResult,
        output_path: Path,
        **kwargs: Any,
    ) -> Path:
        """Export report as multi-sheet Excel workbook.

        Args:
            report: The complete report result.
            output_path: File path to write to.
            **kwargs: Additional keyword arguments (dataframe).

        Returns:
            The path to the written Excel file.
        """
        start = time.perf_counter()
        df: pd.DataFrame = kwargs.get("dataframe", pd.DataFrame())

        xlsx_path = output_path.with_suffix(".xlsx")
        xlsx_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(
            xlsx_path,
            engine="openpyxl",
        ) as writer:
            # Sheet 1 — Summary
            summary_data = {
                "Field": [
                    "Title",
                    "Generated At",
                    "Total Keywords",
                    "Relevant",
                    "Irrelevant",
                    "Avg Confidence",
                    "Top Category",
                    "Dominant Intent",
                    "Pipeline Health",
                    "Warnings",
                    "Errors",
                ],
                "Value": [
                    report.executive.title,
                    str(report.executive.generated_at),
                    report.executive.total_keywords_analysed,
                    report.executive.relevant_keywords,
                    report.executive.irrelevant_keywords,
                    round(
                        report.executive.average_confidence,
                        2,
                    ),
                    report.executive.top_category,
                    report.executive.dominant_intent,
                    report.executive.pipeline_health,
                    report.executive.warnings_count,
                    report.executive.errors_count,
                ],
            }
            pd.DataFrame(summary_data).to_excel(
                writer,
                sheet_name="Summary",
                index=False,
            )

            # Sheet 2 — Keywords
            df.to_excel(
                writer,
                sheet_name="Keywords",
                index=False,
            )

            # Sheet 3 — Statistics
            stats_rows: list[dict[str, object]] = []
            analytics = report.analytics
            stats_rows.append(
                {
                    "Metric": "Relevance - Relevant",
                    "Value": analytics.relevance.relevant,
                }
            )
            stats_rows.append(
                {
                    "Metric": "Relevance - Irrelevant",
                    "Value": analytics.relevance.irrelevant,
                }
            )
            stats_rows.append(
                {
                    "Metric": "Relevance - Uncertain",
                    "Value": analytics.relevance.uncertain,
                }
            )
            stats_rows.append(
                {
                    "Metric": "Avg Search Volume",
                    "Value": round(
                        analytics.search_volume.average_volume,
                        2,
                    ),
                }
            )
            stats_rows.append(
                {
                    "Metric": "Median Search Volume",
                    "Value": round(
                        analytics.search_volume.median_volume,
                        2,
                    ),
                }
            )
            for cat, cnt in analytics.categories.counts.items():
                stats_rows.append({"Metric": f"Category - {cat}", "Value": cnt})
            pd.DataFrame(stats_rows).to_excel(
                writer,
                sheet_name="Statistics",
                index=False,
            )

            # Sheet 4 — Pipeline Metrics
            metrics_rows: list[dict[str, object]] = []
            metrics_rows.append(
                {
                    "Metric": "Execution ID",
                    "Value": report.pipeline.execution_id,
                }
            )
            metrics_rows.append(
                {
                    "Metric": "Pipeline Version",
                    "Value": report.pipeline.pipeline_version,
                }
            )
            metrics_rows.append(
                {
                    "Metric": "Total Execution Time (ms)",
                    "Value": round(
                        report.pipeline.timing.total_execution_time_ms,
                        2,
                    ),
                }
            )
            for stage, ms in report.pipeline.timing.stage_timings.items():
                metrics_rows.append(
                    {"Metric": f"Stage - {stage}", "Value": round(ms, 2)}
                )
            pd.DataFrame(metrics_rows).to_excel(
                writer,
                sheet_name="Pipeline Metrics",
                index=False,
            )

        duration_ms = (time.perf_counter() - start) * 1000
        size_bytes = xlsx_path.stat().st_size
        logger.info(
            f"ExcelExporter: wrote {len(df)} rows "
            f"({size_bytes:,} bytes) in {duration_ms:.1f}ms "
            f"-> {xlsx_path}"
        )
        return xlsx_path
