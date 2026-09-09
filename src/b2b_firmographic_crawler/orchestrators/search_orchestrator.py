import os
from typing import List, Optional

from b2b_firmographic_crawler.base.searcher import CompanySearcher
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig, IQuery
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.storage.persistent_disk_cache import DiskCache
from b2b_firmographic_crawler.utils.general_utils import GeneralUtils

logger = get_logger("Search Orchestrator")


class CompanySearchingService:
    """Source-agnostic service for searching companies by name.

    Each source provides its own CompanySearcher implementation,
    making this service fully source-agnostic.
    """

    def __init__(
        self,
        searcher: CompanySearcher,
        source_name: str,
        cache_dir: Optional[str] = None,
    ):
        """Wire a source's searcher to an ISearchResponse cache.

        Args:
            searcher: Source-specific company lookup.
            source_name: Cache-key namespace, e.g. ``"craft"``. Search
                results are stored under ``"<source_name>:<company_name>"``
                so identical queries issued to different sources never
                share (and cross-serve) cache entries.
            cache_dir: Base dir for the ``ISearchResponse`` disk cache;
                defaults to the current working directory.
        """
        self.searcher = searcher
        self.source_name = (source_name or "").strip().lower() or "unknown"
        self._disk_cache = DiskCache(
            ISearchResponse, cache_dir or os.getcwd()
        )  # intentionally kept away from user control

    def search_company(
        self, query: IQuery, config: Optional[ICrawlerConfig] = None
    ) -> List[ISearchResponse]:
        """Search by company name with caching.

        Only ``query.company_name`` is honored today — a query without
        it yields ``[]`` (stock-ticker search is not implemented by any
        source yet). Fresh searches are cached under the source-namespaced
        key ``"<source_name>:<company_name>"`` with a TTL from
        ``search_cache_expiry_time_days``; ``force_rescrape`` bypasses
        the cache.

        Args:
            query: Search request (name and/or ticker).
            config: Crawl settings; defaults are used when omitted.

        Returns:
            Suggestion list (possibly empty).

        Raises:
            Exception: Search failures after logging.
        """
        crawler_config = config or ICrawlerConfig()
        results: list[ISearchResponse] = []

        try:
            if query.company_name:
                # Namespaced per source so two sources queried with the
                # same company name never serve each other's results.
                cache_key = f"{self.source_name}:{query.company_name}"
                if not crawler_config.force_rescrape:
                    result = self._disk_cache.get(
                        cache_key,
                    )
                    if result:
                        return result

                result = self.searcher.search_by_name(
                    query.company_name, crawler_config
                )
                self._disk_cache.set(
                    cache_key,
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
