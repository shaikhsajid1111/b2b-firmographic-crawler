"""Offline test suite for b2b-firmographic-crawler.

Run with:

    uv run python test.py

No network access or browser is required: every crawler is replaced with an
in-memory fake, so the tests exercise the whole pipeline deterministically
(search -> parse -> scrape -> cache -> source-registry string dispatch).
"""

import json
import tempfile
import time
import traceback

from b2b_firmographic_crawler import (
    B2BFirmographicCrawler,
    CompanyData,
    ICrawlerConfig,
    ISearchResponse,
    SourceProvider,
    SourceRegistry,
    register_source,
)
from b2b_firmographic_crawler.base.scraper import CompanyNameScraper, UrlScraper
from b2b_firmographic_crawler.sources.craft.parsers.company_page_parser import (
    CraftParser,
)
from b2b_firmographic_crawler.sources.craft.parsers.search_result_parser import (
    CraftSearchParser,
)
from b2b_firmographic_crawler.sources.craft.provider import CraftSource
from b2b_firmographic_crawler.storage.persistent_disk_cache import DiskCache

# --------------------------------------------------------------------------
# Fakes: canned Craft responses + scrapers that never touch the network.
# --------------------------------------------------------------------------

CRAFT_SEARCH_RESPONSE = json.dumps(
    {
        "data": {
            "universalSearch": [
                {
                    "company": {
                        "displayName": "Stripe",
                        "slug": "stripe",
                        "logo": {"url": "https://logo.example.com/stripe.png"},
                        "__typename": "Company",
                    },
                    "__typename": "SearchSuggestion",
                },
                {
                    "company": {
                        "displayName": "Stripe Atlas",
                        "slug": "stripe-atlas",
                        "logo": None,
                        "__typename": "Company",
                    },
                    "__typename": "SearchSuggestion",
                },
            ]
        }
    }
)

CRAFT_COMPANY_CACHE = json.dumps(
    {
        "Company:123": {
            "displayName": "TestCo",
            "homepage": "https://test.example.com",
            "foundedYear": 2001,
            "status": "Operating",
            "tags": [{"id": "tag1", "typename": "Tag"}],
            "employees": [{"id": "emp1", "typename": "EmployeeNumber"}],
            "locations": [{"id": "loc1", "typename": "Location"}],
            "totalFunding": {"id": "fund1"},
            "keyExecutives": [{"id": "kex1", "typename": "KeyExecutive"}],
            "competitors": [{"id": "Company:999", "typename": "Company"}],
            "incomeStatements": [{"id": "inc1"}],
            "operatingMetrics": [{"id": "om1", "typename": "OperatingMetric"}],
        },
        "tag1": {"name": "Software"},
        "emp1": {"employeeNumber": 1234, "date": "2024-01-15"},
        "loc1": {
            "city": "SF",
            "countryName": "USA",
            "countryCode": "US",
            "address": "1 Main St",
            "hq": True,
            "__typename": "Location",
        },
        "fund1": {"value": 12000000, "currencySymbol": "$"},
        "kex1": {"name": "Jane Doe", "title": "CEO"},
        "Company:999": {
            "displayName": "RivalCo",
            "tags": [{"id": "tag1", "typename": "Tag"}],
        },
        "inc1": {"revenue": 500.5, "currencyIsoCode": "USD", "period": {"id": "p1"}},
        "p1": {"displayEndDate": "2023-12-31", "periodType": "FY"},
        "om1": {
            "companySpecificKpi": "MAU",
            "unitType": "users",
            "period": {"id": "p1"},
            "value": {"id": "v1", "typename": "Money"},
        },
        "v1": {"value": 99.5},
    }
)


class FakeCraftSearchScraper(CompanyNameScraper):
    """Returns a canned Craft GraphQL search response (no network)."""

    def __init__(self) -> None:
        self.calls = []

    def scrape(self, query, config=None) -> str:
        self.calls.append(query)
        return CRAFT_SEARCH_RESPONSE


