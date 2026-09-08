import os
from typing import Optional

from b2b_firmographic_crawler.base.parser import Parser
from b2b_firmographic_crawler.base.scraper import UrlScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.models.company_data import CompanyData
from b2b_firmographic_crawler.storage.persistent_disk_cache import DiskCache
from b2b_firmographic_crawler.utils.general_utils import GeneralUtils

logger = get_logger("Scraping Orchestrator")


class CompanyPageScrapingService:
    """Source-agnostic service for scraping and parsing company pages.

    Each source provides its own UrlScraper and Parser implementations,
    making this service fully source-agnostic.
    """

    def __init__(
        self,
        page_parser: Parser,
        url_scraper: UrlScraper,
        cache_dir: Optional[str] = None,
    ):
        self.url_scraper = url_scraper
        self.page_parser = page_parser
        self._disk_cache = DiskCache(CompanyData, cache_dir or os.getcwd())

    def fetch_page(self, url: str, config: Optional[ICrawlerConfig] = None) -> str:
        try:
            return self.url_scraper.scrape(url, config)
        except Exception:
            logger.exception("Error while fetching page: %s", url)
            raise

    def parse_page(self, page_data: str) -> Optional[CompanyData]:
        try:
            return self.page_parser.parse(page_data)
        except Exception:
            logger.exception("Error while parsing page")
            raise

    def scrape_company_page(
        self, url: str, config: Optional[ICrawlerConfig] = None
    ) -> Optional[CompanyData]:
        crawler_config = config if config is not None else ICrawlerConfig()
        try:
            if not crawler_config.force_rescrape:
                cached_data = self._disk_cache.get(url)
                if cached_data:
                    return cached_data

            page_data = self.fetch_page(url, crawler_config)
            parsed_page = self.page_parser.parse(page_data)
            self._disk_cache.set(
                url,
                parsed_page,
                GeneralUtils.generate_time_from_now(
                    crawler_config.company_cache_expiry_time_days
                ).timestamp(),
            )
            return parsed_page
        except Exception:
            logger.exception("Error while processing page: %s", url)
            raise
