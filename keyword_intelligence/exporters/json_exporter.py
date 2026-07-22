"""JSON exporters for pipeline metadata."""

import json
from pathlib import Path

from loguru import logger

from keyword_intelligence.exporters.base import BaseExporter
from keyword_intelligence.models import PipelineResult
from keyword_intelligence.pipeline.context import PipelineContext


class JSONExporter(BaseExporter):
    """Generates execution_summary.json, pipeline_metrics.json, and stage_metrics.json."""

    def export(
        self, result: PipelineResult, context: PipelineContext, output_dir: Path
    ) -> list[str]:
        generated_files = []

        try:
            # 1. execution_summary.json
            summary_path = output_dir / "execution_summary.json"
            with open(summary_path, "w") as f:
                json.dump(result.execution_summary, f, indent=2)
            generated_files.append(str(summary_path.absolute()))

            # 2. pipeline_metrics.json
            pm_path = output_dir / "pipeline_metrics.json"
            with open(pm_path, "w") as f:
                f.write(result.metrics.model_dump_json(indent=2))
            generated_files.append(str(pm_path.absolute()))

            # 3. stage_metrics.json
            sm_path = output_dir / "stage_metrics.json"
            with open(sm_path, "w") as f:
                f.write(
                    json.dumps(
                        [m.model_dump() for m in result.stage_metrics],
                        indent=2,
                        default=str,
                    )
                )
            generated_files.append(str(sm_path.absolute()))

        except Exception as e:
            logger.error(f"Failed to generate JSON outputs: {e}")

        return generated_files
