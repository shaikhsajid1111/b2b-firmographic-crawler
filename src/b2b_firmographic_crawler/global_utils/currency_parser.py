from typing import Optional, TypedDict

from babel import Locale
from babel.numbers import get_currency_symbol
from price_parser import Price


class IAmountData(TypedDict):
    amount: Optional[float]
    currency: Optional[str]


class CurrencyParser:
    @staticmethod
    def parse_amount_and_currency(string: str) -> IAmountData:
        price = Price.fromstring(string)
        currency_symbol = price.currency
        currency_code = CurrencyParser.get_codes_by_symbol(currency_symbol)
        parsed_data = IAmountData(
            amount=price.amount_float,
            currency=currency_code[0] if currency_code else currency_symbol,
        )
        return parsed_data

    @staticmethod
    def get_codes_by_symbol(symbol: Optional[str], locale_str: str = "en") -> list:
        if not symbol:
            return []
        search_symbol = symbol.strip()
        locale = Locale.parse(locale_str)
        matched_codes = []

        # Iterate through all standard currency codes in the locale
        for code in locale.currencies.keys():
            # Get the preferred symbol for each code
            if get_currency_symbol(code, locale=locale) == search_symbol:
                matched_codes.append(code)

        return sorted(list(set(matched_codes)))
