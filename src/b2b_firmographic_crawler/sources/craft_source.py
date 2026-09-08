from typing import List, Optional

from b2b_firmographic_crawler.base.searcher import CompanySearcher
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig, IQuery
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse
from b2b_firmographic_crawler.models.company_data import CompanyData
from b2b_firmographic_crawler.orchestrators.scraping_orchestrator import (
    CraftCompanyPageScrapingService,
)
from b2b_firmographic_crawler.orchestrators.search_orchestrator import (
    CraftCompanySearchingService,
)
from b2b_firmographic_crawler.parsers.search_result_parser import CraftSearchParser
from b2b_firmographic_crawler.searchers.search_by_name import CompanySearchByName
from b2b_firmographic_crawler.sources.base import SourceProvider
from b2b_firmographic_crawler.sources.registry import SourceRegistry


@SourceRegistry.register("craft")
class CraftSource(SourceProvider):
    """craft.co provider: company search + firmographic page scraping."""

    source_name = "craft"

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        searcher=None,
        url_scraper=None,
        page_parser=None,
    ) -> None:
        if searcher is not None and not isinstance(searcher, CompanySearcher):
            # Accept a raw CompanyNameScraper too, and wrap it with Craft's
            # search-response parser for convenience.
            searcher = CompanySearchByName(searcher, CraftSearchParser())
        self.search_service = CraftCompanySearchingService(
            searcher=searcher, cache_dir=cache_dir
        )
        self.scraping_service = CraftCompanyPageScrapingService(
            url_scraper=url_scraper, page_parser=page_parser, cache_dir=cache_dir
        )

    def search_company(
        self,
        query: str,
        config: Optional[ICrawlerConfig] = None,
    ) -> List[ISearchResponse]:
        return self.search_service.search_company(
            IQuery(company_name=query), config
        )

    def get_company_data(
        self,
        url: str,
        config: Optional[ICrawlerConfig] = None,
    ) -> Optional[CompanyData]:
        return self.scraping_service.scrape_company_page(url, config)
