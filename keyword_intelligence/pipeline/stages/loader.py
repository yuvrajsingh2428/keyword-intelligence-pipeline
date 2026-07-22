"""Loader stage for ingesting raw data from files into the pipeline."""

from __future__ import annotations

import hashlib
from pathlib import Path

from keyword_intelligence.column_resolver.models import ResolutionMethod
from keyword_intelligence.column_resolver.resolver import ColumnResolver
from keyword_intelligence.core.constants import StageType
from keyword_intelligence.input_loader.loader import InputLoader
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class LoaderStage(BaseStage):
    """Loads keyword data from a CSV or Excel file into the PipelineContext.

    Supports reading .csv, .xlsx, and .xls files transparently.
    """

    def __init__(
        self,
        file_path: str | Path | bytes,
        file_name: str | None = None,
        sheet_name: str | None = None,
        keyword_column: str | None = None,
    ) -> None:
        """Initialize the loader with target file and optional sheet name."""
        self.file_input = file_path
        self.file_name = file_name
        self.sheet_name = sheet_name
        self.keyword_column = keyword_column

    @property
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.LOADER

    @property
    def stage_version(self) -> str:
        """Return the version of the stage."""
        return "3.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Read the file and set the DataFrame in the context."""
        loader = InputLoader()

        # Load the dataframe
        df = loader.load(
            self.file_input, file_name=self.file_name, sheet_name=self.sheet_name
        )

        # Resolve Column
        resolver = ColumnResolver()
        if self.keyword_column:
            if self.keyword_column not in df.columns:
                raise ValueError(
                    f"Explicit keyword column '{self.keyword_column}' not found in file."
                )
            mapped_col = self.keyword_column
            method = ResolutionMethod.MANUAL.value
            confidence = 100.0
        else:
            candidates = resolver.resolve(df.columns.tolist())
            best = candidates[0]
            mapped_col = best.original_column
            method = best.method.value
            confidence = best.confidence_score

        df = df.rename(columns={mapped_col: "keyword"})

        # Calculate checksum and size if possible
        checksum = ""
        file_size = 0
        actual_name = self.file_name or "unknown"
        ext = ""

        if isinstance(self.file_input, bytes):
            checksum = hashlib.sha256(self.file_input).hexdigest()
            file_size = len(self.file_input)
            ext = Path(actual_name).suffix.lower()
        else:
            path = Path(str(self.file_input))
            if path.exists():
                actual_name = path.name
                ext = path.suffix.lower()
                file_size = path.stat().st_size
                sha256 = hashlib.sha256()
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256.update(chunk)
                checksum = sha256.hexdigest()

        context.data = df

        # Populate DatasetMetadata
        context.dataset_metadata.file_name = actual_name
        context.dataset_metadata.file_size = file_size
        context.dataset_metadata.file_extension = ext
        context.dataset_metadata.checksum = checksum
        context.dataset_metadata.total_rows = len(df)
        context.dataset_metadata.total_columns = len(df.columns)
        context.dataset_metadata.original_column_names = df.columns.tolist()

        context.dataset_metadata.resolved_keyword_column = mapped_col
        context.dataset_metadata.resolution_method = method
        context.dataset_metadata.resolution_confidence = confidence

        return context
