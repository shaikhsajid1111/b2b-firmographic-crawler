import json
from typing import Dict


class OwlerScrapingUtils:

    @staticmethod
    def prepare_search_query_headers() -> Dict[str, str]:
        headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.9",
            "priority": "u=1, i",
            "referer": "https://www.owler.com/company/google",
            "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Brave";v="152"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Linux",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        }

        return headers

    @staticmethod
    def get_search_query_url(company_name: str):
        return f"https://www.owler.com/a/v1/pb/basicSearchInternal?searchTerm={company_name}"
