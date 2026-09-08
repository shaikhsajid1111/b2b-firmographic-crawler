from typing import Optional

from curl_cffi import requests

from b2b_firmographic_crawler.base.scraper import CompanyNameScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.sources.craft.utils import CraftScrapingUtils

logger = get_logger(__name__)


class CompanySearchCrawler(CompanyNameScraper):

    def build_proxies(self, proxy: Optional[str]) -> Optional[dict]:
        if not proxy:
            return None
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    def scrape(
        self, query: str, config: Optional[ICrawlerConfig] = None
    ) -> str:
        try:
            headers = CraftScrapingUtils.prepare_search_query_headers()
            payload = CraftScrapingUtils.prepare_search_query_payload(query)
            url = CraftScrapingUtils.get_search_query_url()
            proxy: Optional[str] = config.proxy if config else None
            response = requests.request(
                "POST",
                url,
                headers=headers,
                data=payload,
                impersonate="chrome",
                proxies=self.build_proxies(proxy),
                timeout=config.request_timeout if config else 30.0,
            )
            response.raise_for_status()
            return response.text
        except Exception as ex:
            logger.exception(f"Error while trying to fetch company by name: {ex}")
            raise
