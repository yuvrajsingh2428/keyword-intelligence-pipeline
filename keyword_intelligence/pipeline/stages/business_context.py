"""Business Context stage for the pipeline."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.business_context.engine import BusinessContextEngine
from keyword_intelligence.business_context.filter import DeterministicFilter
from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class BusinessContextStage(BaseStage):
    """Pipeline stage that builds the Business Profile and pre-filters keywords."""

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
        return "2.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        logger.info(f"Executing stage {self.stage_type.value}")

        # 1. Build or retrieve the profile
        profile = self.engine.process(self.company_name, self.website, self.industry)
        context.business_profile = profile

        # Print Validation Summary Part 1 & 2
        logger.info("\n--- Business Facts Summary ---")
        facts = profile.business_facts
        logger.info(f"Brands extracted: {len(facts.brands)}")
        logger.info(f"Product Families extracted: {len(facts.product_families)}")
        logger.info(f"Categories extracted: {len(facts.categories)}")
        logger.info(f"Products extracted: {len(facts.products)}")
        logger.info(f"Services extracted: {len(facts.services)}")
        logger.info(f"Taxonomy Nodes: {len(facts.taxonomy)}")
        logger.info(f"Aliases: {len(facts.aliases)}")
        logger.info(f"Synonyms: {len(facts.synonyms)}")

        all_confs = [
            e.confidence_score
            for lst in (
                facts.brands,
                facts.product_families,
                facts.categories,
                facts.products,
                facts.services,
            )
            for e in lst
        ]
        avg_conf = sum(all_confs) / len(all_confs) if all_confs else 0.0
        logger.info(f"Average Confidence: {avg_conf:.2f}")

        logger.info("\n--- Business Knowledge Summary ---")
        logger.info(f"Industry: {profile.industry}")
        logger.info(f"Description: {profile.business_description[:50]}...")
        logger.info(f"Technologies: {len(profile.technologies)}")
        logger.info(f"Customer Segments: {len(profile.customer_segments)}")

        # 2. Run deterministic filter
        if context.has_data and "keyword" in context.data.columns:
            logger.info("\nRunning deterministic pre-classification...")
            det_filter = DeterministicFilter(profile)

            relevance_col = []
            confidence_col = []
            reason_col = []

            matched_brand = 0
            matched_product = 0
            matched_category = 0
            matched_taxonomy = 0
            matched_alias = 0
            matched_synonym = 0
            sent_to_ai = 0

            for kw in context.data["keyword"]:
                rel, conf, reason = det_filter.classify(str(kw))
                relevance_col.append(rel.value if rel else None)
                confidence_col.append(conf)
                reason_col.append(reason)

                if rel.value == "RELEVANT":
                    if "Brand" in reason:
                        matched_brand += 1
                    elif "Product Match" in reason or "Product Family Match" in reason:
                        matched_product += 1
                    elif "Category" in reason:
                        matched_category += 1
                    elif "Taxonomy" in reason:
                        matched_taxonomy += 1
                    elif "Alias" in reason:
                        matched_alias += 1
                    elif "Synonym" in reason:
                        matched_synonym += 1
                elif rel.value == "UNCERTAIN":
                    sent_to_ai += 1

            context.data["business_relevance"] = relevance_col
            context.data["business_confidence"] = confidence_col
            context.data["business_reason"] = reason_col

            context.data["relevance"] = relevance_col
            context.data["category"] = [None] * len(relevance_col)
            context.data["intent"] = [None] * len(relevance_col)
            context.data["ai_confidence"] = confidence_col

            logger.info("\n--- Deterministic Classification Summary ---")
            logger.info(f"Matched by Brand: {matched_brand}")
            logger.info(f"Matched by Product: {matched_product}")
            logger.info(f"Matched by Category: {matched_category}")
            logger.info(f"Matched by Taxonomy: {matched_taxonomy}")
            logger.info(f"Matched by Alias: {matched_alias}")
            logger.info(f"Matched by Synonym: {matched_synonym}")
            logger.info(f"Sent to AI: {sent_to_ai}")

        return context
