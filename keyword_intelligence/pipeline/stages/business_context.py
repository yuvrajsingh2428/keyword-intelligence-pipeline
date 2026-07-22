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
        logger.info(f"Executing stage {self.stage_type.value}")

        if not context.has_data or "keyword" not in context.data.columns:
            logger.warning(
                "No data or 'keyword' column missing in BusinessContextStage."
            )
            return context

        logger.info(
            f"Building dynamic company profile for {self.company_name} ({self.website})"
        )
        profile = self.engine.process(
            company_name=self.company_name, website=self.website, industry=self.industry
        )

        logger.info("Running deterministic business context enrichment...")
        rule_engine = BusinessRuleEngine(profile)

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
        matched_category = 0
        sent_to_ai = 0
        retail_filtered = 0

        for kw in context.data["keyword"]:
            res = rule_engine.process(str(kw))

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

            if res.product_family:
                matched_product += 1
            if res.brand:
                matched_brand += 1
            if res.category:
                matched_category += 1

        context.data["business_brand"] = brands
        context.data["business_category"] = categories
        context.data["business_product_family"] = families
        context.data["business_domain"] = domains
        context.data["business_relevance"] = relevances
        context.data["business_reason"] = reasons
        context.data["business_confidence"] = confidences
        context.data["requires_ai"] = requires_ais

        logger.info("\nBusiness Context")
        logger.info(f"Rows: {len(context.data)}")
        logger.info(f"Matched Brand: {matched_brand}")
        logger.info(f"Matched Category: {matched_category}")
        logger.info(f"Requires AI: {sent_to_ai}")
        logger.info(f"Retail Filtered: {retail_filtered}")

        return context
