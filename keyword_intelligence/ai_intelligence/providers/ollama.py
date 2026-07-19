"""Ollama transport layer and provider."""

from __future__ import annotations

import httpx
from loguru import logger

from keyword_intelligence.ai_intelligence.models import AIProviderCapabilities
from keyword_intelligence.ai_intelligence.providers.base import AIProvider
from keyword_intelligence.config.settings import Settings


class OllamaTransport:
    """Handles HTTP communication with the Ollama REST API."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.endpoint = f"{self.base_url}/api/generate"

    def generate(self, model: str, system_prompt: str, user_prompt: str) -> str:
        """Send a generation request to Ollama and return the raw response string."""
        payload = {
            "model": model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",  # Enforce JSON mode
        }

        logger.debug(
            f"Sending request to Ollama ({self.endpoint}). Model: {model}, Timeout: {self.timeout}s"
        )
        logger.debug(f"Ollama System Prompt:\n{system_prompt}")
        logger.debug(f"Ollama User Prompt:\n{user_prompt}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.endpoint, json=payload)
                response.raise_for_status()

                data = response.json()
                raw_text = str(data.get("response", ""))
                logger.debug(f"Ollama raw response snippet:\n{raw_text[:300]}...")
                return raw_text

        except httpx.TimeoutException as e:
            logger.error(f"Ollama request timed out after {self.timeout}s: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise


class OllamaProvider(AIProvider):
    """Real AI provider integration using a local Ollama instance."""

    def __init__(self, settings: Settings) -> None:
        self.model = settings.ai_model
        self.transport = OllamaTransport(
            base_url=settings.ollama_url, timeout=settings.ai_timeout
        )

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def provider_version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 20

    @property
    def capabilities(self) -> AIProviderCapabilities:
        return AIProviderCapabilities(
            max_batch_size=100,  # Local GPU constraints usually prefer smaller batches
            supports_batching=True,
            supports_streaming=False,
            supports_json_mode=True,
            supports_function_calling=False,
        )

    def health_check(self) -> bool:
        """Check if Ollama REST API is reachable."""
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(self.transport.base_url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def classify(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama via the transport layer."""
        return self.transport.generate(
            model=self.model, system_prompt=system_prompt, user_prompt=user_prompt
        )
