"""Health check aggregation and execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from keyword_intelligence.models.base import AppBaseModel


class HealthReport(AppBaseModel):
    """Aggregate health status of the application."""

    status: str
    components: dict[str, dict[str, Any]]


class HealthIndicator(ABC):
    """Interface for components that provide health checks."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the indicator (e.g., 'Cache', 'Pipeline')."""
        pass

    @abstractmethod
    def check_health(self) -> dict[str, Any]:
        """Perform the health check.

        Returns:
            Dictionary containing at least 'status' (healthy/unhealthy).
        """
        pass


class ConfigurationHealth(HealthIndicator):
    """Health indicator for application configuration."""

    @property
    def name(self) -> str:
        """Return the indicator name."""
        return "Configuration"

    def check_health(self) -> dict[str, Any]:
        """Perform the configuration health check."""
        return {"status": "healthy"}


class HealthAggregator:
    """Aggregates health checks from all registered indicators."""

    def __init__(self) -> None:
        """Initialize health aggregator."""
        self._indicators: list[HealthIndicator] = []

    def register(self, indicator: HealthIndicator) -> None:
        """Register a new health indicator."""
        self._indicators.append(indicator)

    def check(self) -> HealthReport:
        """Execute all health checks and return the aggregate report."""
        components = {}
        overall_status = "healthy"

        for indicator in self._indicators:
            try:
                res = indicator.check_health()
                components[indicator.name] = res
                if res.get("status") != "healthy":
                    overall_status = "unhealthy"
            except Exception as e:
                components[indicator.name] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"

        return HealthReport(status=overall_status, components=components)
