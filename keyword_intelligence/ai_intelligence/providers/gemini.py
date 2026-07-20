"""Google Gemini provider implementation."""

from __future__ import annotations

from google import genai
from google.genai import types
from google.genai.errors import APIError
from loguru import logger

from keyword_intelligence.ai_intelligence.models import AIProviderCapabilities
from keyword_intelligence.ai_intelligence.providers.base import AIProvider
from keyword_intelligence.config.settings import Settings


class GeminiProvider(AIProvider):
    """Real AI provider integration using Google Gemini API."""

    def __init__(self, settings: Settings) -> None:
        self.model = settings.ai_model

        keys = [
            settings.google_gemini_api_key_1,
            settings.google_gemini_api_key_2,
            settings.google_gemini_api_key_3,
            settings.google_gemini_api_key_4,
            settings.google_gemini_api_key_5,
        ]

        self.api_keys = [k for k in keys if k]

        if not self.api_keys:
            raise ValueError(
                "No Google_Gemini_api_key configurations found in environment or .env file."
            )

        self.timeout = settings.ai_timeout
        self.current_key_idx = 0

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def provider_version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 15

    @property
    def capabilities(self) -> AIProviderCapabilities:
        return AIProviderCapabilities(
            max_batch_size=200,
            supports_batching=True,
            supports_streaming=False,
            supports_json_mode=True,
            supports_function_calling=True,
        )

    def health_check(self) -> bool:
        """Verify Gemini API is reachable using the first key."""
        try:
            client = genai.Client(api_key=self.api_keys[0])
            models = list(client.models.list())
            return len(models) > 0
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

    def classify(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API via the official SDK with key rotation."""
        for attempt_idx in range(self.current_key_idx, len(self.api_keys)):
            api_key = self.api_keys[attempt_idx]
            self.current_key_idx = attempt_idx

            client = genai.Client(api_key=api_key)
            logger.info(f"Using Gemini API Key #{attempt_idx + 1}")

            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )

                raw_text = response.text or ""
                logger.debug(f"Gemini raw response snippet:\n{raw_text[:300]}...")

                if attempt_idx > 0:
                    logger.info(f"Gemini API Key #{attempt_idx + 1} succeeded")

                return raw_text

            except APIError as e:
                err_str = str(e).lower()
                retry_keywords = [
                    "429",
                    "quota",
                    "rate limit",
                    "503",
                    "500",
                    "timeout",
                    "unavailable",
                    "exhausted",
                    "overloaded",
                ]

                if any(k in err_str for k in retry_keywords):
                    logger.warning(
                        f"Gemini API Key #{attempt_idx + 1} quota exceeded or unavailable"
                    )
                    if attempt_idx + 1 < len(self.api_keys):
                        logger.info(f"Switching to Gemini API Key #{attempt_idx + 2}")
                        continue
                    else:
                        logger.warning("All Gemini API keys exhausted")
                        raise RuntimeError(
                            f"All Gemini API keys exhausted. Last error: {e}"
                        ) from e
                else:
                    logger.error(f"Gemini API error: {e.message}")
                    raise RuntimeError(f"Gemini API failure: {e.message}") from e

            except Exception as e:
                err_str = str(e).lower()
                retry_keywords = [
                    "429",
                    "quota",
                    "rate limit",
                    "503",
                    "500",
                    "timeout",
                    "unavailable",
                    "exhausted",
                    "connection",
                ]

                if any(k in err_str for k in retry_keywords):
                    logger.warning(f"Gemini API Key #{attempt_idx + 1} unavailable")
                    if attempt_idx + 1 < len(self.api_keys):
                        logger.info(f"Switching to Gemini API Key #{attempt_idx + 2}")
                        continue
                    else:
                        logger.warning("All Gemini API keys exhausted")
                        raise RuntimeError(
                            f"All Gemini API keys exhausted. Last error: {e}"
                        ) from e
                else:
                    logger.error(f"Unexpected error communicating with Gemini: {e}")
                    raise

        raise RuntimeError("All Gemini API keys exhausted.")
