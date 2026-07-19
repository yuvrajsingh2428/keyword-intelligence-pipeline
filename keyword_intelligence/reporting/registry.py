"""Exporter registry and resolver."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.reporting.exporters.base import ReportExporter


class ExporterRegistry:
    """Central registry for all report exporters."""

    def __init__(self) -> None:
        """Initialise with an empty exporter dictionary."""
        self._exporters: dict[str, ReportExporter] = {}

    def register(self, exporter: ReportExporter) -> None:
        """Register an exporter instance."""
        if exporter.exporter_name in self._exporters:
            logger.warning(f"Overwriting exporter: {exporter.exporter_name}")
        self._exporters[exporter.exporter_name] = exporter
        logger.debug(
            f"Registered exporter: {exporter.exporter_name} "
            f"v{exporter.exporter_version}"
        )

    def get(self, name: str) -> ReportExporter | None:
        """Retrieve a specific exporter by name."""
        return self._exporters.get(name)

    def get_all(self) -> list[ReportExporter]:
        """Return all registered exporters."""
        return list(self._exporters.values())


class ExporterResolver:
    """Resolves the exporter to use based on configuration."""

    def __init__(self, registry: ExporterRegistry) -> None:
        """Initialise with the exporter registry.

        Args:
            registry: The populated exporter registry.
        """
        self.registry = registry

    def resolve(self, format_name: str) -> ReportExporter:
        """Resolve an exporter by format name.

        Args:
            format_name: The configured format (csv, excel, json).

        Returns:
            The matching ReportExporter.

        Raises:
            ValueError: If no exporter matches.
        """
        exporter = self.registry.get(format_name)
        if not exporter:
            available = [e.exporter_name for e in self.registry.get_all()]
            raise ValueError(
                f"Exporter '{format_name}' not found. Available: {available}"
            )
        return exporter
