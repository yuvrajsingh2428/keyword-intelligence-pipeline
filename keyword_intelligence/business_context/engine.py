"""Business Context Engine."""

from __future__ import annotations

import time

from loguru import logger

from keyword_intelligence.ai_intelligence.registry import AIProviderResolver
from keyword_intelligence.business_context.cache import BusinessProfileCache
from keyword_intelligence.business_context.collectors.website import WebsiteCollector
from keyword_intelligence.business_context.enricher import BusinessFactsEnricher
from keyword_intelligence.business_context.extractor import StructuredExtractor
from keyword_intelligence.business_context.llm_enricher import LLMEnricher
from keyword_intelligence.business_context.models import BusinessProfile
from keyword_intelligence.business_context.validator import BusinessFactsValidator
from keyword_intelligence.config.settings import Settings


class BusinessContextEngine:
    """Facade for building the Business Profile."""

    def __init__(self, settings: Settings, ai_resolver: AIProviderResolver) -> None:
        self.settings = settings
        self.cache = BusinessProfileCache(
            ttl_hours=settings.business_context_cache_ttl_hours
        )

        # We could use a registry for collectors, but we only have website for now.
        self.collector = WebsiteCollector(settings)
        self.extractor = StructuredExtractor()
        self.enricher = BusinessFactsEnricher(settings)
        self.validator = BusinessFactsValidator()
        self.llm_enricher = LLMEnricher(settings, ai_resolver)

    def process(
        self,
        company_name: str,
        website: str,
        industry: str = "",
        force_refresh: bool = False,
    ) -> BusinessProfile:
        """Build or retrieve a BusinessProfile for the given company."""
        # Logging removed
        start = time.perf_counter()

        if force_refresh:
            self.cache.invalidate(company_name, website)

        profile = self.cache.get(company_name, website)
        if profile:
            # Logging removed
            return profile

        # 1. Collect
        try:
            contents = self.collector.collect(company_name, website)
        except Exception as e:
            # Logging removed
            contents = []

        # 2. Extract Draft
        draft = self.extractor.extract(company_name, website, industry, contents)
        draft.metadata.source_pages = [c.source_url for c in contents]

        # 2.5 Enrich and Validate
        if contents:
            self.enricher.enrich(draft, contents)
            self.validator.validate(draft)

        # Log draft stats
        # Logging removed

        if not contents:
            draft.metadata.quality_score = 0.0
            # Continue to LLM enricher for parametric fallback

        # 3. Enrich profile with missing metadata via LLM
        profile = self.llm_enricher.generate(draft, contents)

        # Logging removed

        # 4. Calculate Quality Score
        score = 0.0
        score += min(len(contents) / 5.0, 1.0) * 20.0  # Up to 20 points for pages
        score += (
            min(len(profile.business_facts.products) / 5.0, 1.0) * 30.0
        )  # Up to 30 points for products
        score += (
            min(len(profile.business_facts.categories) / 5.0, 1.0) * 20.0
        )  # Up to 20 points for categories
        score += (
            min(len(profile.business_facts.brands) / 2.0, 1.0) * 20.0
        )  # Up to 20 points for brands

        # LLM confidence is usually 0.8 per entity since we hardcoded it in generator for now
        # We just add a flat 10 points if the LLM ran successfully
        if profile.metadata.llm_model:
            score += 10.0

        profile.metadata.quality_score = round(score, 1)

        # 5. Cache
        self.cache.put(profile)
        # Logging removed

        duration_ms = (time.perf_counter() - start) * 1000
        # Logging removed

        return profile
