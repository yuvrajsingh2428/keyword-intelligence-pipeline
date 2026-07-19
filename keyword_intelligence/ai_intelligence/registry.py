"""Registry and resolution layer for AI providers."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.ai_intelligence.providers.base import AIProvider


class AIProviderRegistry:
    """Central registry for all available AI providers."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        """Register a provider instance."""
        if provider.provider_name in self._providers:
            logger.warning(
                f"Overwriting existing AI provider: {provider.provider_name}"
            )
        self._providers[provider.provider_name] = provider
        logger.debug(
            f"Registered AIProvider: {provider.provider_name} v{provider.provider_version}"
        )

    def get_all(self) -> list[AIProvider]:
        """Return all registered providers sorted by priority."""
        return sorted(self._providers.values(), key=lambda p: p.priority)

    def get(self, name: str) -> AIProvider | None:
        """Retrieve a specific provider by name."""
        return self._providers.get(name)


class AIProviderResolver:
    """Resolves the appropriate provider to use based on configuration."""

    def __init__(self, registry: AIProviderRegistry) -> None:
        self.registry = registry

    def resolve(self, requested_provider: str) -> AIProvider:
        """Resolve the provider by name.

        Args:
            requested_provider: The configured provider name.

        Returns:
            The resolved AIProvider instance.

        Raises:
            ValueError: If the requested provider cannot be found.
        """
        provider = self.registry.get(requested_provider)

        if not provider:
            available = list(self.registry._providers.keys())
            raise ValueError(
                f"AI provider '{requested_provider}' not found. "
                f"Available providers: {available}"
            )

        return provider
