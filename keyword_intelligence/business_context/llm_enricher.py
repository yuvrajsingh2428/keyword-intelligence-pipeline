"""LLM-powered Business Profile generator."""

from __future__ import annotations

import json

from loguru import logger

from keyword_intelligence.ai_intelligence.registry import AIProviderResolver
from keyword_intelligence.business_context.models import (
    BusinessProfile,
    CollectedContent,
)
from keyword_intelligence.config.settings import Settings


class LLMEnricher:
    """Uses an LLM to enrich the draft business profile metadata."""

    def __init__(self, settings: Settings, resolver: AIProviderResolver) -> None:
        self.settings = settings
        self.resolver = resolver

    def generate(
        self, draft: BusinessProfile, contents: list[CollectedContent]
    ) -> BusinessProfile:
        """Enrich the draft profile using LLM inference."""
        logger.info("Enriching Business Profile via LLM.")

        provider = self.resolver.resolve(self.settings.ai_provider)

        # Summarize content to fit in context window
        corpus = []
        for c in contents:
            corpus.append(
                f"--- URL: {c.source_url} | Title: {c.title} ---\n{c.clean_text[:1000]}"
            )
        text_corpus = "\n".join(corpus)

        system_prompt = (
            "You are an expert Business Analyst. Provide missing field enrichment for the business profile from the provided website text.\n"
            "Return ONLY a JSON object strictly matching this schema. Do not output markdown code blocks. \n"
            "SCHEMA:\n"
            "{\n"
            '  "industry": "string",\n'
            '  "business_description": "string",\n'
            '  "technologies": ["string"],\n'
            '  "customer_segments": ["string"],\n'
            '  "important_keywords": ["string"],\n'
            '  "business_concepts": ["string"]\n'
            "}\n"
        )

        user_prompt = (
            f"Company: {draft.company_name}\n\nWebsite Content:\n{text_corpus}"
        )

        try:
            logger.debug(
                f"Sending profile generation prompt to {provider.provider_name}..."
            )
            raw_response = provider.classify(
                system_prompt=system_prompt, user_prompt=user_prompt
            )

            raw = raw_response

            if raw.startswith("```"):
                raw = raw.strip("`").removeprefix("json").strip()

            data = json.loads(raw)

            draft.industry = data.get("industry", draft.industry)
            draft.business_description = data.get("business_description", "")

            draft.technologies.extend(data.get("technologies", []))
            draft.customer_segments.extend(data.get("customer_segments", []))
            draft.important_keywords.extend(data.get("important_keywords", []))
            draft.business_concepts.extend(data.get("business_concepts", []))

            draft.metadata.llm_model = provider.provider_name

            logger.info("Successfully enriched Business Profile.")

        except Exception as e:
            logger.error(f"Failed to generate business profile via LLM: {e}")

        return draft
