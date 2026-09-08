from typing import Optional

from curl_cffi import requests

from b2b_firmographic_crawler.base.scraper import CompanyNameScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.sources.owler.utils import OwlerScrapingUtils

logger = get_logger(__name__)


class OwlerCompanySearchService(CompanyNameScraper):

    def build_proxies(self, proxy: Optional[str]) -> Optional[dict]:
        if not proxy:
            return None
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    def scrape(self, query: str, config: Optional[ICrawlerConfig] = None) -> str:
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
