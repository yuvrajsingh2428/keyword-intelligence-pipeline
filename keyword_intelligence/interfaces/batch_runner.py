"""Batch interface adapter for the Keyword Intelligence Pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from keyword_intelligence.models import PipelineConfig
from keyword_intelligence.pipeline.pipeline import Pipeline


class BatchRunner:
    """Service that scheduled jobs use to execute the pipeline."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        """Initialize the Batch Runner with configuration."""
        self.config = config or PipelineConfig()

        logger.add("logs/batch_pipeline.log", rotation="50 MB", level="INFO")

    def run(self, input_file: Path | str, output_dir: Path | str) -> dict[str, Any]:
        """Execute the pipeline in batch mode.

        Args:
            input_file: Path to the dataset.
            output_dir: Path to save the results.

        Returns:
            The execution summary dictionary.
        """
        input_path = Path(input_file)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Batch runner started for {input_path.name}")

        pipeline = Pipeline(config=self.config)

        try:
            result, context = pipeline.run(
                input_file=input_path,
                file_name=input_path.name,
            )

            if context.has_data:
                df = context.data
                output_csv = out_dir / f"batch_output_{result.execution_id}.csv"
                df.to_csv(output_csv, index=False)
                result.output_file_locations.append(str(output_csv))

            metrics_file = out_dir / f"batch_metrics_{result.execution_id}.json"
            with open(metrics_file, "w") as f:
                json.dump(result.metrics.model_dump(), f, indent=2)
            result.output_file_locations.append(str(metrics_file))

            summary_file = out_dir / f"batch_summary_{result.execution_id}.json"
            with open(summary_file, "w") as f:
                summary = result.execution_summary.copy()
                summary["output_files"] = result.output_file_locations
                json.dump(summary, f, indent=2)

            logger.info(f"Batch runner completed successfully for {input_path.name}")
            return summary

        except Exception as e:
            logger.exception("Batch execution failed")
            raise e
