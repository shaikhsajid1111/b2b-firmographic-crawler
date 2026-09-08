from abc import ABC, abstractmethod
from typing import Any, Dict, List

from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse


class SearchResponseParser(ABC):
    @abstractmethod
    def parse(self, data: Dict[Any, Any]) -> List[ISearchResponse]:
        pass
