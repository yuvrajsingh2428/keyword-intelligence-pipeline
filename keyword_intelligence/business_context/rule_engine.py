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
    ProductResolver,
    TechnologyResolver,
    SynonymResolver,
)


class BusinessRuleEngine:
    """Orchestrates deterministic rules to enrich keyword business context."""

    def __init__(self, profile: BusinessProfile) -> None:
        self.profile = profile

        # Repair broken wiring: Normalize the business profile entities to match pipeline keywords
        from keyword_intelligence.core.container import container
        from keyword_intelligence.normalization.engine import NormalizationEngine
        
        try:
            normalizer = container.resolve(NormalizationEngine)
        except Exception:
            normalizer = None

        norm_cache = {}
        if normalizer:
            import pandas as pd
            all_patterns = set()
            facts = self.profile.business_facts
            
            if self.profile.company_name:
                all_patterns.add(self.profile.company_name)
                
            for lst in [facts.brands, facts.categories, facts.product_families, facts.products]:
                for ent in lst:
                    all_patterns.add(ent.entity)
                    
            for k, v_list in facts.synonyms.items():
                all_patterns.add(k)
                all_patterns.update(v_list)
                
            for tech in self.profile.technologies:
                all_patterns.add(tech)
                
            pat_list = list(all_patterns)
            if pat_list:
                s = pd.Series(pat_list)
                res = normalizer.normalize_series(s)
                norm_cache = dict(zip(pat_list, res.normalized_series.tolist()))

        self.brand_resolver = BrandResolver(profile, norm_cache)
        self.category_resolver = CategoryResolver(profile, norm_cache)
        self.family_resolver = ProductFamilyResolver(profile, norm_cache)
        self.product_resolver = ProductResolver(profile, norm_cache)
        self.technology_resolver = TechnologyResolver(profile, norm_cache)
        self.synonym_resolver = SynonymResolver(profile, norm_cache)

    def process(self, keyword: str) -> KeywordBusinessContext:
        """Process a single keyword and return its enriched context."""
        ctx = KeywordBusinessContext(keyword=keyword)

        # Resolve all pieces of evidence
        family = self.family_resolver.resolve(keyword)
        product = self.product_resolver.resolve(keyword)
        brand = self.brand_resolver.resolve(keyword)
        category = self.category_resolver.resolve(keyword)
        tech = self.technology_resolver.resolve(keyword)
        synonym = self.synonym_resolver.resolve(keyword)

        # Aggregate context
        match_parts = []
        confidences = []

        if family:
            ctx.product_family = family.name
            ctx.brand = family.brand
            ctx.company = self.profile.company_name
            ctx.category = family.category
            ctx.domain = self.profile.industry
            match_parts.append(f"product family '{family.name}'")
            confidences.append(family.confidence)

        if product:
            ctx.product = product.name
            ctx.brand = product.brand if product.brand else ctx.brand
            ctx.company = self.profile.company_name
            ctx.category = product.category if product.category else ctx.category
            ctx.domain = self.profile.industry
            match_parts.append(f"product '{product.name}'")
            confidences.append(product.confidence)

        if brand:
            ctx.brands_detected = brand.names
            ctx.primary_brand = brand.primary
            ctx.brand = brand.primary
            ctx.company = (
                self.profile.company_name
                if brand.primary == self.profile.company_name
                else None
            )
            match_parts.append(f"brand '{brand.primary}'")
            confidences.append(brand.confidence)

        if category:
            ctx.category = category.name
            match_parts.append(f"category '{category.name}'")
            confidences.append(category.confidence)

        if tech:
            ctx.technology = tech.name
            match_parts.append(f"technology '{tech.name}'")
            confidences.append(tech.confidence)

        if synonym:
            ctx.synonym_matched = synonym.name
            match_parts.append(f"synonym '{synonym.name}'")
            confidences.append(synonym.confidence)

        # Comparison Query Detection
        if brand and len(brand.names) > 1:
            ctx.primary_brand = brand.names[0]
            ctx.secondary_brand = brand.names[1]
            ctx.search_intent = "Comparison"
            ctx.requires_ai = True
            ctx.retail_relevance = None
            ctx.deterministic_reason = f"Comparison query between {ctx.primary_brand} and {ctx.secondary_brand}"
            return ctx

        if match_parts:
            ctx.requires_ai = False
            ctx.retail_relevance = True
            ctx.business_confidence = max(confidences) if confidences else 1.0
            ctx.deterministic_reason = (
                f"Matched {' and '.join(match_parts)} from business taxonomy."
            )
            return ctx

        # 4. Unknown Keyword
        ctx.requires_ai = True
        ctx.deterministic_reason = "No deterministic match found; escalating to AI."
        ctx.business_confidence = 0.0
        return ctx
