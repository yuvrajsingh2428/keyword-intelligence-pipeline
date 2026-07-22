"""Business Context stage for the pipeline."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.business_context.engine import BusinessContextEngine
from keyword_intelligence.business_context.rule_engine import BusinessRuleEngine
from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class BusinessContextStage(BaseStage):
    """Pipeline stage that enriches keywords with deterministic business context."""

    def __init__(
        self,
        engine: BusinessContextEngine,
        company_name: str,
        website: str,
        industry: str = "",
    ) -> None:
        self.engine = engine
        self.company_name = company_name
        self.website = website
        self.industry = industry

    @property
    def stage_type(self) -> StageType:
        return StageType.BUSINESS_CONTEXT

    @property
    def stage_version(self) -> str:
        return "3.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.has_data or "keyword" not in context.data.columns:
            return context

        profile = self.engine.process(
            company_name=self.company_name, website=self.website, industry=self.industry
        )

        rule_engine = BusinessRuleEngine(profile)

        products = []
        technologies = []
        synonyms = []
        brands = []
        categories = []
        families = []
        domains = []
        relevances = []
        reasons = []
        confidences = []
        requires_ais = []

        matched_brand = 0
        matched_product = 0
        matched_family = 0
        matched_category = 0
        matched_technology = 0
        matched_synonym = 0
        sent_to_ai = 0
        retail_filtered = 0

        for kw in context.data["keyword"]:
            res = rule_engine.process(str(kw))

            products.append(res.product)
            technologies.append(res.technology)
            synonyms.append(res.synonym_matched)
            brands.append(res.brand)
            categories.append(res.category)
            families.append(res.product_family)
            domains.append(res.domain)
            relevances.append(res.retail_relevance)
            reasons.append(res.deterministic_reason)
            confidences.append(res.business_confidence)
            requires_ais.append(res.requires_ai)

            if res.requires_ai:
                sent_to_ai += 1
            else:
                if res.retail_relevance is False:
                    retail_filtered += 1

            if res.product:
                matched_product += 1
            if res.product_family:
                matched_family += 1
            if res.brand:
                matched_brand += 1
            if res.category:
                matched_category += 1
            if res.technology:
                matched_technology += 1
            if res.synonym_matched:
                matched_synonym += 1

        context.data["business_product"] = products
        context.data["business_technology"] = technologies
        context.data["business_synonym"] = synonyms
        context.data["business_brand"] = brands
        context.data["business_category"] = categories
        context.data["business_product_family"] = families
        context.data["business_domain"] = domains
        context.data["business_relevance"] = relevances
        context.data["business_reason"] = reasons
        context.data["business_confidence"] = confidences
        context.data["requires_ai"] = requires_ais

        # Format Trace Blocks
        facts = profile.business_facts
        total_kws = len(context.data)
        
        business_profile_trace = (
            f"Business Profile\n"
            f"Brands: {len(facts.brands)}\n"
            f"Categories: {len(facts.categories)}\n"
            f"Products: {len(facts.products)}\n"
            f"Product Families: {len(facts.product_families)}\n"
            f"Technologies: {len(profile.technologies)}\n"
            f"Customer Segments: {len(profile.customer_segments)}\n"
            f"Synonyms: {len(facts.synonyms)}\n"
        )
        
        rule_engine_trace = (
            f"Brand Resolver\n"
            f"Input Entities: {total_kws}\n"
            f"Matches: {matched_brand}\n"
            f"Misses: {total_kws - matched_brand}\n\n"
            
            f"Category Resolver\n"
            f"Input Entities: {total_kws}\n"
            f"Matches: {matched_category}\n"
            f"Misses: {total_kws - matched_category}\n\n"
            
            f"Product Resolver\n"
            f"Input Entities: {total_kws}\n"
            f"Matches: {matched_product}\n"
            f"Misses: {total_kws - matched_product}\n\n"
            
            f"Product Family Resolver\n"
            f"Input Entities: {total_kws}\n"
            f"Matches: {matched_family}\n"
            f"Misses: {total_kws - matched_family}\n\n"
            
            f"Technology Resolver\n"
            f"Input Entities: {total_kws}\n"
            f"Matches: {matched_technology}\n"
            f"Misses: {total_kws - matched_technology}"
        )
        
        context.stage_diagnostics[self.stage_type.value] = f"{business_profile_trace}\n{rule_engine_trace}"

        return context
