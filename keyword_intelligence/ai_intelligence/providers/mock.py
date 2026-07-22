"""Deterministic mock provider for AI classification."""

from __future__ import annotations

import hashlib
import json
import time

from keyword_intelligence.ai_intelligence.models import (
    AIProviderCapabilities,
    RelevanceEnum,
)
from keyword_intelligence.ai_intelligence.providers.base import AIProvider


class MockAIProvider(AIProvider):
    """Mock provider generating deterministic JSON based on keyword hashes."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def provider_version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 100

    @property
    def capabilities(self) -> AIProviderCapabilities:
        return AIProviderCapabilities(
            max_batch_size=1000,
            supports_batching=True,
            supports_streaming=False,
            supports_json_mode=True,
            supports_function_calling=False,
        )

    def health_check(self) -> bool:
        return True

    def classify(self, system_prompt: str, user_prompt: str) -> str:
        """Generate deterministic classification JSON based on keyword hash."""
        time.sleep(0.005)  # Simulate small network latency

        # We need to extract the keywords from the user prompt.
        # Since PromptRenderer replaces {{keywords}} with a JSON array string,
        # we can attempt to extract it, or just use regex.
        # For the mock, we can assume the user prompt contains the JSON list directly
        if "Business Analyst" in system_prompt:
            return json.dumps(
                {
                    "industry": "Computer Hardware",
                    "business_description": "Mock description for testing",
                    "brands": ["ThinkPad", "Legion", "Yoga", "IdeaPad"],
                    "product_families": ["Laptops", "Desktops", "Workstations"],
                    "product_categories": [
                        "Laptop",
                        "Desktop",
                        "Monitor",
                        "Accessories",
                        "Gaming",
                    ],
                    "products": ["ThinkPad X1", "Yoga 9i", "Legion 5"],
                    "services": ["Support", "Warranty"],
                    "technologies": ["Intel", "AMD", "Nvidia"],
                    "customer_segments": ["Business", "Gamers", "Students"],
                    "important_keywords": ["lenovo", "thinkpad"],
                    "negative_keywords": ["shoes", "clothing"],
                }
            )

        # Let's extract the JSON array from the prompt:
        # Business context might contain brackets, so we look for the keywords specifically
        keywords_json_str = user_prompt
        if "Classify these keywords:" in user_prompt:
            keywords_json_str = user_prompt.split("Classify these keywords:")[
                -1
            ].strip()

        start_idx = keywords_json_str.find("[")
        end_idx = keywords_json_str.rfind("]") + 1

        if start_idx == -1 or end_idx == 0:
            # Malformed prompt test case simulation
            if "malformed_json" in user_prompt:
                return '{"invalid": json'
            if "missing_fields" in user_prompt:
                return '[{"keyword": "test"}]'
            raise ValueError("Could not find JSON array of keywords in user prompt.")

        keywords_json = keywords_json_str[start_idx:end_idx]
        try:
            keywords = json.loads(keywords_json)
        except json.JSONDecodeError:
            return '{"invalid": json'

        if "malformed_json" in keywords:
            return '{"invalid": json'
        if "missing_fields" in keywords:
            return '[{"keyword": "missing_fields"}]'

        results = []
        for kw in keywords:
            hash_val = int(hashlib.md5(kw.encode("utf-8")).hexdigest(), 16)

            # Relevance
            rel_idx = hash_val % len(RelevanceEnum)
            classification = list(RelevanceEnum)[rel_idx]
            relevant = classification == RelevanceEnum.RELEVANT
            relevance_str = classification.value
            confidence = round(0.50 + ((hash_val % 51) / 100.0), 2)  # 0.50 to 1.00

            results.append(
                {
                    "keyword": kw,
                    "relevance": relevance_str,
                    "reason": "Mock semantic reasoning based on hash.",
                    "search_intent": "informational",
                    "category": "Laptop" if relevant else "Unknown",
                    "confidence": confidence,
                    "recommended_action": "Target" if relevant else "Ignore",
                }
            )

        return json.dumps(results)
