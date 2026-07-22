"""Business Context Resolvers."""

from __future__ import annotations

import re
from typing import NamedTuple

from keyword_intelligence.business_context.models import BusinessProfile


class ResolvedBrand(NamedTuple):
    names: list[str]
    primary: str
    confidence: float


class ResolvedCategory(NamedTuple):
    name: str
    confidence: float


class ResolvedFamily(NamedTuple):
    name: str
    brand: str
    category: str
    confidence: float


class BrandResolver:
    """Resolves brands from keywords."""

    def __init__(self, profile: BusinessProfile) -> None:
        self.profile = profile

    def resolve(self, keyword: str) -> ResolvedBrand | None:
        """Find brand in keyword."""
        kw_lower = keyword.lower()
        found_brands = []

        # Always include the company name as a baseline brand
        brands_to_check = [b.entity for b in self.profile.business_facts.brands]
        if (
            self.profile.company_name
            and self.profile.company_name not in brands_to_check
        ):
            brands_to_check.append(self.profile.company_name)

        for brand_name in brands_to_check:
            patterns = [brand_name.lower()]
            if brand_name.lower() in self.profile.business_facts.synonyms:
                patterns.extend(
                    [
                        s.lower()
                        for s in self.profile.business_facts.synonyms[
                            brand_name.lower()
                        ]
                    ]
                )

            for pat in patterns:
                if re.search(rf"\b{re.escape(pat)}\b", kw_lower):
                    if brand_name not in found_brands:
                        found_brands.append(brand_name)
                    break

        if not found_brands:
            return None

        company_lower = self.profile.company_name.lower()
        primary = (
            self.profile.company_name
            if company_lower in [b.lower() for b in found_brands]
            else found_brands[0]
        )
        return ResolvedBrand(names=found_brands, primary=primary, confidence=0.98)


class CategoryResolver:
    """Resolves product categories from keywords."""

    def __init__(self, profile: BusinessProfile) -> None:
        self.profile = profile

    def resolve(self, keyword: str) -> ResolvedCategory | None:
        """Find category in keyword."""
        kw_lower = keyword.lower()
        for cat_evidence in self.profile.business_facts.categories:
            cat_name = cat_evidence.entity
            patterns = [cat_name.lower()]
            if cat_name.lower() in self.profile.business_facts.synonyms:
                patterns.extend(
                    [
                        s.lower()
                        for s in self.profile.business_facts.synonyms[cat_name.lower()]
                    ]
                )

            for pat in patterns:
                if re.search(rf"\b{re.escape(pat)}\b", kw_lower):
                    confidence = 0.85
                    if cat_evidence.confidence_score > 1.0:
                        confidence = 0.92
                    return ResolvedCategory(name=cat_name, confidence=confidence)
        return None


class ProductFamilyResolver:
    """Resolves specific product families from keywords."""

    def __init__(self, profile: BusinessProfile) -> None:
        self.profile = profile

    def resolve(self, keyword: str) -> ResolvedFamily | None:
        """Find product family in keyword."""
        kw_lower = keyword.lower()
        for fam_evidence in self.profile.business_facts.product_families:
            family_name = fam_evidence.entity
            patterns = [family_name.lower()]
            if family_name.lower() in self.profile.business_facts.synonyms:
                patterns.extend(
                    [
                        s.lower()
                        for s in self.profile.business_facts.synonyms[
                            family_name.lower()
                        ]
                    ]
                )

            for pat in patterns:
                if re.search(rf"\b{re.escape(pat)}\b", kw_lower):
                    brand = self.profile.company_name
                    category = "Unknown"
                    for (
                        parent_cat,
                        children,
                    ) in self.profile.business_facts.taxonomy.items():
                        if family_name in children:
                            category = parent_cat
                            break

                    return ResolvedFamily(
                        name=family_name,
                        brand=brand,
                        category=category,
                        confidence=1.00,
                    )
        return None
