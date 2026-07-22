"""Deterministic rule-based pre-classifier."""

from __future__ import annotations

import re

from keyword_intelligence.ai_intelligence.models import RelevanceEnum
from keyword_intelligence.business_context.models import BusinessProfile


class DeterministicFilter:
    """Pre-classifies keywords using deterministic rules against the BusinessFacts."""

    CONF_NEGATIVE = 95.0
    CONF_COMPANY = 99.0
    CONF_TAXONOMY = 90.0
    CONF_BRAND_BASE = 70.0
    CONF_BRAND_MAX = 95.0
    CONF_PRODUCT_BASE = 65.0
    CONF_PRODUCT_MAX = 90.0
    CONF_CATEGORY_BASE = 60.0
    CONF_CATEGORY_MAX = 85.0
    CONF_FAMILY_BASE = 60.0
    CONF_FAMILY_MAX = 85.0
    CONF_ALIAS = 85.0
    CONF_TECH = 80.0
    CONF_SERVICE = 75.0
    CONF_SEGMENT = 70.0
    CONF_KEYWORD = 65.0
    CONF_MULTIPLIER = 5.0

    def __init__(self, profile: BusinessProfile) -> None:
        self.profile = profile
        self.company_name = profile.company_name.lower()
        self.facts = profile.business_facts

        # Build optimized lookup sets
        self.brands = {b.entity.lower(): b for b in self.facts.brands}
        self.products = {p.entity.lower(): p for p in self.facts.products}
        self.categories = {c.entity.lower(): c for c in self.facts.categories}
        self.families = {f.entity.lower(): f for f in self.facts.product_families}
        self.services = {s.entity.lower(): s for s in self.facts.services}

        self.technologies = {t.lower() for t in profile.technologies}
        self.segments = {s.lower() for s in profile.customer_segments}
        self.keywords = {k.lower() for k in profile.important_keywords}

        self.taxonomy = {}
        for parent, children in self.facts.taxonomy.items():
            self.taxonomy[parent.lower()] = [c.lower() for c in children]

        self.aliases = {k.lower(): v.lower() for k, v in self.facts.aliases.items()}

    def classify(self, keyword: str) -> tuple[RelevanceEnum, float, str]:
        """Classify a single keyword.

        Returns:
            Tuple of (RelevanceEnum, Confidence (0-100), Reason string).
        """
        kw = keyword.lower().strip()

        # 2. Company match
        if self.company_name in kw:
            return (
                RelevanceEnum.RELEVANT,
                self.CONF_COMPANY,
                f"Company Match: {self.profile.company_name}",
            )

        # 3. Taxonomy Match
        for parent_lower, children_lower in self.taxonomy.items():
            if re.search(r"\b" + re.escape(parent_lower) + r"\b", kw):
                orig_parent = next(
                    (p for p in self.facts.taxonomy if p.lower() == parent_lower),
                    parent_lower.title(),
                )
                return (
                    RelevanceEnum.RELEVANT,
                    self.CONF_TAXONOMY,
                    f"Taxonomy Match: Parent ({orig_parent})",
                )
            for child_lower in children_lower:
                if re.search(r"\b" + re.escape(child_lower) + r"\b", kw):
                    orig_parent = next(
                        (p for p in self.facts.taxonomy if p.lower() == parent_lower),
                        parent_lower.title(),
                    )
                    orig_child = child_lower.title()
                    return (
                        RelevanceEnum.RELEVANT,
                        self.CONF_TAXONOMY,
                        f"Taxonomy Match: {orig_parent} → {orig_child}",
                    )

        # 4. Brand match
        for brand, b_obj in self.brands.items():
            if re.search(r"\b" + re.escape(brand) + r"\b", kw):
                conf = min(
                    self.CONF_BRAND_MAX,
                    self.CONF_BRAND_BASE
                    + b_obj.confidence_score * self.CONF_MULTIPLIER,
                )
                return RelevanceEnum.RELEVANT, conf, f"Brand Match: {b_obj.entity}"

        # 5. Product match
        for prod, p_obj in self.products.items():
            if re.search(r"\b" + re.escape(prod) + r"\b", kw):
                conf = min(
                    self.CONF_PRODUCT_MAX,
                    self.CONF_PRODUCT_BASE
                    + p_obj.confidence_score * self.CONF_MULTIPLIER,
                )
                return RelevanceEnum.RELEVANT, conf, f"Product Match: {p_obj.entity}"

        # 6. Category match
        for cat, c_obj in self.categories.items():
            if re.search(r"\b" + re.escape(cat) + r"\b", kw):
                conf = min(
                    self.CONF_CATEGORY_MAX,
                    self.CONF_CATEGORY_BASE
                    + c_obj.confidence_score * self.CONF_MULTIPLIER,
                )
                return RelevanceEnum.RELEVANT, conf, f"Category Match: {c_obj.entity}"

        # 7. Family match
        for fam, f_obj in self.families.items():
            if re.search(r"\b" + re.escape(fam) + r"\b", kw):
                conf = min(
                    self.CONF_FAMILY_MAX,
                    self.CONF_FAMILY_BASE
                    + f_obj.confidence_score * self.CONF_MULTIPLIER,
                )
                return (
                    RelevanceEnum.RELEVANT,
                    conf,
                    f"Product Family Match: {f_obj.entity}",
                )

        # 8. Alias Match
        for alias, canon in self.aliases.items():
            if re.search(r"\b" + re.escape(alias) + r"\b", kw):
                return (
                    RelevanceEnum.RELEVANT,
                    self.CONF_ALIAS,
                    f"Alias Match: {alias} → {canon}",
                )

        # 9. Other LLM enriched fields
        for tech in self.technologies:
            if re.search(r"\b" + re.escape(tech) + r"\b", kw):
                return (
                    RelevanceEnum.RELEVANT,
                    self.CONF_TECH,
                    f"Technology match: {tech}",
                )

        for svc, s_obj in self.services.items():
            if re.search(r"\b" + re.escape(svc) + r"\b", kw):
                return (
                    RelevanceEnum.RELEVANT,
                    self.CONF_SERVICE,
                    f"Service match: {s_obj.entity}",
                )

        for seg in self.segments:
            if re.search(r"\b" + re.escape(seg) + r"\b", kw):
                return (
                    RelevanceEnum.RELEVANT,
                    self.CONF_SEGMENT,
                    f"Customer segment match: {seg}",
                )

        for ikw in self.keywords:
            if re.search(r"\b" + re.escape(ikw) + r"\b", kw):
                return (
                    RelevanceEnum.RELEVANT,
                    self.CONF_KEYWORD,
                    f"Business keyword match: {ikw}",
                )

        return RelevanceEnum.UNCERTAIN, 0.0, "No deterministic match found"
