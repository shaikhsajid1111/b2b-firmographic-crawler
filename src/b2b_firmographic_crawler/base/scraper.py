from abc import ABC, abstractmethod
from typing import Dict, Optional

from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig


class UrlScraper(ABC):
    @abstractmethod
    def build_proxies(self, proxy: Optional[str]) -> Optional[Dict]:
        pass

    @abstractmethod
    def scrape(self, url: str, config: Optional[ICrawlerConfig] = None) -> str:
        pass


class CompanyNameScraper(ABC):
    @abstractmethod
    def scrape(self, query: str, config: Optional[ICrawlerConfig] = None) -> str:
        pass
