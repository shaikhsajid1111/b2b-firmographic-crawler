"""Owler parsers: page + search-response parsing."""

from b2b_firmographic_crawler.sources.owler.parser.company_page_parser import (
    OwlerParser,
)
from b2b_firmographic_crawler.sources.owler.parser.search_result_parser import (
    OwlerSearchParser,
)

__all__ = ["OwlerParser", "OwlerSearchParser"]
