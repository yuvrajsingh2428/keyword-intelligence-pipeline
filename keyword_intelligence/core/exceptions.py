"""Application exception hierarchy for the Keyword Intelligence Pipeline.

Defines a structured exception tree rooted at KeywordIntelligenceError.
All application-specific exceptions should inherit from this base class
to enable precise error handling and avoid catching unrelated errors
from third-party libraries.

Exception Hierarchy:
    KeywordIntelligenceError (base)
    ├── ConfigurationError      — invalid settings, missing env vars
    └── InitializationError     — app startup failures

Future phases will extend this hierarchy:
    KeywordIntelligenceError
    ├── ConfigurationError
    ├── InitializationError
    ├── PipelineError           — pipeline execution failures
    │   ├── StageError          — individual stage failures
    │   └── ContextError        — pipeline context issues
    ├── DataSourceError         — external data source failures
    └── ProviderError           — LLM/AI provider failures
"""

from __future__ import annotations


class KeywordIntelligenceError(Exception):
    """Base exception for all application-specific errors.

    All custom exceptions in the Keyword Intelligence Pipeline inherit
    from this class. Catching this exception will catch any application
    error without catching unrelated exceptions from third-party code.

    Args:
        message: Human-readable error description.
        detail: Optional additional context or diagnostic information.
    """

    def __init__(self, message: str, detail: str | None = None) -> None:
        """Initialize the base exception.

        Args:
            message: Human-readable error description.
            detail: Optional additional context or diagnostic information.
        """
        self.message = message
        self.detail = detail
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        if self.detail:
            return f"{self.message} — {self.detail}"
        return self.message


class ConfigurationError(KeywordIntelligenceError):
    """Raised when application configuration is invalid or missing.

    Examples:
        - Required environment variable not set
        - Invalid value for a configuration field
        - .env file parsing failure
        - Incompatible configuration combinations
    """


class InitializationError(KeywordIntelligenceError):
    """Raised when the application fails to initialize properly.

    Examples:
        - Logging system setup failure
        - Required directory creation failure
        - Database connection failure at startup
        - Service dependency unavailable
    """


class PipelineError(KeywordIntelligenceError):
    """Raised when the pipeline encounters an execution failure."""


class DataSourceError(PipelineError):
    """Raised when a data source cannot be read or accessed."""


class UnsupportedFileExtensionError(DataSourceError):
    """Raised when a file extension is not supported by the loader."""


class FileEncodingError(DataSourceError):
    """Raised when a file cannot be decoded with supported encodings."""


class SchemaValidationError(PipelineError):
    """Raised when a dataframe does not match the required schema."""
