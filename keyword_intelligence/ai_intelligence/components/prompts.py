"""Prompt management for the AI engine."""

from __future__ import annotations

import json

from loguru import logger

from keyword_intelligence.models.base import AppBaseModel


class PromptTemplate(AppBaseModel):
    """Represents a versioned prompt template."""

    prompt_name: str
    prompt_version: str
    provider: str
    schema_version: str
    system_prompt: str
    user_prompt_template: str


class PromptRegistry:
    """Registry to store and resolve prompt templates."""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        """Register a prompt template."""
        key = f"{template.provider}:{template.prompt_name}:{template.prompt_version}"
        self._templates[key] = template
        logger.debug(f"Registered prompt template: {key}")

    def get(
        self, provider: str, prompt_name: str, version: str
    ) -> PromptTemplate | None:
        """Retrieve a specific template by provider, name, and version."""
        key = f"{provider}:{prompt_name}:{version}"
        return self._templates.get(key)


class PromptBuilder:
    """Resolves prompt templates from the registry."""

    def __init__(self, registry: PromptRegistry) -> None:
        self.registry = registry

    def build(self, provider: str, prompt_name: str, version: str) -> PromptTemplate:
        """Build/resolve the prompt template from the registry."""
        template = self.registry.get(provider, prompt_name, version)
        if not template:
            raise ValueError(
                f"Prompt template '{prompt_name}' (v{version}) not found for provider '{provider}'."
            )
        return template


class PromptRenderer:
    """Renders the resolved prompt template with runtime data."""

    def render(self, template: PromptTemplate, keywords: list[str]) -> str:
        """Render the user prompt template with the provided keywords.

        Args:
            template: The PromptTemplate to render.
            keywords: List of keywords to classify.

        Returns:
            The fully rendered string ready for the LLM.
        """
        # A simple replacement for Phase 4. We inject the JSON-encoded list of keywords.
        keywords_json = json.dumps(keywords, ensure_ascii=False)
        rendered = template.user_prompt_template.replace("{{keywords}}", keywords_json)
        return rendered
