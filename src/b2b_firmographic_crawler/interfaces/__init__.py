"""Convenience re-exports of the config/query/response models."""

from b2b_firmographic_crawler.interfaces.iconfig import (
    ICrawlerConfig,
    IQuery,
    IDatabaseConfig,
)
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse

__all__ = [
    "ICrawlerConfig",
    "IQuery",
    "IDatabaseConfig",
    "ISearchResponse",
]
