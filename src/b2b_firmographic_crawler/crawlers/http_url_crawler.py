import json
import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from curl_cffi import requests

from b2b_firmographic_crawler.base.scraper import UrlScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.utils.scraping_utils import ScrapingUtils

logger = get_logger(__name__)


class HTTPUrlScraper(UrlScraper):

    def build_proxies(self, proxy: Optional[str]) -> Any:
        if not proxy:
            return None
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    def _build_soup(self, html_markup: str) -> BeautifulSoup:
        return BeautifulSoup(html_markup, "html.parser")

    def _extract_cache_from_scripts(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract window.App.cache data from JSON assigned in script tags.
        """
        scripts = soup.find_all("script")

        for script in scripts:
            if not script.string:
                continue

            script_content = script.string

            assignments = (
                (r"window\.App\.cache\s*=\s*", False),
                (r"window\.App\s*=\s*", True),
            )
            for pattern, contains_cache in assignments:
                match = re.search(pattern, script_content)
                if not match:
                    continue

                try:
                    json_source = re.sub(
                        r"(?<=:)\s*undefined\b", "null", script_content[match.end():]
                    )
                    value, _ = json.JSONDecoder().raw_decode(json_source)
                except json.JSONDecodeError as ex:
                    logger.debug("Failed to parse %s JSON: %s", pattern, ex)
                    continue

                if contains_cache and isinstance(value, dict):
                    value = value.get("cache")
                if value is not None:
                    logger.debug("Successfully extracted cache using: %s", pattern)
                    return value
        return None

    def scrape(self, url: str, config: Optional[ICrawlerConfig] = None) -> str:
        try:
            logger.info("Starting HTTP crawl: %s", url)
            headers = ScrapingUtils.prepare_search_query_headers()
            proxy: Optional[str] = config.proxy if config else None
            proxies = self.build_proxies(proxy) if config else None
            response = requests.request(
                "GET",
                url,
                headers=headers,
                impersonate="chrome",
                proxies=proxies,
                timeout=config.request_timeout if config else 30.0,
            )

            response.raise_for_status()
            soup = self._build_soup(response.text)

            # Extract cache data from script tags
            cache_data = self._extract_cache_from_scripts(soup)

            if not cache_data:
                logger.warning(
                    "No window.App.cache data found in HTTP response for %s. "
                    "This may be because the data is loaded dynamically via JavaScript. "
                    "Consider using SeleniumBaseUrlScraper instead.",
                    url,
                )
                raise ValueError(
                    "No window.App.cache data found in response. "
                    "The target website may load data dynamically. "
                    "Use SeleniumBaseUrlScraper for full JavaScript support."
                )

            logger.info("Successfully extracted cache data from %s", url)
            return json.dumps(cache_data)

        except Exception as ex:
            logger.exception(f"Error while scraping company URL with HTTP: {ex}")
            raise
