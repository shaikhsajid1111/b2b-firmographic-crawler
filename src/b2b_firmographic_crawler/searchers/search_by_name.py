from typing import List, Optional

from b2b_firmographic_crawler.base.searcher import CompanySearcher
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse


class CompanySearchByName(CompanySearcher):

    def search_by_name(
        self, name: str, config: Optional[ICrawlerConfig] = None
    ) -> List[ISearchResponse]:
        response = self.searcher.scrape(name, config)
        return self.search_response_parser.parse(response)

    def search_by_symbol(
        self, symbol: str, config: Optional[ICrawlerConfig] = None
    ) -> List[ISearchResponse]:
        raise NotImplementedError("Search by stock symbol is not implemented yet.")
