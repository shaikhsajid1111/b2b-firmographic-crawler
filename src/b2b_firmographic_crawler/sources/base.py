from abc import ABC, abstractmethod
from typing import List, Optional

from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse
from b2b_firmographic_crawler.models.company_data import CompanyData


class SourceProvider(ABC):
    """Contract every data source must fulfil.

    The crawler is source-agnostic: a *source* (craft, owler, crunchbase, ...)
    is a self-contained bundle of a searcher (find companies by name) and a
    scraper/parser (extract firmographic data from a company page). Users
    select the source with a plain string::

        B2BFirmographicCrawler().get_company_data(url, source="owler")

    How to implement a new source (e.g. Owler or Crunchbase):

    1. Implement the low-level pieces for that website, subclassing the
       existing base contracts:
       - URL scraping:  ``base.scraper.UrlScraper`` (fetch + return raw page)
       - page parsing:  ``base.parser.Parser`` (raw page -> CompanyData)
       - name search:   ``base.scraper.CompanyNameScraper`` +
                        ``base.search_parser.SearchResponseParser``
                        (query -> List[ISearchResponse])

    2. Subclass ``SourceProvider``, wire the pieces together and register it::

        @SourceRegistry.register("owler")
        class OwlerSource(SourceProvider):
            source_name = "owler"

            def search_company(self, query, config=None):
                return self.search_service.search_company(...)

            def get_company_data(self, url, config=None):
                return self.scraping_service.scrape_company_page(url, config)

    3. Done - the string "owler" is now accepted everywhere.
    """

    source_name: str = ""

    @abstractmethod
    def search_company(
        self,
        query: str,
        config: Optional[ICrawlerConfig] = None,
    ) -> List[ISearchResponse]:
        """Search companies by name and return search suggestions."""
        ...

    @abstractmethod
    def get_company_data(
        self,
        url: str,
        config: Optional[ICrawlerConfig] = None,
    ) -> Optional[CompanyData]:
        """Scrape a company page URL and return the parsed CompanyData."""
        ...
