"""Core input loader implementation."""

from __future__ import annotations

import io
from pathlib import Path
from typing import ClassVar

import pandas as pd
from loguru import logger

from keyword_intelligence.input_loader.exceptions import (
    CorruptedWorkbookError,
    EmptyFileError,
    FileEncodingError,
    MissingSheetError,
    UnsupportedFileFormatError,
)


class InputLoader:
    """Universal tabular data loader for CSV and Excel files."""

    SUPPORTED_ENCODINGS: ClassVar[tuple[str, ...]] = ("utf-8", "utf-8-sig", "latin-1")
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".csv", ".xlsx", ".xls"}

    def load(
        self,
        file_input: str | Path | bytes,
        file_name: str | None = None,
        sheet_name: str | None = None,
    ) -> pd.DataFrame:
        """Load tabular data into a pandas DataFrame.

        Args:
            file_input: A file path (str/Path) or raw bytes.
            file_name: The name of the file (required if file_input is bytes).
            sheet_name: The name of the sheet to load (applicable only to Excel).

        Returns:
            A pandas DataFrame.

        Raises:
            UnsupportedFileFormatError: If the extension is unsupported.
            MissingSheetError: If the requested sheet is missing.
            EmptyFileError: If the resulting DataFrame has 0 rows or columns.
            CorruptedWorkbookError: If an Excel file is corrupted.
            FileEncodingError: If a CSV file cannot be decoded.
        """
        # Determine file extension and payload
        is_bytes = isinstance(file_input, bytes)
        actual_file_name = file_name if is_bytes else Path(str(file_input)).name
        ext = Path(actual_file_name).suffix.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileFormatError(
                f"Extension '{ext}' not supported. Must be one of {self.SUPPORTED_EXTENSIONS}"
            )

        # Dispatch
        try:
            if ext == ".csv":
                df = self._load_csv(file_input)
            else:
                df = self._load_excel(file_input, sheet_name=sheet_name)
        except Exception as e:
            if isinstance(
                e,
                (
                    UnsupportedFileFormatError,
                    EmptyFileError,
                    MissingSheetError,
                    CorruptedWorkbookError,
                    FileEncodingError,
                ),
            ):
                raise e
            raise Exception(f"Failed to load data: {e}") from e

        # Validate basic structure
        if df.empty or len(df.columns) == 0:
            raise EmptyFileError(
                f"The loaded file/sheet from {actual_file_name} is empty."
            )

        return df

    def get_sheet_names(self, file_input: str | Path | bytes) -> list[str]:
        """Extract sheet names from an Excel file without loading data."""
        try:
            if isinstance(file_input, bytes):
                excel_file = pd.ExcelFile(io.BytesIO(file_input))
            else:
                excel_file = pd.ExcelFile(file_input)
            return excel_file.sheet_names
        except Exception as e:
            raise CorruptedWorkbookError(
                f"Failed to read workbook to extract sheet names: {e}"
            ) from e

    def get_columns(
        self,
        file_input: str | Path | bytes,
        file_name: str | None = None,
        sheet_name: str | None = None,
    ) -> list[str]:
        """Extract column names from the file/sheet quickly."""
        is_bytes = isinstance(file_input, bytes)
        actual_file_name = file_name if is_bytes else Path(str(file_input)).name
        ext = Path(actual_file_name).suffix.lower()

        if ext == ".csv":
            for encoding in self.SUPPORTED_ENCODINGS:
                try:
                    if is_bytes:
                        df = pd.read_csv(
                            io.BytesIO(file_input), encoding=encoding, nrows=0
                        )
                    else:
                        df = pd.read_csv(file_input, encoding=encoding, nrows=0)
                    return df.columns.tolist()
                except UnicodeDecodeError:
                    continue
            raise FileEncodingError("Failed to decode CSV for columns.")
        else:
            # Excel reads the whole sheet anyway, but nrows=0 is a bit faster in pandas >= 1.2
            if is_bytes:
                df = pd.read_excel(
                    io.BytesIO(file_input), sheet_name=sheet_name or 0, nrows=0
                )
            else:
                df = pd.read_excel(file_input, sheet_name=sheet_name or 0, nrows=0)
            return df.columns.tolist()

    def _load_csv(self, file_input: str | Path | bytes) -> pd.DataFrame:
        last_exception = None
        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                if isinstance(file_input, bytes):
                    # We must reset stream position if we iterate
                    df = pd.read_csv(
                        io.BytesIO(file_input), encoding=encoding, dtype=str
                    )
                else:
                    df = pd.read_csv(file_input, encoding=encoding, dtype=str)

                logger.debug(f"Successfully loaded CSV with encoding {encoding}")
                return df
            except UnicodeDecodeError as e:
                last_exception = e
            except pd.errors.EmptyDataError:
                raise EmptyFileError("The CSV file contains no data.")

        raise FileEncodingError(
            f"Failed to decode CSV. Tried: {self.SUPPORTED_ENCODINGS}"
        ) from last_exception

    def _load_excel(
        self, file_input: str | Path | bytes, sheet_name: str | None
    ) -> pd.DataFrame:
        try:
            if isinstance(file_input, bytes):
                excel_file = pd.ExcelFile(io.BytesIO(file_input))
            else:
                excel_file = pd.ExcelFile(file_input)
        except Exception as e:
            raise CorruptedWorkbookError(f"Failed to open Excel workbook: {e}") from e

        sheets = excel_file.sheet_names
        if not sheets:
            raise CorruptedWorkbookError("Excel workbook contains no sheets.")

        target_sheet = sheet_name
        if target_sheet:
            if target_sheet not in sheets:
                raise MissingSheetError(
                    f"Sheet '{target_sheet}' not found in workbook. Available: {sheets}"
                )
        else:
            # Load first sheet by default
            target_sheet = sheets[0]

        logger.debug(f"Loading Excel sheet: {target_sheet}")
        df = pd.read_excel(excel_file, sheet_name=target_sheet, dtype=str)
        return df
