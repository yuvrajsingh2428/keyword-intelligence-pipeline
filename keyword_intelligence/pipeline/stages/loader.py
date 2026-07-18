"""Loader stage for ingesting raw data from files into the pipeline."""

from __future__ import annotations

from pathlib import Path

from typing import ClassVar

import pandas as pd
from loguru import logger

from keyword_intelligence.core.exceptions import (
    DataSourceError,
    FileEncodingError,
    UnsupportedFileExtensionError,
)
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class LoaderStage(BaseStage):
    """Loads keyword data from a CSV or Excel file into the PipelineContext.

    Supports reading .csv, .xlsx, and .xls files. For CSVs, it automatically
    attempts to decode using UTF-8, UTF-8-SIG, and Latin-1.
    """

    SUPPORTED_ENCODINGS: ClassVar[tuple[str, ...]] = ("utf-8", "utf-8-sig", "latin-1")
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".csv", ".xlsx", ".xls"}

    def __init__(self, file_path: str | Path) -> None:
        """Initialize the loader with the target file path."""
        self.file_path = Path(file_path)

    @property
    def name(self) -> str:
        """Return the name of the stage."""
        return "Loader"

    def execute(self, context: PipelineContext) -> None:
        """Read the file and set the DataFrame in the context.

        Args:
            context: The pipeline context to populate.

        Raises:
            UnsupportedFileExtensionError: If the file is not a supported type.
            FileEncodingError: If the CSV cannot be decoded.
            DataSourceError: For other read errors (e.g., file not found).
        """
        if not self.file_path.exists():
            raise DataSourceError(f"File not found: {self.file_path}")

        ext = self.file_path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileExtensionError(
                f"Extension '{ext}' not supported. "
                f"Must be one of {self.SUPPORTED_EXTENSIONS}"
            )

        logger.info(f"Loading data from {self.file_path}")

        try:
            df = self._load_csv() if ext == ".csv" else self._load_excel()
        except Exception as e:
            if isinstance(e, (FileEncodingError, UnsupportedFileExtensionError)):
                raise
            raise DataSourceError(f"Failed to read file: {e}") from e

        context.data = df
        context.metadata["source_file"] = str(self.file_path)
        logger.info(f"Loaded {len(df)} rows from {self.file_path.name}")

    def _load_csv(self) -> pd.DataFrame:
        """Attempt to load a CSV using supported encodings."""
        last_exception: Exception | None = None

        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                # We use dtype=str to avoid pandas guessing types incorrectly
                # for things like volume (which might have commas) early on.
                df = pd.read_csv(self.file_path, encoding=encoding, dtype=str)
                logger.debug(
                    f"Successfully decoded {self.file_path.name} with {encoding}"
                )
                return df
            except UnicodeDecodeError as e:
                last_exception = e
                logger.debug(f"Failed to decode with {encoding}: {e}")

        raise FileEncodingError(
            f"Failed to decode {self.file_path.name}. Tried: {self.SUPPORTED_ENCODINGS}"
        ) from last_exception

    def _load_excel(self) -> pd.DataFrame:
        """Load an Excel file."""
        return pd.read_excel(self.file_path, dtype=str)
