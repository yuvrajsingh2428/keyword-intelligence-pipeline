"""Models and Enums for the AI Intelligence Engine."""

from __future__ import annotations

from enum import Enum

from keyword_intelligence.models.base import AppBaseModel


class RelevanceEnum(str, Enum):
    """Keyword relevance classifications."""

    RELEVANT = "RELEVANT"
    IRRELEVANT = "IRRELEVANT"
    UNCERTAIN = "UNCERTAIN"


class AIProviderCapabilities(AppBaseModel):
    """Capabilities of a specific AI provider."""

    max_batch_size: int
    supports_batching: bool
    supports_streaming: bool
    supports_json_mode: bool
    supports_function_calling: bool


class KeywordResponseSchema(AppBaseModel):
    """Strict JSON schema expected from the LLM parsing phase."""

    keyword: str
    relevance: RelevanceEnum
    reason: str
    search_intent: str
    category: str
    confidence: float  # 0.0 to 1.0
    recommended_action: str


class AIClassificationResult(AppBaseModel):
    """Final merged output for a single keyword."""

    keyword: str
    relevance: RelevanceEnum
    reason: str
    search_intent: str
    category: str
    confidence: float
    recommended_action: str
    provider_used: str
    prompt_version: str
    processing_method: str = "AI"
    model: str = ""
    latency: float = 0.0


class AIEngineStatistics(AppBaseModel):
    """Statistics for an AI engine execution run."""

    total_keywords: int
    resolved_keywords: int
    unresolved_keywords: int
    batches_processed: int
    provider_calls: int
    successful_responses: int
    failed_responses: int
    validation_failures: int
    parse_failures: int
    cache_hits: int
    cache_misses: int
    retries: int
    average_batch_latency_ms: float
    average_provider_latency_ms: float
    execution_time_ms: float


class AIProviderMetrics(AppBaseModel):
    """Metrics for the specific AI provider used during a run."""

    provider_name: str
    provider_version: str
    prompts_executed: int
    tokens_estimated: int
    average_latency_ms: float
    cache_hit_ratio: float
    success_rate: float
