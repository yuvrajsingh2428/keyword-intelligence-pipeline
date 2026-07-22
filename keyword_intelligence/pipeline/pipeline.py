"""Core Pipeline execution facade."""

from __future__ import annotations

import tempfile
from pathlib import Path

from loguru import logger

from keyword_intelligence.ai_intelligence.engine import AIEngine
from keyword_intelligence.config.settings import Settings
from keyword_intelligence.core.container import container
from keyword_intelligence.duplicate_detection.engine import DuplicateDetectionEngine
from keyword_intelligence.models.pipeline import PipelineConfig, PipelineResult
from keyword_intelligence.normalization.engine import NormalizationEngine
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.events import PipelineEventListener
from keyword_intelligence.pipeline.orchestrator import PipelineOrchestrator
from keyword_intelligence.pipeline.registry import StageRegistry
from keyword_intelligence.pipeline.stages.ai_classification import AIClassificationStage
from keyword_intelligence.pipeline.stages.business_context import BusinessContextStage
from keyword_intelligence.pipeline.stages.duplicate import DuplicateDetectionStage
from keyword_intelligence.pipeline.stages.loader import LoaderStage
from keyword_intelligence.pipeline.stages.normalization import NormalizationStage
from keyword_intelligence.pipeline.stages.preprocessor import PreprocessorStage
from keyword_intelligence.pipeline.stages.search_volume import SearchVolumeStage
from keyword_intelligence.pipeline.stages.validator import ValidatorStage
from keyword_intelligence.search_volume.engine import SearchVolumeEngine


