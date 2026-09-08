import os
from typing import List, Optional

from b2b_firmographic_crawler.base.searcher import CompanySearcher
from b2b_firmographic_crawler.crawlers.company_name_scraper_chain import (
    CompanyNameScraperChain,
)
from b2b_firmographic_crawler.crawlers.http_company_search_crawler import (
    CompanySearchCrawler,
)
from b2b_firmographic_crawler.crawlers.selenium_base_search_crawler import (
    SeleniumbaseSearchCrawler,
)
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig, IQuery
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.parsers.search_result_parser import CraftSearchParser
from b2b_firmographic_crawler.searchers.search_by_name import CompanySearchByName
from b2b_firmographic_crawler.storage.persistent_disk_cache import DiskCache
from b2b_firmographic_crawler.utils.general_utils import GeneralUtils

logger = get_logger("Craft Search Orchestrator")


class CraftCompanySearchingService:
    def __init__(
        self,
        searcher: Optional[CompanySearcher] = None,
        cache_dir: Optional[str] = None,
    ):
        self.searcher = searcher or CompanySearchByName(
            CompanyNameScraperChain(
                (CompanySearchCrawler(), SeleniumbaseSearchCrawler())
            ),
            CraftSearchParser(),
        )
        self._disk_cache = DiskCache(
            ISearchResponse, cache_dir or os.getcwd()
        )  # intentionally kept away from user control

    def search_company(
        self, query: IQuery, config: Optional[ICrawlerConfig] = None
    ) -> List[ISearchResponse]:
        crawler_config = config or ICrawlerConfig()
        results: list[ISearchResponse] = []

        try:
            if query.company_name:
                if not crawler_config.force_rescrape:
                    result = self._disk_cache.get(
                        query.company_name,
                    )
                    if result:
                        return result

                result = self.searcher.search_by_name(
                    query.company_name, crawler_config
                )
                self._disk_cache.set(
                    query.company_name,
                    result,
                    GeneralUtils.generate_time_from_now(
                        crawler_config.search_cache_expiry_time_days
                    ).timestamp(),
                )
                if result:
                    results.extend(result)
            return results
        except Exception:
            logger.exception("Error while searching for company: %s", query)
            raise
