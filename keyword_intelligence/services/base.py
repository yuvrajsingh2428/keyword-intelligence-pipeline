"""Abstract base service for the Keyword Intelligence Pipeline.

Defines the lifecycle interface that all application services must
implement. Services are long-lived components that manage external
resources (API clients, database connections, etc.) and are
initialized at startup and shut down gracefully.

Usage:
    from keyword_intelligence.services.base import BaseService

    class LLMService(BaseService):
        async def initialize(self) -> None:
            self._client = SomeAPIClient(self.settings.api_key)

        async def shutdown(self) -> None:
            await self._client.close()

        async def health_check(self) -> bool:
            return await self._client.ping()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyword_intelligence.config.settings import Settings


class BaseService(ABC):
    """Abstract base class for application services.

    Provides a standard lifecycle (initialize → use → shutdown) and
    dependency injection via the constructor. All services receive
    a Settings instance, ensuring they never read environment
    variables directly.

    Subclasses must implement:
        - initialize(): Acquire resources, establish connections.
        - shutdown(): Release resources, close connections.
        - health_check(): Verify the service is operational.

    Args:
        settings: The validated application settings instance.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the base service with application settings.

        Args:
            settings: The validated application settings instance.
        """
        self._settings = settings
        self._initialized: bool = False

    @property
    def settings(self) -> Settings:
        """Return the application settings."""
        return self._settings

    @property
    def is_initialized(self) -> bool:
        """Check whether the service has been initialized."""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service and acquire resources.

        Called once during application startup. Implementations should
        establish connections, validate credentials, and prepare the
        service for use.

        Raises:
            InitializationError: If the service cannot be initialized.
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """Shut down the service and release resources.

        Called during application teardown. Implementations should
        close connections, flush buffers, and clean up resources
        gracefully.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Check whether the service is healthy and operational.

        Returns:
            True if the service is operational, False otherwise.
        """
