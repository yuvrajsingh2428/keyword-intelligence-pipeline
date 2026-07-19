"""Cache for Business Profiles."""

from __future__ import annotations

from datetime import datetime, timedelta

from keyword_intelligence.business_context.models import BusinessProfile


class BusinessProfileCache:
    """In-memory cache for Business Profiles."""

    def __init__(self, ttl_hours: int = 24) -> None:
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: dict[str, tuple[datetime, BusinessProfile]] = {}

    def _generate_key(self, company_name: str, website: str) -> str:
        return f"{company_name.lower().strip()}:{website.lower().strip()}"

    def get(self, company_name: str, website: str) -> BusinessProfile | None:
        """Retrieve profile if it exists and is not expired."""
        key = self._generate_key(company_name, website)
        if key in self._cache:
            timestamp, profile = self._cache[key]
            if datetime.utcnow() - timestamp < self.ttl:
                return profile
            else:
                del self._cache[key]
        return None

    def put(self, profile: BusinessProfile) -> None:
        """Store a profile in the cache."""
        key = self._generate_key(profile.company_name, profile.website)
        self._cache[key] = (datetime.utcnow(), profile)

    def invalidate(self, company_name: str, website: str) -> None:
        """Forcefully remove a profile from the cache."""
        key = self._generate_key(company_name, website)
        if key in self._cache:
            del self._cache[key]
