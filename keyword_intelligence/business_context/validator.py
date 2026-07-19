"""Business Facts Validator."""

from __future__ import annotations

import re

from loguru import logger

from keyword_intelligence.business_context.models import BusinessProfile


class BusinessFactsValidator:
    """Validates enriched business facts and emits warnings for anomalies."""

    def __init__(self) -> None:
        self.generic_ui_labels = {
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
        }

    def validate(self, profile: BusinessProfile) -> None:
        """Validates BusinessFacts. Emits warnings, never raises exceptions."""
        logger.info("Running BusinessFactsValidator...")
        facts = profile.business_facts

        # 1. Count Rules
        if len(facts.brands) < 1:
            logger.warning("Validation Warning: Brands < 1.")

        if len(facts.products) < 10:
            logger.warning(
                f"Validation Warning: Products < 10 (found {len(facts.products)})."
            )

        if len(facts.categories) < 5:
            logger.warning(
                f"Validation Warning: Categories < 5 (found {len(facts.categories)})."
            )

        if (
            len(facts.product_families) > len(facts.products)
            and len(facts.products) > 0
        ):
            logger.warning("Validation Warning: Product Families > Products.")

        # Gather sets for reference validation
        all_product_names = {p.entity.lower() for p in facts.products}
        all_category_names = {c.entity.lower() for c in facts.categories}
        all_entity_names = (
            all_product_names
            | all_category_names
            | {b.entity.lower() for b in facts.brands}
            | {f.entity.lower() for f in facts.product_families}
            | {s.entity.lower() for s in facts.services}
        )

        # 2. Uniqueness Rules
        self._check_uniqueness(facts.brands, "Brands")
        self._check_uniqueness(facts.product_families, "Product Families")
        self._check_uniqueness(facts.products, "Products")
        self._check_uniqueness(facts.categories, "Categories")

        # 3. String Quality Rules
        for list_name, entities in [
            ("Brands", facts.brands),
            ("ProductFamilies", facts.product_families),
            ("Products", facts.products),
            ("Categories", facts.categories),
            ("Services", facts.services),
        ]:
            for ent in entities:
                name = ent.entity
                if not name:
                    logger.warning(
                        f"Validation Warning: Empty string found in {list_name}."
                    )
                elif not name.strip():
                    logger.warning(
                        f"Validation Warning: Whitespace-only string found in {list_name}."
                    )
                elif name.lower() in self.generic_ui_labels:
                    logger.warning(
                        f"Validation Warning: Generic UI label '{name}' found in {list_name}."
                    )
                elif re.fullmatch(r"^[0-9\W]+$", name):
                    logger.warning(
                        f"Validation Warning: Malformed entity '{name}' found in {list_name}."
                    )

        # 4. Product Family Relationship Rule
        for pf in facts.product_families:
            pf_lower = pf.entity.lower()
            # Check if any product starts with this family name
            has_supporting_product = any(
                p_lower.startswith(pf_lower) for p_lower in all_product_names
            )
            # If no direct prefix match, check if it's explicitly in the product list as an exact match
            if not has_supporting_product and pf_lower not in all_product_names:
                logger.warning(
                    f"Validation Warning: Product Family '{pf.entity}' has no supporting Product."
                )

        # 5. Alias Rules
        if len(facts.aliases) != len(set(facts.aliases.keys())):
            logger.warning(
                "Validation Warning: Aliases are not unique."
            )  # technically dict keys are always unique, but good to check if it was a list
        for alias, base_name in facts.aliases.items():
            if not alias.strip() or not base_name.strip():
                logger.warning(
                    f"Validation Warning: Empty alias or base_name ('{alias}' -> '{base_name}')."
                )
            # Every Alias references an existing Product or Category whenever possible
            if base_name.lower() not in all_entity_names:
                logger.warning(
                    f"Validation Warning: Alias target '{base_name}' does not reference an existing extracted entity."
                )

        # 6. Synonym Rules
        for term1, term_list in facts.synonyms.items():
            if len(set(term_list)) != len(term_list):
                logger.warning(
                    f"Validation Warning: Synonyms for '{term1}' contain duplicates."
                )
            for term2 in term_list:
                # Every Synonym contains exactly two normalized valid entities (bidirectional is checked implicitly)
                if not term1.strip() or not term2.strip():
                    logger.warning(
                        f"Validation Warning: Empty synonym found ('{term1}', '{term2}')."
                    )

        logger.info("BusinessFactsValidator completed.")

    def _check_uniqueness(self, entities: list, list_name: str) -> None:
        names = [e.entity.lower() for e in entities]
        if len(names) != len(set(names)):
            logger.warning(
                f"Validation Warning: Duplicate entities found in {list_name} after normalization."
            )