class FakeCraftUrlScraper(UrlScraper):
    """Returns a canned Craft window.App.cache payload (no network)."""

    def __init__(self) -> None:
        self.calls = []

    def build_proxies(self, proxy):
        return None

    def scrape(self, url, config=None) -> str:
        self.calls.append(url)
        return CRAFT_COMPANY_CACHE


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


def test_company_data_defaults():
    """Adjusted CompanyData: fresh per-instance timestamps, sane defaults."""
    a = CompanyData(company_name="A")
    time.sleep(0.01)
    b = CompanyData(company_name="B")
    assert (
        a.last_scraped_at != b.last_scraped_at
    ), "last_scraped_at must be per-instance"
    assert a.company_status.status.value == "unknown"
    assert a.company_founded_year is None
    assert a.company_industries == []
    assert a.company_funding_info == []
    assert a.company_locations == []


def test_craft_parser_parses_full_payload():
    """CraftParser maps the raw window.App.cache payload onto CompanyData."""
    company = CraftParser().parse(CRAFT_COMPANY_CACHE)
    assert company.company_name == "TestCo"
    assert company.company_domain == "example.com"  # tldextract strips subdomain
    assert company.company_industries == ["software"]
    assert company.company_founded_year == 2001
    assert company.company_employee_counts[0].total_employees == 1234
    assert company.company_locations[0].city == "SF"
    assert company.company_locations[0].is_headquarter is True
    assert company.company_funding_info[0].funding_amount == 12000000
    assert company.company_funding_info[0].funding_currency == "USD"
    assert company.key_executives[0].name == "Jane Doe"
    assert company.similar_companies[0].company_name == "RivalCo"
    assert company.company_income_statements[0].revenue == 500.5
    assert company.company_operating_metrics[0].metric_value == 99.5
    assert (
        company.company_status.status.value == "unknown"
    )  # "Operating" has no keyword match


def test_disk_cache_round_trip():
    """Parsed CompanyData survives a persist -> load cycle."""
    company = CraftParser().parse(CRAFT_COMPANY_CACHE)
    with tempfile.TemporaryDirectory() as tmp:
        cache = DiskCache(CompanyData, tmp)
        cache.set("stripe", company, expiry_time=9999999999)
        loaded = cache.get("stripe")
        assert loaded.company_name == "TestCo"
        assert loaded.company_locations[0].is_headquarter is True
        cache.delete("stripe")
        assert cache.get("stripe") is None


def test_craft_search_flow_with_fake_scraper():
    """Search: fake scraper -> CraftSearchParser -> ISearchResponse + caching."""
    fake = FakeCraftSearchScraper()
    with tempfile.TemporaryDirectory() as tmp:
        source = CraftSource(cache_dir=tmp, searcher=fake)
        results = source.search_company("stripe", ICrawlerConfig(force_rescrape=True))
        assert len(results) == 2
        assert isinstance(results[0], ISearchResponse)
        assert results[0].company_name == "Stripe"
        assert results[0].source_url == "https://craft.co/stripe"
        assert results[1].slug == "stripe-atlas"
        assert fake.calls == ["stripe"]

        # Second call (no force_rescrape) is served from the disk cache.
        cached = source.search_company("stripe")
        assert [r.slug for r in cached] == ["stripe", "stripe-atlas"]
        assert fake.calls == ["stripe"], "second search must be cached"

        # force_rescrape bypasses the cache.
        source.search_company("stripe", ICrawlerConfig(force_rescrape=True))
        assert fake.calls == ["stripe", "stripe"]


