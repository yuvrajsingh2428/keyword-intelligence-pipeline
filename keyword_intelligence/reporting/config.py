"""Configuration mapping for the Reporting Engine."""

from __future__ import annotations

from keyword_intelligence.config.settings import Settings


class ReportEngineConfig:
    """Extracts and validates reporting configuration."""

    def __init__(
        self,
        report_format: str,
        output_dir: str,
    ) -> None:
        """Initialise the reporting configuration.

        Args:
            report_format: Default export format (csv, excel, json).
            output_dir: Directory path for exported files.
        """
        self.report_format = report_format
        self.output_dir = output_dir

    @classmethod
    def from_settings(cls, settings: Settings) -> ReportEngineConfig:
        """Create configuration from global settings."""
        return cls(
            report_format=settings.report_format,
            output_dir=settings.report_output_dir,
        )
