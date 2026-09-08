import json
from typing import Dict


class CraftScrapingUtils:
    """Craft.co specific scraping utilities."""

    @staticmethod
    def get_search_query_url() -> str:
        return "https://craft.co/graphql"

    @staticmethod
    def prepare_search_query_headers() -> Dict[str, str]:
        headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://craft.co",
            "priority": "u=1, i",
            "referer": "https://craft.co/amazon",
            "sec-ch-ua": '"Not=A?Brand";v="99", "Brave";v="151", "Chromium";v="151"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        return headers

    @staticmethod
    def prepare_search_query_payload(query: str) -> str:
        return json.dumps(
            {
                "operationName": "UniversalSearch",
                "variables": {"query": query},
                "query": "query UniversalSearch($query: String\u0021) { universalSearch(query: $query) { ...UniversalSearchResult __typename }}fragment UniversalSearchResult on SearchSuggestion { company { ...CompanyWithLogo __typename } name type url __typename}fragment CompanyWithLogo on Company { id slug displayName logo { id url __typename } __typename}",
            }
        )

    @staticmethod
    def build_craft_page_url(query: str = "google") -> str:
        return f"https://craft.co/{query}"