def test_craft_scrape_flow_with_fake_scraper():
    """Scrape: fake scraper -> CraftParser -> CompanyData + caching."""
    fake = FakeCraftUrlScraper()
    with tempfile.TemporaryDirectory() as tmp:
        source = CraftSource(cache_dir=tmp, url_scraper=fake)
        company = source.get_company_data(
            "https://craft.co/stripe", ICrawlerConfig(force_rescrape=True)
        )
        assert company.company_name == "TestCo"
        assert fake.calls == ["https://craft.co/stripe"]

        # Second call is served from the disk cache -> no extra scrape.
        cached = source.get_company_data("https://craft.co/stripe")
        assert cached.company_name == "TestCo"
        assert fake.calls == ["https://craft.co/stripe"]

        # force_rescrape bypasses the cache.
        source.get_company_data(
            "https://craft.co/stripe", ICrawlerConfig(force_rescrape=True)
        )
        assert fake.calls == ["https://craft.co/stripe"] * 2


def test_registry_rejects_unknown_source():
    """Unknown source strings fail with a helpful message."""
    try:
        SourceRegistry.create("does-not-exist")
    except ValueError as ex:
        assert "does-not-exist" in str(ex)
        assert "craft" in str(ex)  # lists available sources
    else:
        raise AssertionError("SourceRegistry.create should reject unknown sources")

    assert "craft" in SourceRegistry.available_sources()


def test_custom_source_string_dispatch():
    """Prove pluggability: register a mock 'owler' source, select it by string.

    This is exactly how a real Owler/Crunchbase source plugs in: implement
    SourceProvider, register it with a string, and the facade accepts it.
    """

    if "owler_mock" not in SourceRegistry.available_sources():

        @register_source("owler_mock")
        class OwlerMockSource(SourceProvider):
            """Mock Owler: reuses Craft parsers with canned payloads."""

            def __init__(self, cache_dir=None, **kwargs) -> None:
                self.cache_dir = cache_dir

            def search_company(self, query, config=None):
                return CraftSearchParser().parse(CRAFT_SEARCH_RESPONSE)

            def get_company_data(self, url, config=None):
                return CraftParser().parse(CRAFT_COMPANY_CACHE)

    crawler = B2BFirmographicCrawler(cache_dir=tempfile.mkdtemp())
    assert "craft" in crawler.available_sources()
    assert "owler_mock" in crawler.available_sources()

    # Search + scrape on the custom source, purely via string dispatch.
    results = crawler.search_company("stripe", source="owler_mock")
    assert results[0].company_name == "Stripe"

    company = crawler.get_company_data(
        "https://owler.example.com/stripe", source="owler_mock"
    )
    assert company.company_name == "TestCo"

    # End-to-end: search by name then scrape the first result.
    by_name = crawler.get_company_data_by_name("stripe", source="owler_mock")
    assert by_name.company_name == "TestCo"

    # A source that is not registered yet is rejected by the facade too.
    try:
        crawler.get_company_data("https://x.example.com", source="crunchbase")
    except ValueError as ex:
        assert "crunchbase" in str(ex)
    else:
        raise AssertionError("crunchbase should not be registered yet")


def test_facade_provider_caching_and_case_insensitivity():
    """Providers are created once per source; source names are case-insensitive."""
    crawler = B2BFirmographicCrawler(cache_dir=tempfile.mkdtemp())
    provider = crawler._get_provider("craft")
    assert isinstance(provider, CraftSource)
    assert crawler._get_provider("craft") is provider
    assert crawler._get_provider("CRAFT") is provider  # normalized


def main() -> None:
    tests = [
        test_company_data_defaults,
        test_craft_parser_parses_full_payload,
        test_disk_cache_round_trip,
        test_craft_search_flow_with_fake_scraper,
        test_craft_scrape_flow_with_fake_scraper,
        test_registry_rejects_unknown_source,
        test_custom_source_string_dispatch,
        test_facade_provider_caching_and_case_insensitivity,
    ]

    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception:
            failures += 1
            print(f"FAIL  {test.__name__}")
            traceback.print_exc()

    print()
    if failures:
        print(f"{failures}/{len(tests)} test(s) FAILED")
        raise SystemExit(1)
    print(f"All {len(tests)} tests passed")


if __name__ == "__main__":
    main()
