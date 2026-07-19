"""Business Facts Enricher."""

from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from loguru import logger

from keyword_intelligence.business_context.models import (
    BusinessProfile,
    CollectedContent,
    EntityEvidence,
)
from keyword_intelligence.config.settings import Settings


class BusinessFactsEnricher:
    """Enriches extracted business facts with generic dynamic discovery."""

    STOP_WORDS = frozenset(
        {
            "home",
            "about",
            "contact",
            "footer",
            "explore",
            "quick links",
            "resources",
            "careers",
            "support",
            "benefits",
            "latest",
            "help",
            "menu",
            "search",
            "shop",
            "cart",
            "account",
            "login",
            "register",
            "privacy",
            "terms",
            "conditions",
            "policy",
            "sitemap",
            "news",
            "blog",
            "investors",
            "partners",
            "affiliates",
            "faq",
            "faqs",
            "help is here",
            "buy",
            "store",
            "accessories",
            "deals",
            "offers",
            "products",
            "services",
            "solutions",
            "industries",
            "company",
            "pro",
            "air",
            "new",
            "mac",
            "apple",
            "the",
            "get",
            "switch",
            "compare",
            "smart",
            "magic",
            "all",
            "ways",
            "macos",
            "health",
            "supply",
            "chain",
            "education",
            "shopping",
        }
    )

    INDUSTRY_SYNONYMS = {
        "laptop": "notebook",
        "notebook": "laptop",
        "display": "monitor",
        "monitor": "display",
        "desktop": "pc",
        "pc": "desktop",
        "earbuds": "wireless earbuds",
        "dock": "docking station",
    }

    PATTERN_SLASH = re.compile(r"^(.*?)\s*/\s*(.*?)$", re.IGNORECASE)
    PATTERN_PARENTHESIS = re.compile(r"^(.*?)\s*\(([^)]+)\)$")

    def __init__(self, settings: Settings) -> None:
        self.min_family_confidence = settings.business_context_min_family_confidence
        self.min_brand_confidence = settings.business_context_min_brand_confidence
        self.min_alias_confidence = settings.business_context_min_alias_confidence
        self.min_synonym_confidence = settings.business_context_min_synonym_confidence

    def enrich(self, draft: BusinessProfile, contents: list[CollectedContent]) -> None:
        """Enriches the BusinessProfile draft in-place without removing existing data."""
        logger.info("Running BusinessFactsEnricher...")
        facts = draft.business_facts

        # 1. Noise Filtering and Normalization (Deduplication)
        facts.categories = self._filter_and_dedupe(facts.categories)
        facts.products = self._filter_and_dedupe(facts.products)
        facts.services = self._filter_and_dedupe(facts.services)
        facts.brands = self._filter_and_dedupe(facts.brands)
        facts.product_families = self._filter_and_dedupe(facts.product_families)

        # 2. Brand Detection
        self._enrich_brands(draft, contents)

        # 3. Product Family Detection
        self._enrich_product_families(draft)

        # 4. Synonym Detection (e.g., "Laptops & Notebooks")
        self._enrich_synonyms(draft)

        # 5. Alias Detection (e.g., "MacBook Pro (MBP)")
        self._enrich_aliases(draft)

        logger.info("BusinessFactsEnricher completed.")

    def _filter_and_dedupe(
        self, entities: list[EntityEvidence]
    ) -> list[EntityEvidence]:
        """Removes noise and exactly duplicate entity names."""
        seen = set()
        clean = []
        for ent in entities:
            # Normalize whitespace
            name = re.sub(r"\s+", " ", ent.entity.strip())

            if not name or len(name) < 2:
                continue

            lower_name = name.lower()
            if lower_name in self.STOP_WORDS:
                continue

            # Basic validation: drop if purely numeric or special chars
            if re.fullmatch(r"^[0-9\W]+$", name):
                continue

            if lower_name not in seen:
                seen.add(lower_name)
                # Update with normalized name
                ent.entity = name
                clean.append(ent)
        return clean

    def _enrich_brands(
        self, draft: BusinessProfile, contents: list[CollectedContent]
    ) -> None:
        """Detect brands from domain, company name, and open graph."""
        facts = draft.business_facts
        existing_brand_names = {b.entity.lower() for b in facts.brands}

        potential_brands = set()

        # Company name itself
        if draft.company_name:
            potential_brands.add(draft.company_name)

        # Domain parsing
        if draft.website:
            try:
                parsed = urlparse(draft.website)
                netloc = parsed.netloc
                if netloc.startswith("www."):
                    netloc = netloc[4:]
                parts = netloc.split(".")
                if parts:
                    domain_brand = parts[0].title()
                    potential_brands.add(domain_brand)
            except Exception:
                pass

        # Check titles / og:site_name from contents
        for content in contents:
            if not content.html:
                continue
            try:
                soup = BeautifulSoup(content.html, "lxml")
                og_site_name = soup.find("meta", property="og:site_name")
                if og_site_name and og_site_name.get("content"):
                    potential_brands.add(og_site_name["content"].strip())
            except Exception:
                pass

        # Add discovered brands using thresholds
        for brand in potential_brands:
            brand = self._canonicalize_brand(brand, draft.company_name)
            b_lower = brand.lower()
            if b_lower not in existing_brand_names and len(brand) > 2:
                if b_lower in self.STOP_WORDS and b_lower != draft.company_name.lower():
                    continue

                # Calculate confidence
                conf = 1.0
                if b_lower == draft.company_name.lower():
                    conf += 1.0

                if conf >= self.min_brand_confidence:
                    facts.brands.append(
                        EntityEvidence(
                            entity=brand,
                            entity_type="Brand",
                            evidence_sources=["BusinessFactsEnricher"],
                            confidence_score=conf,
                        )
                    )
                    existing_brand_names.add(b_lower)

    def _canonicalize_brand(self, brand: str, company_name: str) -> str:
        # Strip common localizations and generic prefixes
        patterns = [
            r"\(india\)",
            r"\(in\)",
            r"- india",
            r"- in",
            r"\(us\)",
            r"\(uk\)",
            r"\(eu\)",
            r"\(asia\)",
            r"education -",
            r"business -",
            r"store -",
            r"education",
            r"business",
            r"store",
            r"shop",
        ]
        canon = brand
        for p in patterns:
            canon = re.sub(p, "", canon, flags=re.IGNORECASE)
        canon = canon.strip(" -")

        # If it contains the company name, fallback to company name
        if company_name and company_name.lower() in canon.lower():
            return company_name
        return canon

    def _enrich_product_families(self, draft: BusinessProfile) -> None:
        """Dynamically detect product families using prefix frequency analysis."""
        facts = draft.business_facts
        existing_family_names = {f.entity.lower() for f in facts.product_families}

        # Gather all relevant entity names
        all_names = [e.entity for e in facts.products] + [
            e.entity for e in facts.categories
        ]

        prefix_counts = defaultdict(int)
        prefix_sources = defaultdict(list)

        for name in all_names:
            words = name.split()
            if not words:
                continue

            first_word = words[0]
            # Must be a substantial word, starting with capital (heuristics)
            if len(first_word) > 2 and first_word[0].isupper():
                if (
                    first_word.lower() not in self.STOP_WORDS
                    and first_word.lower() != draft.company_name.lower()
                ):
                    prefix_counts[first_word] += 1
                    prefix_sources[first_word].append(name)

            # Also check two-word prefixes for families like "Mac Studio"
            if len(words) >= 2:
                two_word = f"{words[0]} {words[1]}"
                if (
                    len(two_word) > 5
                    and words[0][0].isupper()
                    and words[1][0].isupper()
                ):
                    w1_lower = words[0].lower()
                    w2_lower = words[1].lower()
                    comp_lower = draft.company_name.lower()

                    w1_invalid = w1_lower in self.STOP_WORDS and w1_lower != comp_lower
                    w2_invalid = w2_lower in self.STOP_WORDS

                    if (
                        not w1_invalid
                        and not w2_invalid
                        and two_word.lower() not in self.STOP_WORDS
                    ):
                        prefix_counts[two_word] += 1
                        prefix_sources[two_word].append(name)

        # Promote to ProductFamily
        for prefix, count in prefix_counts.items():
            if count >= self.min_family_confidence:
                p_lower = prefix.lower()

                # Check if it has at least two DISTINCT descendants
                descendants = set(prefix_sources[prefix])
                if len(descendants) < 2:
                    continue

                if (
                    p_lower not in existing_family_names
                    and p_lower not in self.STOP_WORDS
                ):
                    facts.product_families.append(
                        EntityEvidence(
                            entity=prefix,
                            entity_type="ProductFamily",
                            evidence_sources=list(descendants)[:3],
                            confidence_score=float(count),
                        )
                    )
                    existing_family_names.add(p_lower)

    def _enrich_synonyms(self, draft: BusinessProfile) -> None:
        """Detect synonyms using linguistic rules, dropping generic relational 'and' patterns."""
        facts = draft.business_facts

        all_entities = [e.entity for e in facts.categories + facts.products]

        for name in all_entities:
            match = self.PATTERN_SLASH.match(name)
            if match:
                term1 = match.group(1).strip()
                term2 = match.group(2).strip()

                if len(term1) > 2 and len(term2) > 2:
                    t1_lower = term1.lower()
                    t2_lower = term2.lower()

                    # Validation: check industry dictionary or if one is a suffix of another
                    is_valid = False
                    if (
                        self.INDUSTRY_SYNONYMS.get(t1_lower) == t2_lower
                        or t1_lower.endswith(t2_lower)
                        or t2_lower.endswith(t1_lower)
                    ):
                        is_valid = True

                    if is_valid and self.min_synonym_confidence <= 1.0:
                        if t1_lower not in facts.synonyms:
                            facts.synonyms[t1_lower] = []
                        if term2 not in facts.synonyms[t1_lower]:
                            facts.synonyms[t1_lower].append(term2)

                        if t2_lower not in facts.synonyms:
                            facts.synonyms[t2_lower] = []
                        if term1 not in facts.synonyms[t2_lower]:
                            facts.synonyms[t2_lower].append(term1)

    def _enrich_aliases(self, draft: BusinessProfile) -> None:
        """Detect aliases using parenthesis patterns: Base Name (Alias)."""
        facts = draft.business_facts

        all_entities = (
            facts.products
            + facts.categories
            + facts.services
            + facts.brands
            + facts.product_families
        )

        for ent in all_entities:
            match = self.PATTERN_PARENTHESIS.match(ent.entity)
            if match:
                base_name = match.group(1).strip()
                alias = match.group(2).strip()

                if self._is_valid_alias(alias) and len(base_name) > 0:
                    # Parenthesis extraction gets baseline confidence of 1.0
                    conf = 1.0
                    if conf >= self.min_alias_confidence:
                        facts.aliases[alias] = base_name

        # Simple acronym detection (e.g. Artificial Intelligence -> AI)
        names = [e.entity for e in all_entities]
        for name in names:
            words = name.split()
            if len(words) > 1:
                acronym = "".join([w[0].upper() for w in words if w.isalpha()])
                if self._is_valid_alias(acronym) and acronym in names:
                    # Acronym extraction gets confidence 1.0
                    conf = 1.0
                    if conf >= self.min_alias_confidence:
                        facts.aliases[acronym] = name

    def _is_valid_alias(self, alias: str) -> bool:
        """Reject aliases that are numbers, measurements, years, or generic locations."""
        if not alias or len(alias) < 2:
            return False

        # Reject numbers only
        if re.fullmatch(r"^\d+$", alias):
            return False

        # Reject years
        if re.fullmatch(r"^(19|20)\d{2}$", alias):
            return False

        # Reject measurements (e.g. 1M, 2M, 500GB, 32inch)
        if re.fullmatch(
            r"^\d+\s*(m|cm|mm|inch|gb|tb|hz|khz|mhz|w|kw|v)$", alias, re.IGNORECASE
        ):
            return False

        # Reject generic country/region strings
        locations = {"in", "india", "us", "uk", "usa", "eu", "asia"}
        if alias.lower() in locations:
            return False

        # Keep if it looks like an abbreviation (all caps or alphanum)
        if re.fullmatch(r"^[A-Z0-9\-]+$", alias):
            return True

        return True
