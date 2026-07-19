"""High-level reporting engine orchestrating analytics and export."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
from loguru import logger

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.core.constants import PIPELINE_VERSION
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.reporting.analytics import AnalyticsEngine
from keyword_intelligence.reporting.config import ReportEngineConfig
from keyword_intelligence.reporting.exporters.csv import CSVExporter
from keyword_intelligence.reporting.exporters.excel import ExcelExporter
from keyword_intelligence.reporting.exporters.json import JSONExporter
from keyword_intelligence.reporting.models import (
    ExecutiveSummary,
    PipelineSummary,
    ReportResult,
    TechnicalSummary,
)
from keyword_intelligence.reporting.registry import (
    ExporterRegistry,
    ExporterResolver,
)


class ReportEngine:
    """Facade consuming PipelineContext to produce exported reports.

    Computes analytics, assembles a ReportResult, and invokes the
    configured exporter.  The engine contains no exporter-specific
    logic: it delegates to the resolved ReportExporter entirely.
    """

    def __init__(
        self,
        settings: Settings,
        registry: ExporterRegistry | None = None,
        analytics: AnalyticsEngine | None = None,
    ) -> None:
        """Initialise the report engine.

        Args:
            settings: Global application settings.
            registry: Optional pre-populated exporter registry.
            analytics: Optional analytics engine override.
        """
        self.config = ReportEngineConfig.from_settings(settings)
        self.analytics = analytics or AnalyticsEngine()

        if registry is None:
            registry = ExporterRegistry()
            registry.register(CSVExporter())
            registry.register(ExcelExporter())
            registry.register(JSONExporter())
        self.resolver = ExporterResolver(registry)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        context: PipelineContext,
        export_formats: list[str] | None = None,
        output_dir: str | None = None,
    ) -> ReportResult:
        """Generate the report and export it.

        Args:
            context: The fully-processed pipeline context.
            export_formats: Formats to export (defaults to config).
            output_dir: Override output directory.

        Returns:
            A populated ReportResult.
        """
        start = time.perf_counter()
        logger.info("ReportEngine: starting report generation.")

        formats = export_formats or [self.config.report_format]
        out_dir = Path(output_dir or self.config.output_dir)

        # 1. Compute analytics
        analytics_summary = self.analytics.compute(context)
        timing = self.analytics.compute_timing(context)

        # 2. Assemble summaries
        df = context.data if context.has_data else pd.DataFrame()

        avg_conf = 0.0
        if "ai_confidence" in df.columns:
            valid_conf = pd.to_numeric(df["ai_confidence"], errors="coerce").dropna()
            if not valid_conf.empty:
                avg_conf = float(valid_conf.mean())

        top_cat = ""
        if analytics_summary.categories.counts:
            top_cat = max(
                analytics_summary.categories.counts,
                key=analytics_summary.categories.counts.get,  # type: ignore[arg-type]
            )

        dominant_intent = self._dominant_intent(analytics_summary)

        health = "HEALTHY"
        if context.pipeline_metrics.total_errors > 0:
            health = "DEGRADED"

        executive = ExecutiveSummary(
            total_keywords_analysed=len(df),
            relevant_keywords=analytics_summary.relevance.relevant,
            irrelevant_keywords=analytics_summary.relevance.irrelevant,
            average_confidence=round(avg_conf, 2),
            top_category=top_cat,
            dominant_intent=dominant_intent,
            pipeline_health=health,
            warnings_count=context.pipeline_metrics.total_warnings,
            errors_count=context.pipeline_metrics.total_errors,
        )

        stages_executed = [sm.stage_name for sm in context.stage_metrics]
        technical = TechnicalSummary(
            execution_id=context.execution_id,
            pipeline_version=PIPELINE_VERSION,
            stages_executed=stages_executed,
            timing=timing,
            dataset=analytics_summary.dataset,
            warnings=[
                {"stage": w.stage, "code": w.code, "message": w.message}
                for w in context.warnings
            ],
            errors=[
                {"stage": e.stage, "code": e.code, "message": e.message}
                for e in context.errors
            ],
        )

        pipeline_summary = PipelineSummary(
            execution_id=context.execution_id,
            pipeline_version=PIPELINE_VERSION,
            total_rows_processed=len(df),
            timing=timing,
        )

        report = ReportResult(
            executive=executive,
            business_profile=context.business_profile,
            technical=technical,
            analytics=analytics_summary,
            pipeline=pipeline_summary,
        )

        # 3. Export
        for fmt in formats:
            exporter = self.resolver.resolve(fmt)
            base_name = f"report_{context.execution_id[:8]}"
            path = out_dir / base_name
            exported = exporter.export(report, path, dataframe=df)
            report.exported_files.append(str(exported))

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"ReportEngine: completed in {duration_ms:.1f}ms. "
            f"Exported: {report.exported_files}"
        )
        return report

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dominant_intent(
        analytics: object,
    ) -> str:
        """Determine the most frequent intent classification."""
        from keyword_intelligence.reporting.models import AnalyticsSummary

        if not isinstance(analytics, AnalyticsSummary):
            return ""
        intent = analytics.intent
        mapping = {
            "Informational": intent.informational,
            "Commercial": intent.commercial,
            "Transactional": intent.transactional,
            "Navigational": intent.navigational,
            "Unknown": intent.unknown,
        }
        if not any(mapping.values()):
            return ""
        return max(mapping, key=mapping.get)  # type: ignore[arg-type]
