"""Pipeline orchestrator for managing stage execution, retries, and metrics."""

from __future__ import annotations

import time
import typing
from typing import TYPE_CHECKING

from loguru import logger

from keyword_intelligence.core.exceptions import PipelineError as CorePipelineError
from keyword_intelligence.models import PipelineResult, StageMetrics
from keyword_intelligence.pipeline.progress import NullProgressReporter

if TYPE_CHECKING:
    from keyword_intelligence.config.settings import Settings
    from keyword_intelligence.pipeline.cache import CacheProvider
    from keyword_intelligence.pipeline.context import PipelineContext
    from keyword_intelligence.pipeline.events import PipelineEventListener
    from keyword_intelligence.pipeline.progress import ProgressReporter
    from keyword_intelligence.pipeline.registry import StageRegistry
    from keyword_intelligence.pipeline.stage import BaseStage


class PipelineOrchestrator:
    """Orchestrates the execution of pipeline stages.

    Handles metrics collection, execution timing, checksum caching hooks,
    failure routing, and retries based on configuration.
    """

    def __init__(
        self,
        settings: Settings,
        registry: StageRegistry,
        listeners: list[PipelineEventListener] | None = None,
        cache_provider: CacheProvider | None = None,
        progress_reporter: ProgressReporter | None = None,
    ) -> None:
        """Initialize the orchestrator with configuration and dependencies."""
        self.settings = settings
        self.registry = registry
        self.listeners = listeners or []
        self.cache_provider = cache_provider
        self.progress = progress_reporter or NullProgressReporter()

    def _trigger_event(
        self, event_name: str, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        """Helper to invoke a specific event hook on all listeners."""
        for listener in self.listeners:
            try:
                method = getattr(listener, event_name)
                method(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Listener {listener.__class__.__name__}.{event_name} failed: {e}"
                )

    def _execute_stage_with_retries(
        self, stage: BaseStage, context: PipelineContext
    ) -> StageMetrics:
        """Execute a stage, applying retries on failure, timing it and returning metrics."""
        max_retries = self.settings.max_stage_retries
        retry_delay = self.settings.retry_delay_ms / 1000.0

        for attempt in range(1, max_retries + 2):  # attempts = retries + 1
            try:
                with logger.contextualize(
                    execution_id=context.execution_id, stage=stage.stage_type.value
                ):
                    # Remove debug start log

                    self._trigger_event("before_stage", stage.stage_type, context)

                    from datetime import datetime

                    absolute_start = datetime.utcnow()
                    start_time = time.perf_counter()

                    initial_rows = len(context.data) if context.has_data else 0
                    initial_warnings = len(context.warnings)
                    initial_errors = len(context.errors)

                    # Execute the stage
                    context = stage.execute(context)

                    end_time = time.perf_counter()
                    absolute_end = datetime.utcnow()
                    duration_ms = (end_time - start_time) * 1000

                    final_rows = len(context.data) if context.has_data else 0

                    metrics = StageMetrics(
                        stage_name=stage.stage_type.value,
                        start_time=absolute_start,
                        end_time=absolute_end,
                        rows_loaded=initial_rows,
                        rows_output=final_rows,
                        rows_removed=(
                            initial_rows - final_rows
                            if initial_rows > final_rows
                            else 0
                        ),
                        processing_time_ms=duration_ms,
                        success=True,
                        warnings_count=len(context.warnings) - initial_warnings,
                        errors_count=len(context.errors) - initial_errors,
                        warnings=[
                            w.message for w in context.warnings[initial_warnings:]
                        ],
                        exceptions=[e.message for e in context.errors[initial_errors:]],
                    )

                    stage_name = stage.stage_type.value
                    
                    rows_added = final_rows - initial_rows if final_rows > initial_rows else 0
                    rows_removed = initial_rows - final_rows if initial_rows > final_rows else 0
                    
                    # Compute rows modified via is_normalized if available, or 0 if not tracked.
                    rows_modified = 0
                    if context.has_data and "is_normalized" in context.data.columns:
                        rows_modified = int(context.data["is_normalized"].sum())
                    
                    stage_specific = context.stage_diagnostics.get(stage_name, "")
                    if stage_specific:
                        stage_specific = f"\n{stage_specific}"
                    
                    warnings_count = len(context.warnings) - initial_warnings
                    errors_count = len(context.errors) - initial_errors
                    
                    if self.settings.debug:
                        trace_block = (
                            f"--------------------------------------------------\n"
                            f"Stage: {stage_name}\n"
                            f"--------------------------------------------------\n"
                            f"Rows In: {initial_rows}\n"
                            f"Rows Out: {final_rows}\n"
                            f"Rows Modified: {rows_modified}\n"
                            f"Rows Removed: {rows_removed}\n"
                            f"Rows Added: {rows_added}\n"
                            f"Execution Time: {duration_ms / 1000.0:.2f} sec\n"
                            f"Warnings: {warnings_count}\n"
                            f"Errors: {errors_count}\n"
                            f"{stage_specific}\n"
                            f"--------------------------------------------------"
                        )
                        print(trace_block)
                    else:
                        if errors_count > 0:
                            print(f"{stage_name} ERROR")
                        else:
                            print(f"{stage_name} ✓")

                    self._trigger_event("after_stage", stage.stage_type, context)
                    return metrics

            except Exception as e:
                logger.exception(
                    f"Stage '{stage.stage_type.value}' failed on attempt {attempt}",
                    execution_id=context.execution_id,
                )
                self._trigger_event("on_error", stage.stage_type, e, context)

                if attempt > max_retries:
                    raise  # Exhausted retries
                time.sleep(retry_delay)

        # Should never be reached due to raise inside the loop
        raise CorePipelineError("Exhausted retries unexpectedly.")

    def run(self, context: PipelineContext) -> PipelineResult:
        """Run all registered stages on the given context."""
        logger.info(f"Starting pipeline execution: {context.execution_id}")
        start_time = time.perf_counter()

        # Set started_at for metrics (if model has it, or just pass it in constructor)
        from datetime import datetime

        started_at = datetime.utcnow()

        self._trigger_event("before_pipeline", context)
        self.progress.start()

        stages = self.registry.get_stages()
        total_stages = len(stages)

        for idx, stage in enumerate(stages):
            try:
                metrics = self._execute_stage_with_retries(stage, context)
                context.stage_metrics.append(metrics)

                context.pipeline_metrics.total_time_ms += metrics.processing_time_ms
                context.pipeline_metrics.total_rows_removed += metrics.rows_removed

                self.progress.update(stage.stage_type.value, (idx + 1) / total_stages)

            except Exception as e:
                logger.exception(
                    f"Pipeline failed critically at stage '{stage.stage_type.value}'",
                    execution_id=context.execution_id,
                )
                context.add_error(
                    stage=stage.stage_type.value,
                    code="STAGE_FAILURE",
                    message=f"Failed after retries: {e}",
                )

                if self.settings.stop_on_error:
                    logger.warning(
                        "STOP_ON_ERROR is enabled. Halting pipeline.",
                        execution_id=context.execution_id,
                    )
                    break

        # Checksum caching hook
        self._cache_checksum_hook(context)

        total_duration = (time.perf_counter() - start_time) * 1000
        context.pipeline_metrics.total_time_ms = total_duration
        if context.has_data:
            context.pipeline_metrics.total_rows_processed = len(context.data)

        success = len(context.errors) == 0
        overall_status = "SUCCESS" if success else "FAILED"
        completed_at = datetime.utcnow()

        logger.info(
            f"Pipeline execution finished. Status: {overall_status}. "
            f"Total time: {total_duration:.2f}ms. "
            f"Total errors: {len(context.errors)}.",
            execution_id=context.execution_id,
        )

        self.progress.finish()

        # Update dataset metadata pipeline version
        from keyword_intelligence.core.constants import PIPELINE_VERSION

        context.dataset_metadata.detected_schema_version = PIPELINE_VERSION

        result = PipelineResult(
            execution_id=context.execution_id,
            success=success,
            overall_status=overall_status,
            pipeline_version=PIPELINE_VERSION,
            started_at=started_at,
            completed_at=completed_at,
            metadata=context.dataset_metadata,
            metrics=context.pipeline_metrics,
            stage_metrics=context.stage_metrics,
            warnings=context.warnings,
            errors=context.errors,
            total_execution_time_ms=total_duration,
            total_rows_processed=context.pipeline_metrics.total_rows_processed,
        )

        self._trigger_event("after_pipeline", result)

        return result

    def _cache_checksum_hook(self, context: PipelineContext) -> None:
        """Hook to cache and reuse identical checksum processing in future."""
        if context.dataset_metadata.checksum and self.cache_provider:
            if not self.cache_provider.exists(context.dataset_metadata.checksum):
                logger.debug(
                    f"Checksum {context.dataset_metadata.checksum} recorded for future caching.",
                    execution_id=context.execution_id,
                )
                # In a real implementation we would cache the result/dataframe here
                # self.cache_provider.put(context.dataset_metadata.checksum, context.data)
