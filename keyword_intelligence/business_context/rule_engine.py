"""Business Context Rule Engine."""

from __future__ import annotations

from keyword_intelligence.business_context.models import (
    BusinessProfile,
    KeywordBusinessContext,
)
from keyword_intelligence.business_context.resolvers import (
    BrandResolver,
    CategoryResolver,
    ProductFamilyResolver,
)


class BusinessRuleEngine:
    """Orchestrates deterministic rules to enrich keyword business context."""

    def __init__(self, profile: BusinessProfile) -> None:
        self.profile = profile
        self.brand_resolver = BrandResolver(profile)
        self.category_resolver = CategoryResolver(profile)
        self.family_resolver = ProductFamilyResolver(profile)

    def process(self, keyword: str) -> KeywordBusinessContext:
        """Process a single keyword and return its enriched context."""
        ctx = KeywordBusinessContext(keyword=keyword)

        # 2. Resolve Product Family (Highest precision)
        family = self.family_resolver.resolve(keyword)
        if family:
            ctx.product_family = family.name
            ctx.brand = family.brand
            ctx.company = self.profile.company_name
            ctx.category = family.category
            ctx.domain = self.profile.industry
            ctx.business_confidence = family.confidence
            ctx.requires_ai = False
            ctx.retail_relevance = True
            ctx.deterministic_reason = (
                f"Matched {family.name} product family from business taxonomy."
            )
            return ctx

        # 3. Resolve Brand & Category (Independent)
        brand = self.brand_resolver.resolve(keyword)
        category = self.category_resolver.resolve(keyword)

        if brand:
            ctx.brands_detected = brand.names
            ctx.primary_brand = brand.primary
            ctx.brand = brand.primary
            ctx.company = (
                self.profile.company_name
                if brand.primary == self.profile.company_name
                else None
            )
            ctx.business_confidence = brand.confidence

        if category:
            ctx.category = category.name
            ctx.business_confidence = max(ctx.business_confidence, category.confidence)

        # Comparison Query Detection
        if brand and len(brand.names) > 1:
            ctx.primary_brand = brand.names[0]
            ctx.secondary_brand = brand.names[1]
            ctx.search_intent = "Comparison"
            ctx.requires_ai = True
            ctx.retail_relevance = None
            ctx.deterministic_reason = f"Comparison query between {ctx.primary_brand} and {ctx.secondary_brand}"
            return ctx

        if brand or category:
            ctx.requires_ai = False
            ctx.retail_relevance = True
            match_parts = []
            if brand:
                match_parts.append(f"brand '{ctx.primary_brand}'")
            if category:
                match_parts.append(f"category '{category.name}'")

            ctx.deterministic_reason = (
                f"Matched {' and '.join(match_parts)} from business taxonomy."
            )
            return ctx

        # 4. Unknown Keyword
        ctx.requires_ai = True
        ctx.deterministic_reason = "No deterministic match found; escalating to AI."
        ctx.business_confidence = 0.0
        return ctx
