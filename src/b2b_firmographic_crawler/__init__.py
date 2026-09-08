"""b2b-firmographic-crawler.

A web crawler package that searches companies and extracts firmographic
data (funding, employees, locations, executives, financials, ...) into a
validated :class:`b2b_firmographic_crawler.CompanyData` model.

Sources are pluggable: pass a plain string (e.g. ``source="craft"``) to the
crawler, and register new sources (owler, crunchbase, ...) with
``@SourceRegistry.register("name")``.
"""

from typing import List, Optional

from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig, IQuery
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse
from b2b_firmographic_crawler.models.company_data import CompanyData
from b2b_firmographic_crawler.sources.base import SourceProvider
from b2b_firmographic_crawler.sources.craft_source import CraftSource
from b2b_firmographic_crawler.sources.registry import SourceRegistry

__version__ = "1.0.0"

__all__ = [
    "B2BFirmographicCrawler",
    "CompanyData",
    "IQuery",
    "ICrawlerConfig",
    "ISearchResponse",
    "SourceProvider",
    "SourceRegistry",
    "register_source",
]


def register_source(name: str):
    """Decorator alias for registering a new data source by string name."""
    return SourceRegistry.register(name)


class B2BFirmographicCrawler:
    """High-level facade for company search and firmographic data scraping.

    The data source is selected with a plain string, e.g.::

        crawler = B2BFirmographicCrawler()

        results = crawler.search_company("stripe", source="craft")
        data = crawler.get_company_data(results[0].source_url, source="craft")

    New sources (owler, crunchbase, ...) are added by subclassing
    :class:`SourceProvider` and registering them::

        @register_source("owler")
        class OwlerSource(SourceProvider):
            ...

    after which ``source="owler"`` works everywhere.
    """

    def __init__(
        self,
        config: Optional[ICrawlerConfig] = None,
        cache_dir: Optional[str] = None,
    ) -> None:
        self.config = config or ICrawlerConfig()
        self.cache_dir = cache_dir
        self._providers = {}

    def _get_provider(self, source: str) -> SourceProvider:
        """Instantiate (and cache) the provider for the given source string."""
        key = (source or "").strip().lower()
        if key not in self._providers:
            self._providers[key] = SourceRegistry.create(
                key, cache_dir=self.cache_dir
            )
        return self._providers[key]

    def available_sources(self) -> List[str]:
        """Names of all registered data sources."""
        return SourceRegistry.available_sources()

    def search_company(
        self,
        query: str,
        source: str = "craft",
        config: Optional[ICrawlerConfig] = None,
    ) -> List[ISearchResponse]:
        """Search companies by name on the given source."""
        return self._get_provider(source).search_company(query, config or self.config)

    def get_company_data(
        self,
        url: str,
        source: str = "craft",
        config: Optional[ICrawlerConfig] = None,
    ) -> Optional[CompanyData]:
        """Scrape a company page URL on the given source."""
        return self._get_provider(source).get_company_data(url, config or self.config)

    def get_company_data_by_name(
        self,
        name: str,
        source: str = "craft",
        config: Optional[ICrawlerConfig] = None,
    ) -> Optional[CompanyData]:
        """Search a company by name, then scrape the first matching page."""
        results = self.search_company(name, source, config)
        if not results:
            return None
        return self.get_company_data(results[0].source_url, source, config)
