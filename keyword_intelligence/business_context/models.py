"""Business Context Enrichment models."""

from __future__ import annotations

from pydantic import Field

from keyword_intelligence.models.base import AppBaseModel


class EntityEvidence(AppBaseModel):
    """Evidence for a detected entity from the website."""

    entity: str
    entity_type: str
    evidence_sources: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0


class Relationship(AppBaseModel):
    """Relationship between two entities."""

    source: str
    relation_type: str
    target: str


class BusinessFacts(AppBaseModel):
    """Extracted factual taxonomy of a business."""

    products: list[EntityEvidence] = Field(default_factory=list)
    brands: list[EntityEvidence] = Field(default_factory=list)
    categories: list[EntityEvidence] = Field(default_factory=list)
    services: list[EntityEvidence] = Field(default_factory=list)
    product_families: list[EntityEvidence] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    taxonomy: dict[str, list[str]] = Field(default_factory=dict)
    aliases: dict[str, str] = Field(default_factory=dict)
    synonyms: dict[str, list[str]] = Field(default_factory=dict)


class CollectedContent(AppBaseModel):
    """Raw content collected from a webpage."""

    source_url: str
    title: str
    clean_text: str
    html: str


class ProfileMetadata(AppBaseModel):
    """Metadata about the generated profile."""

    source_pages: list[str] = Field(default_factory=list)
    llm_model: str = ""
    quality_score: float = 0.0


class BusinessProfile(AppBaseModel):
    """The fully generated dynamic company profile."""

    company_name: str
    website: str
    industry: str = ""
    business_description: str = ""
    technologies: list[str] = Field(default_factory=list)
    customer_segments: list[str] = Field(default_factory=list)
    important_keywords: list[str] = Field(default_factory=list)
    business_concepts: list[str] = Field(default_factory=list)
    business_facts: BusinessFacts = Field(default_factory=BusinessFacts)
    metadata: ProfileMetadata = Field(default_factory=ProfileMetadata)


class KeywordBusinessContext(AppBaseModel):
    """The enriched business context for a single keyword."""

    keyword: str
    company: str | None = None
    brands_detected: list[str] = Field(default_factory=list)
    primary_brand: str | None = None
    secondary_brand: str | None = None
    brand: str | None = None
    category: str | None = None
    product_family: str | None = None
    product: str | None = None
    technology: str | None = None
    synonym_matched: str | None = None
    domain: str | None = None
    retail_relevance: bool | None = None
    search_intent: str | None = None
    deterministic_reason: str | None = None
    business_confidence: float = 0.0
    requires_ai: bool = True
