"""OpenRouter API provider implementation."""

from __future__ import annotations

import requests
from loguru import logger

from keyword_intelligence.ai_intelligence.models import AIProviderCapabilities
from keyword_intelligence.ai_intelligence.providers.base import AIProvider
from keyword_intelligence.config.settings import Settings


class OpenRouterProvider(AIProvider):
    """AI provider integration using OpenRouter API."""

    def __init__(self, settings: Settings) -> None:
        self.model = settings.open_router_model
        api_key = settings.open_router_api_key
        self.base_url = settings.open_router_base_url

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY (or open_router_api_key) is not configured in environment or .env file."
            )

        self.api_key = api_key
        self.timeout = settings.ai_timeout

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def provider_version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 20  # Fallback priority

    @property
    def capabilities(self) -> AIProviderCapabilities:
        return AIProviderCapabilities(
            max_batch_size=200,
            supports_batching=True,
            supports_streaming=False,
            supports_json_mode=True,
            supports_function_calling=False,
        )

    def health_check(self) -> bool:
        """Verify OpenRouter API is reachable."""
        try:
            # We can ping the models endpoint to verify key.
            url = self.base_url.replace("/chat/completions", "")
            if not url.endswith("/models"):
                url = url + "models" if url.endswith("/") else url + "/models"

            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(url, headers=headers, timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenRouter health check failed: {e}")
            return False

    def classify(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenRouter API."""
        logger.debug(
            f"Sending request to OpenRouter... Model: {self.model}, Timeout: {self.timeout}s"
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8501",  # Optional, for openrouter stats
            "X-Title": "Keyword Intelligence Pipeline",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            # Some models on OpenRouter require explicit max_tokens to prevent 402 if credit is low,
            # but usually it's best to leave it to the provider if credit is sufficient.
            # We add 2000 as a safe upper bound for JSON lists.
            "max_tokens": 4000,
            "response_format": {"type": "json_object"},
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,  # type: ignore
            )
            response.raise_for_status()

            data = response.json()
            raw_text = data["choices"][0]["message"]["content"] or ""
            logger.debug(f"OpenRouter raw response snippet:\n{raw_text[:300]}...")
            return raw_text

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API error: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise RuntimeError(f"OpenRouter API failure: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error communicating with OpenRouter: {e}")
            raise