class Pipeline:
    """Universal execution external engine for the Keyword Intelligence pipeline."""

    def __init__(
        self,
        settings: Settings | None = None,
        config: PipelineConfig | None = None,
        listeners: list[PipelineEventListener] | None = None,
    ) -> None:
        """Initialize pipeline with configuration and optional listeners."""
        self.settings = settings or Settings()
        self.config = config or PipelineConfig()
        self.listeners = listeners or []

    def run(
        self,
        input_file: str | Path | bytes,
        file_name: str = "dataset.csv",
        company_name: str = "",
        website: str = "",
        industry: str = "",
        sheet_name: str | None = None,
        keyword_column: str | None = None,
    ) -> tuple[PipelineResult, PipelineContext]:
        """Execute the pipeline sequentially."""
        tmp_path = None
        # Handle file input (bytes or path)
        if isinstance(input_file, bytes):
            suffix = Path(file_name).suffix.lower() if file_name else ".csv"
            ext = suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(input_file)
                tmp_path = Path(tmp.name)
        else:
            tmp_path = Path(input_file)
            ext = tmp_path.suffix.lower()

        import json
        import uuid
        from datetime import datetime

        run_id = str(uuid.uuid4())
        output_dir = Path(self.config.report_directory) / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        log_file = output_dir / "pipeline.log"
        log_handler = logger.add(log_file, format="{time} | {level} | {message}")

        logger.info(f"Starting pipeline execution for {file_name}. Run ID: {run_id}")

        result = None
        context = PipelineContext(self.settings)

        try:
            # Rebuild registry conditionally based on config
            registry = StageRegistry()
            registry.register(
                LoaderStage(
                    file_path=tmp_path,
                    file_name=file_name,
                    sheet_name=sheet_name,
                    keyword_column=keyword_column,
                )
            )

            if self.config.enable_validation:
                registry.register(ValidatorStage())

            if self.config.enable_preprocessing:
                registry.register(PreprocessorStage())

            if self.config.enable_normalization:
                registry.register(
                    NormalizationStage(container.resolve(NormalizationEngine))
                )

            if self.config.enable_duplicate_detection:
                registry.register(
                    DuplicateDetectionStage(container.resolve(DuplicateDetectionEngine))
                )

            # Conditionally register business context if provided
            if self.config.enable_business_context:
                from keyword_intelligence.business_context.engine import (
                    BusinessContextEngine,
                )

                registry.register(
                    BusinessContextStage(
                        container.resolve(BusinessContextEngine),
                        company_name=company_name,
                        website=website,
                        industry=industry,
                    )
                )

            if self.config.enable_decision_engine:
                from keyword_intelligence.decision.engine import DecisionEngine
                from keyword_intelligence.pipeline.stages.decision import (
                    DecisionEngineStage,
                )

                # Configure decision engine with pipeline config thresholds dynamically
                decision_engine = container.resolve(DecisionEngine)
                decision_engine.confidence_threshold = (
                    self.config.decision_confidence_threshold
                )
                decision_engine.review_threshold = self.config.decision_review_threshold

                registry.register(DecisionEngineStage(decision_engine))

            if self.config.enable_search_volume:
                registry.register(
                    SearchVolumeStage(container.resolve(SearchVolumeEngine))
                )

            if self.config.enable_ai:
                registry.register(AIClassificationStage(container.resolve(AIEngine)))

            from keyword_intelligence.business_context.engine import (
                BusinessContextEngine,
            )
            from keyword_intelligence.pipeline.stages.final_classification import (
                FinalClassificationStage,
            )

            registry.register(
                FinalClassificationStage(
                    container.resolve(BusinessContextEngine), company_name, website
                )
            )

            all_listeners = self.listeners

            orchestrator = PipelineOrchestrator(
                settings=self.settings,
                registry=registry,
                listeners=all_listeners,
            )

            result = orchestrator.run(context)

        except Exception as e:
            logger.exception(f"Pipeline execution failed critically: {e}")

            from keyword_intelligence.core.constants import PIPELINE_VERSION

            context.add_error(
                stage="PIPELINE",
                code="CRITICAL_FAILURE",
                message=str(e),
            )

            result = PipelineResult(
                execution_id=context.execution_id,
                success=False,
                overall_status="FAILED",
                pipeline_version=PIPELINE_VERSION,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                metadata=context.dataset_metadata,
                metrics=context.pipeline_metrics,
                stage_metrics=context.stage_metrics,
                warnings=context.warnings,
                errors=context.errors,
            )

        finally:
            if isinstance(input_file, bytes) and tmp_path and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

            # Artifact Generation
            try:
                if result:
                    # 1. Generate execution summary stats
                    summary = {
                        "run_id": run_id,
                        "status": result.overall_status,
                        "total_time_ms": result.total_execution_time_ms,
                        "rows_processed": result.total_rows_processed,
                        "rows_dropped": result.metrics.total_rows_removed,
                        "errors_count": len(result.errors),
                        "input_file_type": "Excel"
                        if ext in [".xlsx", ".xls"]
                        else "CSV",
                        "input_file_name": file_name,
                        "selected_sheet": sheet_name
                        if ext in [".xlsx", ".xls"]
                        else None,
                        "columns_loaded": context.dataset_metadata.total_columns,
                        "original_column_name": context.dataset_metadata.resolved_keyword_column,
                        "mapped_column": "keyword",
                        "resolution_method": context.dataset_metadata.resolution_method,
                        "resolution_confidence": context.dataset_metadata.resolution_confidence,
                    }

                    if context.has_data:
                        df = context.data

                        # Apply Quality Gates
                        if len(df) == 0:
                            raise ValueError(
                                "Pipeline Quality Gate Failed: No keywords processed."
                            )
                        if "relevant" in df.columns and int(df["relevant"].sum()) == 0:
                            raise ValueError(
                                "Pipeline Quality Gate Failed: 100% of keywords classified as irrelevant."
                            )
                        if (
                            "processing_method" in df.columns
                            and (df["processing_method"] == "AI").all()
                        ):
                            raise ValueError(
                                "Pipeline Quality Gate Failed: 100% AI usage detected. Deterministic logic bypassed."
                            )
                        if "decision_confidence" in df.columns:
                            invalid_conf = df[
                                ~df["decision_confidence"].between(0.0, 1.0)
                            ]
                            if not invalid_conf.empty:
                                raise ValueError(
                                    "Pipeline Quality Gate Failed: Confidence score outside range 0-1."
                                )

                        required_cols = ["keyword", "relevant", "processing_method"]
                        missing = [c for c in required_cols if c not in df.columns]
                        if missing:
                            raise ValueError(
                                f"Pipeline Quality Gate Failed: Missing required output columns {missing}."
                            )

                        if "duplicate_group_id" in df.columns:
                            summary["duplicate_groups_created"] = int(
                                df["duplicate_group_id"].nunique()
                            )
                        if "is_normalized" in df.columns:
                            summary["normalization_changes"] = int(
                                df["is_normalized"].sum()
                            )
                        if "decision" in df.columns:
                            summary["decisions"] = (
                                df["decision"].value_counts().to_dict()
                            )

                        total_rows = len(df)
                        duplicates = (
                            int((df["status"] == "DUPLICATE").sum())
                            if "status" in df.columns
                            else 0
                        )
                        active = total_rows - duplicates

                        summary["Rows Read"] = total_rows
                        summary["Unique Keywords"] = active
                        summary["Duplicate Keywords"] = duplicates
                        summary["Relevant"] = (
                            int((df["relevant"] == True).sum())
                            if "relevant" in df.columns
                            else 0
                        )
                        summary["Irrelevant"] = active - summary["Relevant"]

                        summary["Deterministic"] = (
                            int((df["processing_method"] == "Deterministic").sum())
                            if "processing_method" in df.columns
                            else 0
                        )
                        summary["AI"] = (
                            int((df["processing_method"] == "AI").sum())
                            if "processing_method" in df.columns
                            else 0
                        )
                        summary["AI Reduction %"] = (
                            f"{(summary['Deterministic'] / active * 100):.1f}%"
                            if active > 0
                            else "0.0%"
                        )

                        summary["Runtime"] = (
                            f"{round(result.total_execution_time_ms / 1000.0, 2)} sec"
                        )

                        # Generate Health Report
                        health = {
                            "Dictionary Load Success": True,
                            "Business Context Coverage": f"{(int(df['business_brand'].notna().sum()) / total_rows * 100):.1f}%"
                            if total_rows > 0
                            else "0.0%",
                            "AI Usage %": f"{(summary['AI'] / active * 100):.1f}%"
                            if active > 0
                            else "0.0%",
                            "Duplicate Reduction %": f"{(duplicates / total_rows * 100):.1f}%"
                            if total_rows > 0
                            else "0.0%",
                            "Normalization %": f"{(int(df['is_normalized'].sum()) / total_rows * 100):.1f}%"
                            if "is_normalized" in df.columns and total_rows > 0
                            else "0.0%",
                            "Average Confidence": f"{df['decision_confidence'].mean():.2f}"
                            if "decision_confidence" in df.columns
                            else "0.00",
                            "Pipeline Runtime": summary["Runtime"],
                            "Warnings": [w.message for w in context.warnings],
                        }

                    result.execution_summary = summary

                    # 2. Export Artifacts
                    from keyword_intelligence.exporters.export_manager import (
                        ExportManager,
                    )

                    manager = ExportManager()

                    timestamp_dir = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    output_dir = Path(self.config.report_directory) / timestamp_dir

                    exported_files = manager.export(result, context, output_dir)

                    # Export Health Report
                    import json

                    health_path = output_dir / "pipeline_health.json"
                    with open(health_path, "w") as f:
                        json.dump(health, f, indent=2)
                    exported_files.append(str(health_path.absolute()))

                    result.output_file_locations.extend(exported_files)

            except Exception as artifact_e:
                logger.error(f"Failed to write execution artifacts: {artifact_e}")

            # Stop capturing logs for this run
            logger.remove(log_handler)

        return result, context
