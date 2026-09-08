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


class OwlerHttpUrlScraper(UrlScraper):
    """HTTP URL scraper for owler.com pages.

    Extracts window.__NEXT_DATA__.props.initialState from script tags.
    """

    def build_proxies(self, proxy: Optional[str]) -> Any:
        if not proxy:
            return None
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    def _build_soup(self, html_markup: str) -> BeautifulSoup:
        return BeautifulSoup(html_markup, "html.parser")

    def _extract_next_data_from_scripts(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract window.__NEXT_DATA__.props.initialState from script tags.

        Owler (Next.js) embeds its initial state in a script tag as
        window.__NEXT_DATA__ = {..., props: {initialState: {...}}}
        """
        scripts = soup.find_all("script")

        for script in scripts:
            if not script.string:
                continue

            script_content = script.string

            # Look for window.__NEXT_DATA__ assignment
            pattern = r"window\.__NEXT_DATA__\s*=\s*"
            match = re.search(pattern, script_content)
            if not match:
                continue

            try:
                json_source = re.sub(
                    r"(?<=:)\s*undefined\b", "null", script_content[match.end() :]
                )
                value, _ = json.JSONDecoder().raw_decode(json_source)
            except json.JSONDecodeError as ex:
                logger.debug("Failed to parse __NEXT_DATA__ JSON: %s", ex)
                continue

            # Navigate to props.initialState
            if isinstance(value, dict):
                props = value.get("props", {})
                initial_state = props.get("initialState")
                if initial_state is not None:
                    logger.debug("Successfully extracted __NEXT_DATA__.props.initialState")
                    return initial_state

        return None

    def scrape(self, url: str, config: Optional[ICrawlerConfig] = None) -> str:
        try:
            logger.info("Starting HTTP crawl: %s", url)
            headers = ScrapingUtils.prepare_default_headers()
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

            # Extract NEXT_DATA from script tags
            next_data = self._extract_next_data_from_scripts(soup)

            if not next_data:
                logger.warning(
                    "No window.__NEXT_DATA__ data found in HTTP response for %s. "
                    "This may be because the data is loaded dynamically via JavaScript. "
                    "Consider using SeleniumBaseUrlScraper instead.",
                    url,
                )
                raise ValueError(
                    "No window.__NEXT_DATA__ data found in response. "
                    "The target website may load data dynamically. "
                    "Use SeleniumBaseUrlScraper for full JavaScript support."
                )

            logger.info("Successfully extracted __NEXT_DATA__ from %s", url)
            return json.dumps(next_data)

        except Exception as ex:
            logger.exception(f"Error while scraping company URL with HTTP: {ex}")
            raise
