"""Input Loader Module.

Abstracts file loading to provide a unified Pandas DataFrame to the pipeline,
supporting both CSV and Excel seamlessly.
"""

from keyword_intelligence.input_loader.exceptions import (
    CorruptedWorkbookError,
    EmptyFileError,
    FileEncodingError,
    InputLoaderError,
    MissingSheetError,
    UnsupportedFileFormatError,
)
from keyword_intelligence.input_loader.loader import InputLoader

__all__ = [
    "CorruptedWorkbookError",
    "EmptyFileError",
    "FileEncodingError",
    "InputLoader",
    "InputLoaderError",
    "MissingSheetError",
    "UnsupportedFileFormatError",
]
