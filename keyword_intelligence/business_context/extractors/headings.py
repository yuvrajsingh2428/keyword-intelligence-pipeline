"""Extracts entities from H1/H2/H3 headings."""

from __future__ import annotations

from bs4 import BeautifulSoup

from keyword_intelligence.business_context.extractors.base import (
    BaseExtractor,
    ExtractedEntity,
    ExtractedRelation,
)


class HeadingExtractor(BaseExtractor):
    """Extracts main entities from headings."""

    def extract(
        self, html: str, url: str
    ) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
        entities: list[ExtractedEntity] = []
        relations: list[ExtractedRelation] = []

        if not html:
            return entities, relations

        soup = BeautifulSoup(html, "lxml")

        # H1 is usually the main product/category of the page
        h1s = soup.find_all("h1")
        for h1 in h1s:
            text = h1.get_text(strip=True)
            if len(text) > 3 and len(text) < 50:
                entities.append(
                    ExtractedEntity(entity=text, entity_type="Product", source="H1")
                )

        # H2 can be sub-products or features
        h2s = soup.find_all("h2")
        for h2 in h2s:
            text = h2.get_text(strip=True)
            if len(text) > 3 and len(text) < 30:
                entities.append(
                    ExtractedEntity(
                        entity=text,
                        entity_type="Product",  # Keep it generic, normalizer can adjust
                        source="H2",
                    )
                )

                # Relate H2 to the first H1 if present
                if h1s:
                    h1_text = h1s[0].get_text(strip=True)
                    if len(h1_text) > 3 and len(h1_text) < 50:
                        relations.append(
                            ExtractedRelation(
                                source_entity=text,
                                relation_type="belongs_to",
                                target_entity=h1_text,
                            )
                        )

        return entities, relations
