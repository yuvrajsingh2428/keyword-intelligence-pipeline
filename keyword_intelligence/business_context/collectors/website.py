"""Website collector for Business Context."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from keyword_intelligence.business_context.collectors.base import BaseCollector
from keyword_intelligence.business_context.models import CollectedContent
from keyword_intelligence.config.settings import Settings


class WebsiteCollector(BaseCollector):
    """Collects content from a targeted list of priority pages on a website.

    Ignores non-business pages like careers, legal, etc.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.max_pages = settings.business_context_max_pages
        self.timeout = settings.business_context_crawl_timeout

        self.ignore_patterns = [
            r"/careers?/?",
            r"/jobs?/?",
            r"/investors?/?",
            r"/press(-releases?)?/?",
            r"/news/?",
            r"/blogs?/?",
            r"/privacy(-policy)?/?",
            r"/legal/?",
            r"/cookie(-policy)?/?",
            r"/terms(-of-service|-of-use)?/?",
            r"/support/?",
        ]
        self.ignore_re = re.compile("|".join(self.ignore_patterns), re.IGNORECASE)

    def collect(self, company_name: str, website_url: str) -> list[CollectedContent]:
        logger.info(f"WebsiteCollector starting for {website_url}")

        visited: set[str] = set()
        queue: list[str] = [website_url]
        results: list[CollectedContent] = []

        base_domain = urlparse(website_url).netloc

        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            while queue and len(results) < self.max_pages:
                url = queue.pop(0)

                # Normalize URL for deduplication
                norm_url = url.rstrip("/")
                if norm_url in visited:
                    continue
                visited.add(norm_url)

                if self.ignore_re.search(url):
                    continue

                if hasattr(self, "settings") and getattr(self.settings, "debug", False):
                    logger.debug(f"[DEBUG] Current URL: {url}")

                try:
                    resp = client.get(url)
                    resp.raise_for_status()

                    if "text/html" not in resp.headers.get("Content-Type", ""):
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")

                    title = (
                        soup.title.string.strip()
                        if soup.title and soup.title.string
                        else ""
                    )

                    # Remove noisy tags
                    for script in soup(
                        ["script", "style", "noscript", "svg", "button", "footer"]
                    ):
                        script.decompose()

                    text = soup.get_text(separator=" ", strip=True)
                    clean_text = re.sub(r"\s+", " ", text)

                    results.append(
                        CollectedContent(
                            source_url=url,
                            title=title,
                            clean_text=clean_text,
                            html=resp.text,
                        )
                    )

                    # If this is the homepage, extract links to seed the queue
                    if len(results) == 1:
                        for a_tag in soup.find_all("a", href=True):
                            href = a_tag["href"]
                            full_url = urljoin(url, href)
                            parsed_full = urlparse(full_url)

                            # Only same domain
                            if parsed_full.netloc == base_domain:
                                # Remove fragments
                                full_url = full_url.split("#")[0]
                                if full_url not in visited and full_url not in queue:
                                    queue.append(full_url)

                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")

        logger.info(f"WebsiteCollector finished. Collected {len(results)} pages.")
        return results
