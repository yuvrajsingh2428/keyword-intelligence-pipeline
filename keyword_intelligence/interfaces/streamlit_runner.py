"""Streamlit interface adapter for the Keyword Intelligence Pipeline."""

from __future__ import annotations

import time

from loguru import logger

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.core.container import container
from keyword_intelligence.models.pipeline import PipelineResult
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.pipeline import Pipeline
from keyword_intelligence.reporting.engine import ReportEngine
from keyword_intelligence.reporting.models import ReportResult


class StreamlitRunner:
    """Service that Streamlit pages use to execute the pipeline."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise the runner with settings."""
        self.settings = settings or Settings()
        self._result: PipelineResult | None = None
        self._context: PipelineContext | None = None
        self._report: ReportResult | None = None
        self._logs: list[str] = []

    def run(
        self,
        file_bytes: bytes,
        file_name: str,
        company_name: str,
        website: str,
        industry: str = "",
        sheet_name: str | None = None,
        keyword_column: str | None = None,
    ) -> PipelineResult:
        """Execute the full pipeline on an uploaded file."""
        self._logs.clear()
        self._log(f"Starting pipeline for {file_name}")

        try:
            pipeline = Pipeline(settings=self.settings)

            self._log("Executing pipeline stages…")
            self._result, self._context = pipeline.run(
                input_file=file_bytes,
                file_name=file_name,
                company_name=company_name,
                website=website,
                industry=industry,
                sheet_name=sheet_name,
                keyword_column=keyword_column,
            )

            self._log(
                f"Pipeline finished: {self._result.overall_status} "
                f"in {self._result.total_execution_time_ms:.0f}ms"
            )

            # Generate report
            self._log("Generating report…")
            report_engine = container.resolve(ReportEngine)
            self._report = report_engine.generate(
                self._context,
                export_formats=[],  # UI handles exports in-memory
            )
            self._log("Report generation complete.")

        except Exception:
            self._log("Pipeline execution failed.")
            logger.exception("Pipeline execution failed")
            raise

        return self._result

    @property
    def context(self) -> PipelineContext | None:
        """Return the current pipeline context."""
        return self._context

    @property
    def result(self) -> PipelineResult | None:
        """Return the last pipeline result."""
        return self._result

    @property
    def report(self) -> ReportResult | None:
        """Return the last report result."""
        return self._report

    @property
    def logs(self) -> list[str]:
        """Return execution logs."""
        return list(self._logs)

    def _log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self._logs.append(entry)
        logger.info(msg)
