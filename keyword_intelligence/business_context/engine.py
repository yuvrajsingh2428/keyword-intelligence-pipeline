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
        logger.info(f"BusinessContextEngine starting for {company_name} ({website})")
        start = time.perf_counter()

        if force_refresh:
            self.cache.invalidate(company_name, website)

        profile = self.cache.get(company_name, website)
        if profile:
            logger.info("Found valid BusinessProfile in cache.")
            return profile

        # 1. Collect
        try:
            contents = self.collector.collect(company_name, website)
        except Exception as e:
            logger.error(f"Collector failed completely: {e}")
            contents = []

        # 2. Extract Draft
        draft = self.extractor.extract(company_name, website, industry, contents)
        draft.metadata.source_pages = [c.source_url for c in contents]

        # 2.5 Enrich and Validate
        if contents:
            self.enricher.enrich(draft, contents)
            self.validator.validate(draft)

        # Log draft stats
        logger.info(
            f"BusinessProfile Draft: Products Found: {len(draft.business_facts.products)}, Brands Found: {len(draft.business_facts.brands)}, Categories Found: {len(draft.business_facts.categories)}, Source URLs: {len(draft.metadata.source_pages)}"
        )

        if not contents:
            logger.warning(
                "No website content collected. Returning minimal fallback profile without LLM enrichment."
            )
            draft.metadata.quality_score = 0.0
            return draft

        if self.settings.debug:
            logger.debug(
                f"[DEBUG] Business Facts Extracted - "
                f"Number of Brands: {len(draft.business_facts.brands)}, "
                f"Number of Products: {len(draft.business_facts.products)}, "
                f"Number of Categories: {len(draft.business_facts.categories)}, "
                f"Number of Services: {len(draft.business_facts.services)}"
            )

        # 3. Enrich profile with missing metadata via LLM
        profile = self.llm_enricher.generate(draft, contents)

        logger.info(
            f"BusinessProfile Enriched: Industry: {profile.industry}, Product Families: {len(profile.business_facts.product_families)}, Technologies: {len(profile.technologies)}, Customer Segments: {len(profile.customer_segments)}"
        )

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
        logger.info(
            f"BusinessProfile Cached: Cache Key: {profile.company_name}:{profile.website}"
        )

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(f"BusinessContextEngine completed in {duration_ms:.0f}ms.")

        return profile
