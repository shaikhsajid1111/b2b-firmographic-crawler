from typing import Optional

from curl_cffi import requests

from b2b_firmographic_crawler.base.scraper import CompanyNameScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.sources.owler.utils import OwlerScrapingUtils

logger = get_logger(__name__)


class OwlerCompanySearchService(CompanyNameScraper):
    """Name search via Owler's ``basicSearchInternal`` API (plain HTTP GET)."""

    def build_proxies(self, proxy: Optional[str]) -> Optional[dict]:
        """Map proxy config to ``{"http": ..., "https": ...}`` form, or ``None`` when unset. (Note: unlike the Craft twin, the result is passed as ``proxies`` without Chrome impersonation — kept as-is.)"""
        if not proxy:
            return None
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    def scrape(self, query: str, config: Optional[ICrawlerConfig] = None) -> str:
        """GET the internal search API for ``query`` and return the raw body.

        Args:
            query: Free-text company name (interpolated as ``searchTerm``).
            config: Proxy settings (only ``proxy`` is honored here).

        Returns:
            Raw search API response body as text.

        Raises:
            Exception: Transport/HTTP errors (after logging).
        """
        try:
            headers = OwlerScrapingUtils.prepare_search_query_headers()
            payload = ""
            url = OwlerScrapingUtils.get_search_query_url(query)
            proxy: Optional[str] = config.proxy if config else None
            response = requests.request(
                "GET", url, data=payload, headers=headers, proxies=proxy
            )
            response.raise_for_status()
            return response.text
        except Exception as ex:
            logger.exception(f"Error while trying to fetch company by name: {ex}")
            raise
