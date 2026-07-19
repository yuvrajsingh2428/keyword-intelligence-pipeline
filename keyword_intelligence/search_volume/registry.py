"""Registry and resolution layer for Search Volume providers."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.search_volume.providers.base import SearchVolumeProvider


class ProviderRegistry:
    """Central registry for all available search volume providers."""

    def __init__(self) -> None:
        self._providers: dict[str, SearchVolumeProvider] = {}

    def register(self, provider: SearchVolumeProvider) -> None:
        """Register a provider instance."""
        if provider.provider_name in self._providers:
            logger.warning(f"Overwriting existing provider: {provider.provider_name}")
        self._providers[provider.provider_name] = provider
        logger.debug(
            f"Registered SearchVolumeProvider: {provider.provider_name} v{provider.provider_version}"
        )

    def get_all(self) -> list[SearchVolumeProvider]:
        """Return all registered providers sorted by priority."""
        return sorted(self._providers.values(), key=lambda p: p.priority)

    def get(self, name: str) -> SearchVolumeProvider | None:
        """Retrieve a specific provider by name."""
        return self._providers.get(name)


class ProviderResolver:
    """Resolves the appropriate provider to use based on configuration and capabilities."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    def resolve(self, requested_provider: str) -> SearchVolumeProvider:
        """Resolve the provider by name.

        Args:
            requested_provider: The configured provider name (e.g. 'mock').

        Returns:
            The resolved SearchVolumeProvider instance.

        Raises:
            ValueError: If the requested provider cannot be found.
        """
        provider = self.registry.get(requested_provider)

        if not provider:
            # Fallback logic could go here in the future
            available = list(self.registry._providers.keys())
            raise ValueError(
                f"Search volume provider '{requested_provider}' not found. "
                f"Available providers: {available}"
            )

        return provider
