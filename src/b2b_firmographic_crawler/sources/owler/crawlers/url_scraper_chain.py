from collections.abc import Iterable
from typing import Optional

from b2b_firmographic_crawler.base.scraper import UrlScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger

logger = get_logger("Owler URL scraper chain")


class OwlerUrlScraperChain(UrlScraper):
    """Try URL scrapers in order until one returns a page.

    For Owler, this tries HTTP first, then falls back to Selenium.
    """

    def __init__(self, scrapers: Iterable[UrlScraper]):
        self.scrapers = tuple(scrapers)
        if not self.scrapers:
            raise ValueError("UrlScraperChain requires at least one scraper")

    def build_proxies(self, proxy: Optional[str]):
        return None

    def scrape(self, url: str, config: Optional[ICrawlerConfig] = None) -> str:
        last_error: Optional[Exception] = None

        for scraper in self.scrapers:
            try:
                logger.info("Trying %s for %s", type(scraper).__name__, url)
                return scraper.scrape(url, config)
            except Exception as ex:
                last_error = ex
                logger.warning(
                    "%s failed for %s; trying the next scraper",
                    type(scraper).__name__,
                    url,
                    exc_info=True,
                )

        assert last_error is not None
        raise last_error