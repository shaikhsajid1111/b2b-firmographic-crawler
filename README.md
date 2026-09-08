# b2b-firmographic-crawler

**A pluggable Python web crawler that turns public company pages into clean, validated firmographic data.**

[![Python versions](https://img.shields.io/badge/python-3.10+-blue.svg)](https://pypi.org/project/b2b-firmographic-crawler/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Beta-blue)](https://pypi.org/project/b2b-firmographic-crawler/)

b2b-firmographic-crawler searches for companies on supported data sources (Craft.co today, Owler and Crunchbase pluggable), scrapes their public company pages, and returns the result as a fully typed, validated `CompanyData` model — funding rounds, employee counts, office locations, key executives, industries, income statements and more.

## Disclaimer & privacy

> **⚠️ This project is just code — the person using it is solely responsible for every action taken with it.**

- b2b-firmographic-crawler accesses **only publicly available, unauthenticated web pages**. It does not log in anywhere, does not ask for or use credentials, and does not access, collect, or process any private, personal, or authenticated data. Anything behind logins, paywalls, or API keys is out of scope **by design**.
- The software is provided **"AS IS", WITHOUT WARRANTY OF ANY KIND** (see the [MIT license](LICENSE)). The authors and contributors are **not liable** for any claim, damages, or other liability arising from its use or misuse — including how you collect, store, process, share, resell, or publish any data obtained with it.
- **You** are solely responsible for making sure your use complies with all applicable laws and regulations — including copyright, data-protection and privacy laws (e.g. GDPR, CCPA), and computer-misuse laws — as well as each website's **terms of service**, **robots.txt**, and reasonable **rate limits**.
- Do not use this tool for spam, harassment, surveillance, profiling of individuals, discrimination, or any unlawful purpose. If a website owner signals (through their terms, robots directives, or otherwise) that they do not want their data collected, respect that.

## Features

- **Source-agnostic API** — choose a data source with a plain string: `source="craft"`
- **Typed & validated output** — every record is a [Pydantic](https://docs.pydantic.dev/) `CompanyData` model
- **Resilient scraping** — HTTP-first (`curl-cffi` browser impersonation) with an automatic SeleniumBase/UC browser fallback chain
- **Persistent caching** — resumable runs with configurable TTLs, per record type
- **Pluggable storage** — MongoDB and PostgreSQL stores included
- **Export-ready** — JSON, CSV and Parquet exporters
- **Extensible by design** — register your own source with a single decorator

## Table of Contents

- [Disclaimer & privacy](#disclaimer--privacy)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Sources](#sources)
- [Configuration](#configuration)
- [Caching](#caching)
- [Exporting data](#exporting-data)
- [Storing data](#storing-data)
- [The data model](#the-data-model)
- [Adding a new source](#adding-a-new-source)
- [Logging](#logging)
- [Testing](#testing)
- [Project structure](#project-structure)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Publishing](#publishing)
- [Contributing](#contributing)
- [License](#license)

## Installation

Requires **Python 3.10+**.

```bash
# with pip
pip install b2b-firmographic-crawler

# or with uv (recommended)
uv add b2b-firmographic-crawler
```

To also get the CSV/Parquet exporters (pandas + PyArrow):

```bash
pip install "b2b-firmographic-crawler[export]"
```

> [!NOTE]
> On the first run that needs the browser fallback, SeleniumBase downloads a Chrome
> binary automatically. Pure-HTTP scraping has no browser dependency.

## Quick start

```python
from b2b_firmographic_crawler import B2BFirmographicCrawler

crawler = B2BFirmographicCrawler(cache_dir="./cache")

# 1. Find a company by name
results = crawler.search_company("stripe", source="craft")
print(results[0].company_name)   # Stripe
print(results[0].source_url)     # https://craft.co/stripe

# 2. Scrape its public company page into a validated model
company = crawler.get_company_data(results[0].source_url, source="craft")

print(company.company_name)            # Stripe
print(company.company_domain)          # stripe.com
print(company.company_founded_year)    # 2010
print(company.company_funding_info)    # [CompanyFundingInfo(funding_amount=..., ...)]
print(company.company_locations)       # [CompanyLocation(city=..., is_headquarter=True), ...]
print(company.key_executives)          # [KeyExecutive(name=..., title=...), ...]
```

That's it — two calls produce a complete, typed firmographic record. Everything
below is optional configuration.

## Usage

### Searching for companies

`search_company()` returns a list of `ISearchResponse` suggestions — company
name, canonical page URL, slug and logo:

```python
results = crawler.search_company("airbnb", source="craft")

for result in results:
    print(result.company_name, "->", result.source_url)

first = results[0]
first.company_name   # 'Airbnb'
first.source_url     # 'https://craft.co/airbnb'
first.slug           # 'airbnb'
first.logo_url       # 'https://...'
```

If nothing matches, an empty list is returned.

### Scraping a company page

```python
company = crawler.get_company_data("https://craft.co/airbnb", source="craft")
```

Returns `CompanyData` (see [The data model](#the-data-model)), or `None` when
the page could not be parsed.

### Search + scrape in one call

```python
company = crawler.get_company_data_by_name("airbnb", source="craft")
```

### Working with results

`CompanyData` is a standard Pydantic model, so it composes with the rest of
your stack:

```python
company.model_dump(mode="json")        # plain dict (JSON-safe)
company.model_dump_json(indent=2)      # pretty JSON string
company.company_industries             # ['travel', 'hospitality', ...]

for executive in company.key_executives:
    print(executive.name, "-", executive.title)
```

## Sources

The data source is always a plain string. Names are case-insensitive and
surrounding whitespace is ignored.

| Source | Status | Notes |
| ------ | ------ | ----- |
| `craft` | Implemented | craft.co company search + firmographic pages |
| `owler` | Planned | see [Adding a new source](#adding-a-new-source) |
| `crunchbase` | Planned | see [Adding a new source](#adding-a-new-source) |

```python
crawler.available_sources()                        # ['craft'] + anything you register
crawler.search_company("stripe", source="CRAFT")   # case-insensitive
```

Calling an unregistered source raises a `ValueError` listing every available
source.

### How sources work

Each source is a **self-contained package** under `b2b_firmographic_crawler.sources.<name>`
that bundles its own crawlers and parsers:

- **Crawlers** (`sources/<name>/crawlers/`) — fetch pages and search results from the website
- **Parsers** (`sources/<name>/parsers/`) — extract structured `CompanyData` from raw pages
- **Provider** (`sources/<name>/provider.py`) — wires the crawlers/parsers into the generic orchestrators

All sources share the same:
- **Output model** — every source returns the same `CompanyData` schema
- **Orchestrators** — `CompanyPageScrapingService` and `CompanySearchingService` handle caching and coordination
- **Storage & exports** — MongoDB/PostgreSQL stores and JSON/CSV/Parquet exporters work with any source

This means adding a new source (like Owler) only requires implementing the website-specific
crawlers and parsers — the caching, exports and storage come for free.

## Configuration

### `ICrawlerConfig`

Pass a config to the crawler (applies to every call) or per call:

```python
from b2b_firmographic_crawler import ICrawlerConfig

config = ICrawlerConfig(
    proxy="user:pass@proxy-host:8080",   # HTTP proxy for scraping
    headless=True,                       # run the fallback browser headless
    request_timeout=45.0,                # seconds per request / page load
    company_cache_expiry_time_days=30,   # TTL for scraped company pages
    search_cache_expiry_time_days=7,     # TTL for search results
    force_rescrape=False,                # True = ignore the cache completely
)

crawler = B2BFirmographicCrawler(config=config, cache_dir="./cache")
# or one-off:
company = crawler.get_company_data(url, source="craft", config=config)
```

| Field | Type | Default | Description |
| ----- | ---- | ------- | ----------- |
| `request_timeout` | `float` | `30.0` | Timeout for HTTP requests and browser page loads (must be > 0). |
| `user_agent` | `str` | `""` | Custom User-Agent header for HTTP requests. |
| `proxy` | `str \| None` | `None` | HTTP proxy as `host:port` or `user:pass@host:port`. |
| `headless` | `bool` | `True` | Run the fallback browser headless. |
| `uc` | `bool` | `True` | SeleniumBase UC (undetected) mode for bot-protected pages. |
| `company_cache_expiry_time_days` | `int` | `90` | Days a scraped company record stays fresh. |
| `search_cache_expiry_time_days` | `int` | `90` | Days search results stay fresh. |
| `force_rescrape` | `bool` | `False` | Bypass all caches and scrape live. |

### `IQuery` — search queries

```python
from b2b_firmographic_crawler import IQuery

IQuery(company_name="stripe")   # used internally by search_company()
IQuery(stock_ticket="CRWD")     # at least one field must be non-empty
```

> Stock-symbol search is accepted by the query model but not implemented in
> any source yet (see [Roadmap](#roadmap)).

## Caching

Every source caches scraped pages and search results on disk
([diskcache](https://pypi.org/project/diskcache/)), so repeated runs are fast
and gentle on the target site:

- Records live under `<cache_dir>/<ModelName>/` — `CompanyData/` for company
  pages and `ISearchResponse/` for search results.
- `cache_dir` defaults to the current working directory; pass
  `B2BFirmographicCrawler(cache_dir=...)` to control it.
- Entries expire after `company_cache_expiry_time_days` /
  `search_cache_expiry_time_days`.
- Set `force_rescrape=True` to ignore cached data for a run.

```python
from b2b_firmographic_crawler import CompanyData
from b2b_firmographic_crawler.storage import DiskCache

cache = DiskCache(CompanyData, base_dir="./cache")   # ./cache/CompanyData
cache.delete("https://craft.co/stripe")              # drop one entry
cache.clear()                                        # drop the whole model's cache
```

## Exporting data

```python
from b2b_firmographic_crawler.services import (
    CSVExporter,
    JSONExporter,
    ParquetExporter,
)

company = crawler.get_company_data_by_name("stripe")

JSONExporter().export_data(company, filepath="stripe.json")     # no pandas needed
CSVExporter().export_data(company, filepath="stripe.csv")       # requires [export] extra
ParquetExporter().export_data(company, filepath="stripe.parquet")
```

JSON works out of the box. CSV/Parquet flatten nested fields via
`pandas.json_normalize` and require the `[export]` extra.

## Storing data

Both stores upsert a whole `CompanyData` document keyed by `company_domain`,
so re-running a crawler simply refreshes the existing rows/documents.

### PostgreSQL (JSONB)

```python
from b2b_firmographic_crawler.interfaces.iconfig import IDatabaseConfig
from b2b_firmographic_crawler.storage import PostgreSQLStorage

config = IDatabaseConfig(
    driver="postgresql",
    name="companies",
    host="localhost",
    user="postgres",
    password="secret",
    table="company_data",       # optional extra: table name
)

store = PostgreSQLStorage(config)
store.connect()                 # creates the table if missing
store.store_data(company)       # upsert keyed by company_domain
```

### MongoDB

```python
from b2b_firmographic_crawler.storage import MongoDBStorage

store = MongoDBStorage(
    IDatabaseConfig(
        driver="mongodb+srv",
        name="companies",
        host="cluster0.abc123.mongodb.net",
        user="crawler",
        password="secret",
    )
)
store.connect()
store.store_data(company)       # upsert into the "company_data" collection
```

### Configuration via environment variables

`IDatabaseConfig` is a pydantic-settings model with the `DB_` prefix, so
credentials can stay out of your code:

```bash
export DB_DRIVER=postgresql
export DB_NAME=companies
export DB_HOST=localhost
export DB_USER=postgres
export DB_PASSWORD=secret
```

```python
config = IDatabaseConfig()      # reads DB_* from the environment
```

| Variable | Field | Notes |
| -------- | ----- | ----- |
| `DB_DRIVER` | `driver` | `postgresql`, `mongodb`, `mongodb+srv`, ... |
| `DB_NAME` | `name` | Database name. |
| `DB_HOST` | `host` | Default `localhost`. |
| `DB_PORT` | `port` | Optional; sensible defaults per driver. |
| `DB_USER` / `DB_PASSWORD` | `user` / `password` | Optional credentials. |

## The data model

Every source returns the same schema. `CompanyData` is the top-level model;
all nested models live in `b2b_firmographic_crawler.models`.

### `CompanyData`

| Field | Type | Notes |
| ----- | ---- | ----- |
| `company_name` | `str` | Required. |
| `company_domain` | `str` | Registered domain, e.g. `stripe.com`. |
| `company_industries` | `list[str]` | Lower-cased industry tags. |
| `company_founded_year` | `int \| None` | |
| `company_website_url` | `str \| None` | |
| `company_funding_info` | `list[CompanyFundingInfo]` | |
| `company_logo_url` | `str \| None` | |
| `company_status` | `CurrentCompanyStatus` | Status enum + `last_updated`. |
| `company_description` | `str \| None` | |
| `key_executives` | `list[KeyExecutive]` | |
| `company_type` | `str \| None` | e.g. `private`, `public`. |
| `company_linkedin_url` | `str \| None` | |
| `company_twitter_url` | `str \| None` | |
| `company_symbol` | `str \| None` | Stock ticker, if known. |
| `company_operating_metrics` | `list[CompanyOperatingMetric]` | |
| `company_employee_counts` | `list[CompanyEmployeeCount]` | Time series. |
| `company_locations` | `list[CompanyLocation]` | `is_headquarter` flags the HQ. |
| `similar_companies` | `list[SimilarCompany]` | Competitors. |
| `other_social_media_urls` | `dict[OtherSocialMedia, str] \| None` | `instagram`, `facebook`, `crunchbase`. |
| `company_income_statements` | `list[IncomeStatement]` | |
| `last_scraped_at` | `datetime` | UTC, set automatically per record. |

### Nested models

- **`CompanyFundingInfo`** — `funding_round`, `funding_amount` (float),
  `funding_currency`, `funding_date`, `investors` (list of str)
- **`CompanyEmployeeCount`** — `total_employees` (int), `month`, `year`
- **`CompanyLocation`** — `city`, `state`, `country`, `country_code`,
  `postal_code`, `address`, `latitude`, `longitude`, `is_headquarter`
- **`KeyExecutive`** — `name`, `title`, `linkedin_url`, `twitter_url`,
  `other_social_media_urls`
- **`CompanyOperatingMetric`** — `company_specific_kpi`, `metric_value`,
  `unit_type`, `date`
- **`IncomeStatement`** — `revenue`, `currency`, `net_income`,
  `gross_profit_margin`, `end_date`, `period_type`, `ebitda`, `gross_profit`
- **`SimilarCompany`** — `company_name`, `company_industries`
- **`CurrentCompanyStatus`** — `status` (`CompanyStatus`: `active`,
  `inactive`, `acquired`, `bankrupt`, `closed`, `unknown`), `last_updated`

Example record (abridged):

```json
{
  "company_name": "Stripe",
  "company_domain": "stripe.com",
  "company_founded_year": 2010,
  "company_funding_info": [
    {
      "funding_round": "unknown",
      "funding_amount": 9400000000.0,
      "funding_currency": "USD"
    }
  ],
  "company_locations": [
    {
      "city": "South San Francisco",
      "country": "United States",
      "is_headquarter": true
    }
  ],
  "last_scraped_at": "2026-09-08T12:00:00Z"
}
```

## Adding a new source

The crawler is source-agnostic: each source is a **self-contained package** under
`b2b_firmographic_crawler.sources.<name>` that bundles its own **crawlers** (fetch
pages) and **parsers** (extract `CompanyData`). The source registers a **provider**
that wires these pieces into the generic orchestrators, giving you caching,
exporters and storage for free.

### 1. Create the source package

```
sources/
  owler/
    __init__.py          # exports OwlerSource and its crawlers/parsers
    provider.py          # OwlerSource(SourceProvider) — wires everything
    crawlers/
      __init__.py
      url_scraper.py     # OwlerUrlScraper(UrlScraper)
      search_scraper.py  # OwlerSearchScraper(CompanyNameScraper)
    parsers/
      __init__.py
      page_parser.py     # OwlerParser(Parser)
      search_parser.py   # OwlerSearchParser(SearchResponseParser)
```

Implement the low-level pieces by subclassing the base contracts:

```python
# owler_source/crawlers/url_scraper.py
from b2b_firmographic_crawler.base.scraper import UrlScraper

class OwlerUrlScraper(UrlScraper):
    """Fetches an Owler company page (HTTP first, browser fallback)."""

    def build_proxies(self, proxy):
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None

    def scrape(self, url, config=None) -> str:
        ...  # fetch https://www.owler.com/<path> and return raw HTML/JSON
```

```python
# owler_source/parsers/page_parser.py
from b2b_firmographic_crawler.base.parser import Parser
from b2b_firmographic_crawler.models.company_data import CompanyData

class OwlerParser(Parser):
    """Maps the raw page onto CompanyData."""

    def parse(self, data: str) -> CompanyData | None:
        ...  # parse and return CompanyData(company_name=..., ...)
```

```python
# owler_source/crawlers/search_scraper.py
from b2b_firmographic_crawler.base.scraper import CompanyNameScraper

class OwlerSearchScraper(CompanyNameScraper):
    def scrape(self, query, config=None) -> str:
        ...  # return raw search results for a company name
```

```python
# owler_source/parsers/search_parser.py
from b2b_firmographic_crawler.base.search_parser import SearchResponseParser
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse

class OwlerSearchParser(SearchResponseParser):
    def parse(self, data) -> list[ISearchResponse]:
        ...  # -> [ISearchResponse(company_name=..., source_url=..., slug=...), ...]
```

### 2. Wire them together and register

```python
# owler_source/provider.py
from typing import Optional

from b2b_firmographic_crawler.base.searcher import CompanySearcher
from b2b_firmographic_crawler.interfaces.iconfig import ICrawlerConfig, IQuery
from b2b_firmographic_crawler.interfaces.search_response import ISearchResponse
from b2b_firmographic_crawler.models.company_data import CompanyData
from b2b_firmographic_crawler.orchestrators.scraping_orchestrator import CompanyPageScrapingService
from b2b_firmographic_crawler.orchestrators.search_orchestrator import CompanySearchingService
from b2b_firmographic_crawler.searchers.search_by_name import CompanySearchByName
from b2b_firmographic_crawler.sources.base import SourceProvider
from b2b_firmographic_crawler.sources.registry import SourceRegistry

from .crawlers.url_scraper import OwlerUrlScraper
from .crawlers.search_scraper import OwlerSearchScraper
from .parsers.page_parser import OwlerParser
from .parsers.search_parser import OwlerSearchParser


@SourceRegistry.register("owler")
class OwlerSource(SourceProvider):
    """owler.com provider: company search + firmographic page scraping."""

    source_name = "owler"

    def __init__(self, cache_dir=None, **kwargs):
        self.search_service = CompanySearchingService(
            searcher=CompanySearchByName(
                OwlerSearchScraper(),
                OwlerSearchParser(),
            ),
            cache_dir=cache_dir,
        )
        self.scraping_service = CompanyPageScrapingService(
            page_parser=OwlerParser(),
            url_scraper=OwlerUrlScraper(),
            cache_dir=cache_dir,
        )

    def search_company(self, query, config=None):
        return self.search_service.search_company(IQuery(company_name=query), config)

    def get_company_data(self, url, config=None):
        return self.scraping_service.scrape_company_page(url, config)
```

### 3. Use it like any other source

```python
from b2b_firmographic_crawler import B2BFirmographicCrawler
import owler_source  # noqa: F401 — registers the source on import

crawler = B2BFirmographicCrawler()
company = crawler.get_company_data_by_name("acme", source="owler")
```

> **Tip:** The `CompanyPageScrapingService` and `CompanySearchingService` from
> `b2b_firmographic_crawler.orchestrators` are generic, source-agnostic services.
> Each source provider owns its website-specific crawlers and parsers, and plugs
> them into these shared orchestrators. This means adding a new source only
> requires implementing the website-specific pieces — caching, exports and
> storage come for free.

## Logging

All internals log through Python's standard `logging` module, controlled with
two environment variables:

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `CRAWLER_LOG_LEVEL` | `INFO` | Any stdlib level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, ... |
| `CRAWLER_LOG_FORMAT` | `%(asctime)s %(levelname)s %(name)s: %(message)s` | stdlib log format string |

```bash
CRAWLER_LOG_LEVEL=DEBUG uv run python your_script.py
```

## Testing

The repository ships an offline test suite — no network, no browser — covering
the parser, cache, search/scrape flows and the source registry:

```bash
uv sync                     # set up the environment
uv run python test.py       # run the suite
```

The tests are plain functions, so they also run under pytest:
`uv run pytest test.py`.

## Project structure

```text
src/b2b_firmographic_crawler/
├── __init__.py            # B2BFirmographicCrawler facade + register_source
├── models/                # CompanyData and nested Pydantic models
├── interfaces/            # ICrawlerConfig, IQuery, IDatabaseConfig, ISearchResponse
├── base/                  # abstract contracts (scraper, parser, searcher, storage, ...)
├── crawlers/              # backward-compatible re-exports for Craft crawlers
├── parsers/               # backward-compatible re-exports for Craft parsers
├── searchers/             # search-by-name orchestration
├── orchestrators/         # generic, source-agnostic search & scraping services
├── sources/               # provider registry and self-contained source packages
│   ├── base.py            # SourceProvider abstract base class
│   ├── registry.py        # SourceRegistry — string-keyed source registration
│   └── craft/             # Craft.co source package
│       ├── provider.py    # CraftSource — wires crawlers/parsers into orchestrators
│       ├── crawlers/      # Craft-specific URL and search crawlers
│       │   ├── http_url_crawler.py       # HTTP scraper (window.App.cache)
│       │   ├── selenium_url_crawler.py   # Selenium browser scraper
│       │   ├── url_scraper_chain.py      # HTTP → Selenium fallback chain
│       │   ├── http_company_search_crawler.py  # HTTP search-by-name
│       │   ├── selenium_base_search_crawler.py # Selenium search-by-name
│       │   └── company_name_scraper_chain.py   # search fallback chain
│       └── parsers/       # Craft-specific page and search parsers
│           ├── company_page_parser.py    # raw page → CompanyData
│           └── search_result_parser.py   # raw search → ISearchResponse list
├── storage/               # DiskCache, MongoDBStorage, PostgreSQLStorage
├── services/              # JSON / CSV / Parquet exporters
├── utils/                 # scraping + general helpers
├── global_utils/          # URI & currency helpers
└── logger.py              # logging setup
```

## FAQ

**Why is the first scrape slower?**
Craft serves much of its data client-side. The HTTP scraper tries first; if
the payload is not present in the HTML it raises and the SeleniumBase browser
fallback takes over automatically (downloading Chrome on first use).

**Where is my cache? How do I reset it?**
Under `cache_dir` (the current directory by default): `CompanyData/` and
`ISearchResponse/`. Delete those folders, or call `DiskCache(...).clear()`.

**Can I scrape through a proxy?**
Yes — `ICrawlerConfig(proxy="host:port")`. Both the HTTP and browser scrapers
honour it.

**Can I search by stock symbol?**
The query model accepts `stock_ticket`, but no source implements symbol
search yet (see [Roadmap](#roadmap)).

**Is scraping legal?**
This tool retrieves only **public, unauthenticated** pages — but you remain
solely responsible for how you use it and the data: check each website's
terms of service, robots directives, rate limits and applicable
data-protection law (e.g. GDPR). Cache aggressively, throttle politely, and
only collect what you need. See
[Disclaimer & privacy](#disclaimer--privacy) for the full statement.

## Roadmap

- [ ] Owler source
- [ ] Crunchbase source
- [ ] Search by stock symbol
- [ ] Concurrent scraping with rate limiting and retries
- [ ] More exporters (Excel, SQLite)

## Publishing

New versions are published to PyPI **automatically** whenever a GitHub Release
is published: the
[`publish` workflow](.github/workflows/publish.yml) runs the test suite,
verifies the release tag matches the package version, builds the sdist/wheel
and uploads them via PyPI **Trusted Publishing** (OIDC — no secrets stored in
the repository).

The short version of a release:

1. Bump the version in `pyproject.toml` and `src/b2b_firmographic_crawler/__init__.py`
2. Commit, push, and tag `vX.Y.Z`
3. Create the GitHub Release — Actions publishes it to PyPI

See [PUBLISHING.md](PUBLISHING.md) for one-time setup (pending trusted
publisher + GitHub environment), token-based publishing, TestPyPI dry runs,
manual `uv publish`, and troubleshooting.

## Contributing

Issues and pull requests are welcome! For local development:

```bash
git clone https://github.com/shaikhsajid1111/b2b-firmographic-crawler.git
cd b2b-firmographic-crawler
uv sync
uv run python test.py
```

Please add tests for any new source or parser change and keep the offline
suite green.

## License

[MIT](LICENSE) © Sajid Shaikh

## Acknowledgements

Built on top of great open-source projects:
[Pydantic](https://docs.pydantic.dev/),
[curl-cffi](https://github.com/lexiforest/curl_cffi),
[SeleniumBase](https://github.com/seleniumbase/SeleniumBase),
[diskcache](https://pypi.org/project/diskcache/),
[tldextract](https://github.com/john-kurkowski/tldextract),
[price-parser](https://github.com/scrapinghub/price-parser) and
[Babel](https://babel.pocoo.org/).
