"""Pipeline runner service — the only place pages talk to the pipeline."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from loguru import logger

from keyword_intelligence.ai_intelligence.engine import AIEngine
from keyword_intelligence.config.settings import Settings
from keyword_intelligence.core.container import container
from keyword_intelligence.duplicate_detection.engine import (
    DuplicateDetectionEngine,
)
from keyword_intelligence.models.pipeline import PipelineResult
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.orchestrator import PipelineOrchestrator
from keyword_intelligence.pipeline.registry import StageRegistry
from keyword_intelligence.pipeline.stages.ai_classification import (
    AIClassificationStage,
)
from keyword_intelligence.pipeline.stages.business_context import (
    BusinessContextStage,
)
from keyword_intelligence.pipeline.stages.duplicate import (
    DuplicateDetectionStage,
)
from keyword_intelligence.pipeline.stages.loader import LoaderStage
from keyword_intelligence.pipeline.stages.preprocessor import PreprocessorStage
from keyword_intelligence.pipeline.stages.search_volume import (
    SearchVolumeStage,
)
from keyword_intelligence.pipeline.stages.validator import ValidatorStage
from keyword_intelligence.reporting.engine import ReportEngine
from keyword_intelligence.reporting.models import ReportResult
from keyword_intelligence.search_volume.engine import SearchVolumeEngine


class PipelineRunner:
    """Service that pages use to execute the pipeline.

    Pages should never instantiate orchestrators or stages directly.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise the runner with settings.

        Args:
            settings: Optional Settings override.
        """
        self.settings = settings or Settings()
        self._result: PipelineResult | None = None
        self._context: PipelineContext | None = None
        self._report: ReportResult | None = None
        self._logs: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        file_bytes: bytes,
        file_name: str,
        company_name: str,
        website: str,
        industry: str = "",
    ) -> PipelineResult:
        """Execute the full pipeline on an uploaded file.

        Args:
            file_bytes: Raw file content.
            file_name: Original filename (used for extension detection).
            company_name: Company name for Business Profile.
            website: Website URL for Business Profile.
            industry: Optional industry hint.

        Returns:
            The PipelineResult produced by the orchestrator.
        """
        self._logs.clear()
        self._log(f"Starting pipeline for {file_name}")

        # Write to a temp file so the loader stage can read it
        suffix = Path(file_name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            # Build registry via Container (which provides singletons/transients)
            registry = container.resolve(StageRegistry)
            # Add dynamic loader stage (file-specific)
            registry.register(LoaderStage(tmp_path))
            registry.register(ValidatorStage())
            registry.register(PreprocessorStage())
            # Duplicate, Search Volume and AI are automatically registered via bootstrap
            # Actually, to avoid breaking tests, we just use orchestrator from container.
            # But the orchestrator needs the dynamic loader stage. Let's just create
            # a new instance here or register the file-specific stage dynamically.

            # Rebuilding registry for this run:
            from keyword_intelligence.business_context.engine import (
                BusinessContextEngine,
            )

            registry = StageRegistry()
            registry.register(LoaderStage(tmp_path))
            registry.register(ValidatorStage())
            registry.register(PreprocessorStage())
            registry.register(
                BusinessContextStage(
                    container.resolve(BusinessContextEngine),
                    company_name=company_name,
                    website=website,
                    industry=industry,
                )
            )
            registry.register(
                DuplicateDetectionStage(container.resolve(DuplicateDetectionEngine))
            )
            registry.register(SearchVolumeStage(container.resolve(SearchVolumeEngine)))
            registry.register(AIClassificationStage(container.resolve(AIEngine)))

            orchestrator = PipelineOrchestrator(
                settings=self.settings,
                registry=registry,
            )

            self._context = PipelineContext(self.settings)
            self._log("Executing pipeline stages…")
            self._result = orchestrator.run(self._context)
            self._log(
                f"Pipeline finished: {self._result.overall_status} "
                f"in {self._result.total_execution_time_ms:.0f}ms"
            )

            # Generate report
            self._log("Generating report…")
            report_engine = container.resolve(ReportEngine)
            self._report = report_engine.generate(
                self._context,
                export_formats=["json"],
                output_dir=str(tmp_path.parent),
            )
            self._log("Report generation complete.")

        except Exception:
            self._log("Pipeline execution failed.")
            logger.exception("Pipeline execution failed")
            raise
        finally:
            tmp_path.unlink(missing_ok=True)

        return self._result

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self._logs.append(entry)
        logger.info(msg)
