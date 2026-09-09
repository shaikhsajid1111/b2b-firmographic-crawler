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
from b2b_firmographic_crawler.sources.craft.crawlers.company_name_scraper_chain import (
    CompanyNameScraperChain,
)
from b2b_firmographic_crawler.sources.craft.crawlers.http_company_search_crawler import (
    CraftCompanySearchCrawler,
)
from b2b_firmographic_crawler.sources.craft.crawlers.http_url_crawler import (
    CraftHttpUrlScraper,
)
from b2b_firmographic_crawler.sources.craft.crawlers.selenium_base_search_crawler import (
    SeleniumbaseSearchCrawler,
)
from b2b_firmographic_crawler.sources.craft.crawlers.selenium_base_url_crawler import (
    CraftSeleniumUrlScraper,
)
from b2b_firmographic_crawler.sources.craft.crawlers.url_scraper_chain import (
    CraftUrlScraperChain,
)
from b2b_firmographic_crawler.sources.craft.parsers.company_page_parser import (
    CraftParser,
)
from b2b_firmographic_crawler.sources.craft.parsers.search_result_parser import (
    CraftSearchParser,
)
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
        """Build search + scraping services with HTTP → Selenium fallbacks.

        Defaults wire Craft's search chain (HTTP crawler, then Selenium)
        with its search-response parser, and the page chain (HTTP
        scraper, then Selenium) with its page parser. The ``searcher`` /
        ``url_scraper`` / ``page_parser`` overrides are
        dependency-injection seams for tests and power users: a raw
        scraper is auto-wrapped with this source's response parser.

        Args:
            cache_dir: Base dir for this source's disk caches.
            searcher: Custom :class:`CompanySearcher` (or bare
                :class:`CompanyNameScraper`) replacing the default chain.
            url_scraper: Custom :class:`UrlScraper` replacing the
                default page chain.
            page_parser: Custom :class:`Parser` replacing the default.
        """
        if searcher is not None and not isinstance(searcher, CompanySearcher):
            # Accept a raw CompanyNameScraper too, and wrap it with Craft's
            # search-response parser for convenience.
            searcher = CompanySearchByName(searcher, CraftSearchParser())
        self.search_service = CompanySearchingService(
            searcher=searcher
            or CompanySearchByName(
                CompanyNameScraperChain(
                    (CraftCompanySearchCrawler(), SeleniumbaseSearchCrawler())
                ),
                CraftSearchParser(),
            ),
            cache_dir=cache_dir,
        )
        self.scraping_service = CompanyPageScrapingService(
            page_parser=page_parser or CraftParser(),
            url_scraper=url_scraper
            or CraftUrlScraperChain((CraftHttpUrlScraper(), CraftSeleniumUrlScraper())),
            cache_dir=cache_dir,
        )

    def search_company(
        self,
        query: str,
        config: Optional[ICrawlerConfig] = None,
    ) -> List[ISearchResponse]:
        """Search companies by name on craft.co (cached).

        Args:
            query: Free-text company name; wrapped into
                ``IQuery(company_name=...)``.
            config: Per-call crawl settings.

        Returns:
            Suggestion list (possibly empty).
        """
        return self.search_service.search_company(IQuery(company_name=query), config)

    def get_company_data(
        self,
        url: str,
        config: Optional[ICrawlerConfig] = None,
    ) -> Optional[CompanyData]:
        """Scrape a craft.co company page URL into CompanyData (cached).

        Args:
            url: Canonical company page URL.
            config: Per-call crawl settings.

        Returns:
            The parsed record, or ``None`` when unparseable.
        """
        return self.scraping_service.scrape_company_page(url, config)
