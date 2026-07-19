"""Batch execution abstractions for AI Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger

from keyword_intelligence.ai_intelligence.components.prompts import (
    PromptRenderer,
    PromptTemplate,
)
from keyword_intelligence.ai_intelligence.providers.base import AIProvider


class AIBatchExecutor(ABC):
    """Abstract interface for executing batch requests against an AI provider."""

    @abstractmethod
    def execute(
        self,
        provider: AIProvider,
        template: PromptTemplate,
        renderer: PromptRenderer,
        keyword_batches: list[list[str]],
    ) -> tuple[list[str], list[Exception]]:
        """Execute the batches using the given provider.

        Args:
            provider: The resolved provider to call.
            template: The PromptTemplate to render.
            renderer: The PromptRenderer.
            keyword_batches: Pre-chunked lists of keywords.

        Returns:
            A tuple containing:
            1. List of raw response strings from the LLM (one per batch).
            2. List of exceptions encountered (if any).
        """
        pass


class SequentialAIBatchExecutor(AIBatchExecutor):
    """Executes AI batches one by one synchronously."""

    def __init__(self, max_retries: int = 2, retry_delay: float = 2.0) -> None:
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute(
        self,
        provider: AIProvider,
        template: PromptTemplate,
        renderer: PromptRenderer,
        keyword_batches: list[list[str]],
    ) -> tuple[list[str], list[Exception]]:
        """Run batches sequentially with retry logic."""
        import time

        raw_responses: list[str] = []
        exceptions: list[Exception] = []

        total_batches = len(keyword_batches)

        for i, batch in enumerate(keyword_batches, 1):
            success = False
            last_err = None

            for attempt in range(1, self.max_retries + 2):
                logger.debug(
                    f"Executing AI batch {i}/{total_batches} ({len(batch)} keywords) via {provider.provider_name} (Attempt {attempt})"
                )
                try:
                    user_prompt = renderer.render(template, batch)
                    response_str = provider.classify(
                        template.system_prompt, user_prompt
                    )
                    raw_responses.append(response_str)
                    success = True
                    break
                except Exception as e:
                    last_err = e
                    if attempt <= self.max_retries:
                        logger.warning(
                            f"AI Batch {i} failed (Attempt {attempt}): {e}. Retrying in {self.retry_delay}s..."
                        )
                        time.sleep(self.retry_delay)
                    else:
                        logger.error(
                            f"AI Batch {i} failed permanently after {attempt} attempts: {e}"
                        )

            if not success and last_err:
                exceptions.append(last_err)

        return raw_responses, exceptions
