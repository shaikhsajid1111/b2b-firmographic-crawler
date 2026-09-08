import argparse
import json
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from seleniumbase import Driver

from b2b_firmographic_crawler.base.scraper import CompanyNameScraper
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig
from b2b_firmographic_crawler.logger import get_logger
from b2b_firmographic_crawler.utils.scraping_utils import ScrapingUtils

logger = get_logger(__name__)


class SeleniumbaseSearchCrawler(CompanyNameScraper):
    def __init__(self, *, headless: bool = False, page_load_timeout: int = 30) -> None:
        self.headless = headless
        self.page_load_timeout = page_load_timeout

    def _build_driver_options(
        self, config: Optional[ICrawlerConfig]
    ) -> dict[str, object]:
        driver_options: dict[str, object] = {
            "uc": config.uc if config is not None else True,
            "headless": self.headless
            or (config.headless if config is not None else False),
            "log_cdp_events": True,
        }
        if config is not None and config.proxy:
            driver_options["proxy"] = config.proxy
        return driver_options

    @staticmethod
    def _graphql_response_body(driver, timeout: float) -> str:
        graphql_url = ScrapingUtils.get_search_query_url()
        response_ids: set[str] = set()
        response_urls: dict[str, str] = {}

        def find_response_body(_driver):
            for entry in _driver.get_log("performance"):
                message = json.loads(entry["message"])["message"]
                method = message["method"]
                params = message.get("params", {})

                if method == "Network.responseReceived":
                    response = params["response"]
                    if response["url"] == graphql_url:
                        request_id = params["requestId"]
                        response_ids.add(request_id)
                        response_urls[request_id] = response["url"]
                elif (
                    method == "Network.loadingFinished"
                    and params["requestId"] in response_ids
                ):
                    request_id = params["requestId"]
                    body = _driver.execute_cdp_cmd(
                        "Network.getResponseBody", {"requestId": request_id}
                    )
                    if response_urls.pop(request_id, None) == graphql_url:
                        return body["body"]
            return False

        response_body = WebDriverWait(driver, timeout).until(find_response_body)
        return str(response_body)

    def scrape(
        self, query: str, config: Optional[ICrawlerConfig] = None
    ) -> str:
        url = ScrapingUtils.build_craft_page_url()
        logger.info("Starting crawl: %s", url)
        request_timeout = (
            config.request_timeout if config is not None else self.page_load_timeout
        )

        driver = Driver(**self._build_driver_options(config))
        try:
            driver.set_page_load_timeout(request_timeout)
            driver.get(url)
            WebDriverWait(driver, request_timeout).until(
                lambda current_driver: current_driver.execute_script(
                    "return document.readyState"
                )
                == "complete"
            )
            driver.get_log("performance")
            search_box = driver.find_element(By.CSS_SELECTOR, "input[type=search]")
            ScrapingUtils.enter_keys_to_element(search_box, query)
            response_body = self._graphql_response_body(driver, request_timeout)
            logger.info("Captured Craft GraphQL response for query: %s", query)
            data = json.loads(response_body)
            if not isinstance(data, list) or not data:
                return json.dumps({"data": {"universalSearch": []}})
            return json.dumps(data[0])
        except Exception as ex:
            logger.exception(
                f"Error while scraping company name using seleniumbase: {ex}"
            )
            raise
        finally:
            driver.quit()


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Fetch a Craft company name with SeleniumBase UC mode."
    )
    argument_parser.add_argument("query", help="The company name to search for")
    argument_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome without opening a visible browser window",
    )
    arguments = argument_parser.parse_args()

    response = SeleniumbaseSearchCrawler(headless=arguments.headless).scrape(
        arguments.query, None
    )
    print(response)


if __name__ == "__main__":
    main()
