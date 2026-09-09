import json
import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from curl_cffi import requests

from b2b_firmographic_crawler.base.scraper import UrlScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.sources.owler.utils import OwlerScrapingUtils

logger = get_logger(__name__)


class OwlerHttpUrlScraper(UrlScraper):
    """HTTP URL scraper for owler.com pages.

    Extracts JSON data from <script id="__NEXT_DATA__" type="application/json"> tag.

    Owler (Next.js) embeds its initial state in a script tag:
    <script id="__NEXT_DATA__" type="application/json">{"props":{"initialState":{...}}}</script>
    """

    def build_proxies(self, proxy: Optional[str]) -> Any:
        if not proxy:
            return None
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    def _build_soup(self, html_markup: str) -> BeautifulSoup:
        return BeautifulSoup(html_markup, "html.parser")

    def _extract_next_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract data from the __NEXT_DATA__ script tag.

        Next.js embeds its initial state in a script tag like:
        <script id="__NEXT_DATA__" type="application/json">{"props":{...}}</script>
        """
        # Find the script tag with id="__NEXT_DATA__"
        script_tag = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
        
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                # Navigate to props.initialState
                if isinstance(data, dict):
                    props = data.get("props", {})
                    initial_state = props.get("initialState")
                    if initial_state is not None:
                        logger.debug("Successfully extracted __NEXT_DATA__ props.initialState")
                        return initial_state
            except json.JSONDecodeError as ex:
                logger.debug("Failed to parse __NEXT_DATA__ JSON: %s", ex)

        return None

    def scrape(self, url: str, config: Optional[ICrawlerConfig] = None) -> str:
        try:
            logger.info("Starting HTTP crawl: %s", url)
            headers = OwlerScrapingUtils.prepare_page_headers()
            proxy: Optional[str] = config.proxy if config else None
            proxies = self.build_proxies(proxy) if config else None
            response = requests.get(
                url,
                headers=headers,
                impersonate="chrome",
                proxies=proxies,
                timeout=config.request_timeout if config else 30.0,
            )

            response.raise_for_status()
            soup = self._build_soup(response.text)

            # Extract NEXT_DATA from script tag
            next_data = self._extract_next_data(soup)

            if not next_data:
                logger.warning(
                    "No __NEXT_DATA__ script tag found in HTTP response for %s. "
                    "This may be because the data is loaded dynamically via JavaScript. "
                    "Consider using SeleniumBaseUrlScraper instead.",
                    url,
                )
                raise ValueError(
                    "No __NEXT_DATA__ script tag found in response. "
                    "The target website may load data dynamically. "
                    "Use SeleniumBaseUrlScraper for full JavaScript support."
                )

            logger.info("Successfully extracted __NEXT_DATA__ from %s", url)
            return json.dumps(next_data)

        except Exception as ex:
            logger.exception(f"Error while scraping company URL with HTTP: {ex}")
            raise
