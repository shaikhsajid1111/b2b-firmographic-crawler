from typing import List, Optional

from b2b_firmographic_crawler.base.searcher import CompanySearcher
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig, IQuery
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse
from b2b_firmographic_crawler.models.company_data import CompanyData
from b2b_firmographic_crawler.orchestrators.scraping_orchestrator import (
    CompanyPageScrapingService,
)
from b2b_firmographic_crawler.orchestrators.search_orchestrator import (
    CompanySearchingService,
)
from b2b_firmographic_crawler.searchers.search_by_name import CompanySearchByName
from b2b_firmographic_crawler.sources.base import SourceProvider
from b2b_firmographic_crawler.sources.owler.crawlers.company_name_scraper_chain import (
    OwlerCompanyNameScraperChain,
)
from b2b_firmographic_crawler.sources.owler.crawlers.http_company_search_crawler import (
    OwlerCompanySearchService,
)
from b2b_firmographic_crawler.sources.owler.crawlers.http_url_crawler import (
    OwlerHttpUrlScraper,
)
from b2b_firmographic_crawler.sources.owler.crawlers.selenium_base_search_crawler import (
    OwlerSeleniumSearchCrawler,
)
from b2b_firmographic_crawler.sources.owler.crawlers.selenium_base_url_crawler import (
    OwlerSeleniumUrlScraper,
)
from b2b_firmographic_crawler.sources.owler.crawlers.url_scraper_chain import (
    OwlerUrlScraperChain,
)
from b2b_firmographic_crawler.sources.owler.parser.company_page_parser import (
    OwlerParser,
)
from b2b_firmographic_crawler.sources.owler.parser.search_result_parser import (
    OwlerSearchParser,
)
from b2b_firmographic_crawler.sources.registry import SourceRegistry


@SourceRegistry.register("owler")
class OwlerSource(SourceProvider):
    """owler.com provider: company search + firmographic page scraping."""

    source_name = "owler"

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        searcher=None,
        url_scraper=None,
        page_parser=None,
    ) -> None:
        if searcher is not None and not isinstance(searcher, CompanySearcher):
            # Accept a raw CompanyNameScraper too, and wrap it with Owler's
            # search-response parser for convenience.
            searcher = CompanySearchByName(searcher, OwlerSearchParser())
        self.search_service = CompanySearchingService(
            searcher=searcher
            or CompanySearchByName(
                OwlerCompanyNameScraperChain(
                    (OwlerCompanySearchService(), OwlerSeleniumSearchCrawler())
                ),
                OwlerSearchParser(),
            ),
            cache_dir=cache_dir,
        )
        self.scraping_service = CompanyPageScrapingService(
            page_parser=page_parser or OwlerParser(),
            url_scraper=url_scraper
            or OwlerUrlScraperChain(
                (OwlerHttpUrlScraper(), OwlerSeleniumUrlScraper())
            ),
            cache_dir=cache_dir,
        )

    def search_company(
        self,
        query: str,
        config: Optional[ICrawlerConfig] = None,
    ) -> List[ISearchResponse]:
        return self.search_service.search_company(IQuery(company_name=query), config)

    def get_company_data(
        self,
        url: str,
        config: Optional[ICrawlerConfig] = None,
    ) -> Optional[CompanyData]:
        return self.scraping_service.scrape_company_page(url, config)