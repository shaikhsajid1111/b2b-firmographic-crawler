import re
from typing import Any, Dict, Optional
from b2b_firmographic_crawler.models.company_data import CompanyStatus
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse
from fake_headers import Headers


class GeneralUtils:
    @staticmethod
    def search_data_by_key(data: Dict[str, Any], key_pattern: str) -> Optional[Dict[str, Any]]:
        """
        Returns first matching key-value pair in the data dictionary based on the provided regex pattern.
        """
        for key, value in data.items():
            if re.match(key_pattern, key):
                return value
        return None

    @staticmethod
    def handle_current_status(current_str: str) -> CompanyStatus:
        # match with regex to find the status in the string
        # find the closest active match to the status in the string
        status_match = re.search(
            r"(active|inactive|acquired|bankrupt|closed|unknown)",
            current_str,
            re.IGNORECASE,
        )
        if status_match:
            status_str = status_match.group(1).lower()
            if status_str == "active":
                return CompanyStatus.ACTIVE
            elif status_str == "inactive":
                return CompanyStatus.INACTIVE
            elif status_str == "acquired":
                return CompanyStatus.ACQUIRED
            elif status_str == "bankrupt":
                return CompanyStatus.BANKRUPT
            elif status_str == "closed":
                return CompanyStatus.CLOSED
        return CompanyStatus.UNKNOWN

    @staticmethod
    def get_current_date() -> datetime:
        return datetime.now(tz=timezone.utc)

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        return parse(date_str)

    @staticmethod
    def generate_time_from_now(days: int) -> datetime:
        current_date = datetime.now(tz=timezone.utc)
        n_days_ahead_time = current_date + timedelta(days=days)
        return n_days_ahead_time

    @staticmethod
    def get_random_user_agent() -> str:
        """Generates a fresh random User-Agent string."""
        return Headers(headers=False).generate().get("User-Agent", "")
