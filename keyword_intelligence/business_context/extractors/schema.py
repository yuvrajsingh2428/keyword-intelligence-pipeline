"""Extracts entities from schema.org JSON-LD."""

from __future__ import annotations

import json

from bs4 import BeautifulSoup

from keyword_intelligence.business_context.extractors.base import (
    BaseExtractor,
    ExtractedEntity,
    ExtractedRelation,
)


class SchemaOrgExtractor(BaseExtractor):
    """Extracts structured data from JSON-LD scripts."""

    def extract(
        self, html: str, url: str
    ) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
        entities: list[ExtractedEntity] = []
        relations: list[ExtractedRelation] = []

        if not html:
            return entities, relations

        soup = BeautifulSoup(html, "lxml")
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            if not script.string:
                continue

            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    data = [data]

                for item in data:
                    if not isinstance(item, dict):
                        continue

                    item_type = item.get("@type")

                    if item_type == "Product":
                        name = item.get("name")
                        brand = item.get("brand", {})
                        if isinstance(brand, dict):
                            brand = brand.get("name")

                        if name:
                            entities.append(
                                ExtractedEntity(
                                    entity=name,
                                    entity_type="Product",
                                    source="SchemaOrg",
                                )
                            )
                        if brand:
                            entities.append(
                                ExtractedEntity(
                                    entity=brand,
                                    entity_type="Brand",
                                    source="SchemaOrg",
                                )
                            )
                            if name:
                                relations.append(
                                    ExtractedRelation(
                                        source_entity=name,
                                        relation_type="belongs_to",
                                        target_entity=brand,
                                    )
                                )

                    elif item_type == "BreadcrumbList":
                        items = item.get("itemListElement", [])
                        if not isinstance(items, list):
                            items = []
                        valid_items = [i for i in items if isinstance(i, dict)]
                        prev_name = None
                        for i in sorted(
                            valid_items, key=lambda x: x.get("position", 0)
                        ):
                            cur_item = i.get("item", {})
                            name = (
                                cur_item.get("name")
                                if isinstance(cur_item, dict)
                                else None
                            )
                            name = name or i.get("name")
                            if name:
                                entities.append(
                                    ExtractedEntity(
                                        entity=name,
                                        entity_type="Category",
                                        source="SchemaOrg Breadcrumb",
                                    )
                                )
                                if prev_name:
                                    relations.append(
                                        ExtractedRelation(
                                            source_entity=name,
                                            relation_type="belongs_to",
                                            target_entity=prev_name,
                                        )
                                    )
                                prev_name = name

            except json.JSONDecodeError:
                continue

        return entities, relations
