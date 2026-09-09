from collections.abc import Iterable
from typing import Optional

from b2b_firmographic_crawler.base.scraper import CompanyNameScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger

logger = get_logger("Owler company name scraper chain")


class OwlerCompanyNameScraperChain(CompanyNameScraper):
    """Try company-name scrapers in order until one returns a response.

    For Owler, this tries HTTP first, then falls back to Selenium.
    """

    def __init__(self, scrapers: Iterable[CompanyNameScraper]):
        self.scrapers = tuple(scrapers)
        if not self.scrapers:
            raise ValueError("CompanyNameScraperChain requires at least one scraper")

    def scrape(self, query: str, config: Optional[ICrawlerConfig] = None) -> str:
        last_error: Optional[Exception] = None

        for scraper in self.scrapers:
            try:
                logger.info("Trying %s for %s", type(scraper).__name__, query)
                return scraper.scrape(query, config)
            except Exception as ex:
                last_error = ex
                logger.warning(
                    "%s failed for %s; trying the next scraper",
                    type(scraper).__name__,
                    query,
                    exc_info=True,
                )

        assert last_error is not None
        raise last_error