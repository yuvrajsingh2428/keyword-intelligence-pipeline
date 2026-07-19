"""Base provider interface for the AI engine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from keyword_intelligence.ai_intelligence.models import AIProviderCapabilities


class AIProvider(ABC):
    """Abstract interface for an AI classification provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def provider_version(self) -> str:
        """Version of this provider implementation."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Priority of this provider during resolution (lower is higher priority)."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> AIProviderCapabilities:
        """Capabilities supported by this provider."""
        pass

    @abstractmethod
    def classify(self, system_prompt: str, user_prompt: str) -> str:
        """Send prompts to the AI provider and return the raw string response.

        Args:
            system_prompt: Instructions for the LLM.
            user_prompt: The rendered prompt containing keywords.

        Returns:
            The raw text response from the provider (expected to be JSON).

        Raises:
            Exception: On network, timeout, or provider-specific errors.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify the provider is configured correctly and reachable.

        Returns:
            True if healthy, False otherwise.
        """
        pass
