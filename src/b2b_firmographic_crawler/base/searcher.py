from abc import ABC, abstractmethod
from typing import List, Optional

from b2b_firmographic_crawler.base.scraper import CompanyNameScraper
from b2b_firmographic_crawler.base.search_parser import SearchResponseParser
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse


class CompanySearcher(ABC):
    def __init__(
        self, searcher: CompanyNameScraper, search_response_parser: SearchResponseParser
    ):
        self.searcher = searcher
        self.search_response_parser = search_response_parser

    @abstractmethod
    def search_by_name(
        self, name: str, config: Optional[ICrawlerConfig] = None
    ) -> List[ISearchResponse]:
        pass

    @abstractmethod
    def search_by_symbol(
        self, symbol: str, config: Optional[ICrawlerConfig] = None
    ) -> List[ISearchResponse]:
        pass
