"""Export Manager that aggregates all exporters."""

from pathlib import Path

from keyword_intelligence.exporters.base import BaseExporter
from keyword_intelligence.exporters.csv_exporter import CSVExporter
from keyword_intelligence.exporters.excel_exporter import ExcelExporter
from keyword_intelligence.exporters.json_exporter import JSONExporter
from keyword_intelligence.models.pipeline import PipelineResult
from keyword_intelligence.pipeline.context import PipelineContext


class ExportManager:
    """Manages generation of all pipeline artifacts."""

    def __init__(self):
        self.exporters: list[BaseExporter] = [
            CSVExporter(),
            ExcelExporter(),
            JSONExporter(),
        ]

    def export(
        self, result: PipelineResult, context: PipelineContext, output_dir: Path
    ) -> list[str]:
        """Invoke all enabled exporters.

        Returns:
            A list of all generated file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        all_files = []

        for exporter in self.exporters:
            files = exporter.export(result, context, output_dir)
            all_files.extend(files)

        return all_files
