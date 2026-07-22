"""Exceptions for the Input Loader module."""


class InputLoaderError(Exception):
    """Base exception for input loader errors."""

    pass


class UnsupportedFileFormatError(InputLoaderError):
    """Raised when the file format is not supported."""

    pass


class MissingSheetError(InputLoaderError):
    """Raised when the requested Excel sheet is not found."""

    pass


class CorruptedWorkbookError(InputLoaderError):
    """Raised when an Excel workbook cannot be parsed."""

    pass


class EmptyFileError(InputLoaderError):
    """Raised when the loaded file or sheet contains no data."""

    pass


class FileEncodingError(InputLoaderError):
    """Raised when a CSV file cannot be decoded using supported encodings."""

    pass
