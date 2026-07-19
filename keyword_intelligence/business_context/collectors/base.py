"""Base collector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from keyword_intelligence.business_context.models import CollectedContent


class BaseCollector(ABC):
    """Abstract base class for business context collectors."""

    @abstractmethod
    def collect(self, company_name: str, website_url: str) -> list[CollectedContent]:
        """Collect raw content for the business profile generation.

        Args:
            company_name: Name of the company.
            website_url: Website URL to collect from.

        Returns:
            List of collected content entities.
        """
        pass
