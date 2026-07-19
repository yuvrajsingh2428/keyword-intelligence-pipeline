"""Extracts entities from HTML navigation elements."""

from __future__ import annotations

from bs4 import BeautifulSoup

from keyword_intelligence.business_context.extractors.base import (
    BaseExtractor,
    ExtractedEntity,
    ExtractedRelation,
)


class NavigationExtractor(BaseExtractor):
    """Extracts categories and products from navigation menus."""

    def extract(
        self, html: str, url: str
    ) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
        entities: list[ExtractedEntity] = []
        relations: list[ExtractedRelation] = []

        if not html:
            return entities, relations

        soup = BeautifulSoup(html, "lxml")

        # Look for nav tags or elements with role=navigation
        nav_elements = soup.find_all(["nav"]) + soup.find_all(
            attrs={"role": "navigation"}
        )

        for nav in nav_elements:
            # Look for lists within nav
            for ul in nav.find_all("ul"):
                for li in ul.find_all("li", recursive=False):
                    # Direct text in li or a tag
                    a_tag = li.find("a", recursive=False)
                    if a_tag and a_tag.string:
                        cat_name = a_tag.string.strip()
                        if len(cat_name) > 2:
                            entities.append(
                                ExtractedEntity(
                                    entity=cat_name,
                                    entity_type="Category",
                                    source="Navigation",
                                )
                            )

                            # Submenus
                            sub_ul = li.find("ul")
                            if sub_ul:
                                for sub_li in sub_ul.find_all("li"):
                                    sub_a = sub_li.find("a")
                                    if sub_a and sub_a.string:
                                        sub_name = sub_a.string.strip()
                                        if len(sub_name) > 2:
                                            # We guess sub-items are products or subcategories
                                            entities.append(
                                                ExtractedEntity(
                                                    entity=sub_name,
                                                    entity_type="Category",
                                                    source="Navigation",
                                                )
                                            )
                                            relations.append(
                                                ExtractedRelation(
                                                    source_entity=sub_name,
                                                    relation_type="belongs_to",
                                                    target_entity=cat_name,
                                                )
                                            )

        return entities, relations
