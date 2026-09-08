from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime, timezone


class CompanyFundingInfo(BaseModel):
    funding_round: str = Field(
        default="unknown", description="The funding round of the company"
    )
    funding_amount: float = Field(
        default=0.0, description="The funding amount of the company"
    )
    funding_currency: Optional[str] = Field(
        default=None, description="The currency of the funding amount"
    )
    funding_date: Optional[str] = Field(
        default=None, description="The date of the funding round"
    )
    investors: List[str] = Field(
        default_factory=list, description="List of investors in the funding round"
    )


class CompanyOperatingMetric(BaseModel):
    company_specific_kpi: str = Field(
        default="", description="Company Specific KPIs"
    )
    metric_value: Optional[float] = Field(
        default=None, description="Metric value of the defined KPIs"
    )
    unit_type: Optional[str] = Field(
        default=None, description="Unit type of the KPIs"
    )
    date: Optional[datetime] = Field(
        default=None, description="The date of the metric"
    )


class CompanyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ACQUIRED = "acquired"
    BANKRUPT = "bankrupt"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class CurrentCompanyStatus(BaseModel):
    status: CompanyStatus = Field(
        default=CompanyStatus.UNKNOWN, description="The status of the company"
    )
    last_updated: Optional[datetime] = Field(
        default=None, description="The last updated date of the company status"
    )


class CompanyEmployeeCount(BaseModel):
    total_employees: int = Field(..., description="The total number of employees")
    month: Optional[int] = Field(
        default=None, description="The month of the employee count"
    )
    year: Optional[int] = Field(
        default=None, description="The year of the employee count"
    )


class OtherSocialMedia(Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    CRUNCHBASE = "crunchbase"


class KeyExecutive(BaseModel):
    name: str = Field(..., description="The name of the key executive")
    title: str = Field(..., description="The title of the key executive")
    linkedin_url: Optional[str] = Field(
        default=None, description="The LinkedIn URL of the key executive"
    )
    twitter_url: Optional[str] = Field(
        default=None, description="The twitter URL of the key executive"
    )
    other_social_media_urls: Optional[Dict[OtherSocialMedia, str]] = Field(
        default=None, description="Other social media URLs of the key executive"
    )


class CompanyLocation(BaseModel):
    city: Optional[str] = Field(
        default=None, description="The city of the company location"
    )
    state: Optional[str] = Field(
        default=None, description="The state of the company location"
    )
    country: Optional[str] = Field(
        default=None, description="The country of the company location"
    )
    country_code: Optional[str] = Field(
        default=None, description="The country code of the company location"
    )
    postal_code: Optional[str] = Field(
        default=None, description="The postal code of the company location"
    )
    address: Optional[str] = Field(
        default=None, description="Office location"
    )
    longitude: Optional[float] = Field(
        default=None, description="The longitude of the company location"
    )
    latitude: Optional[float] = Field(
        default=None, description="The latitude of the company location"
    )
    is_headquarter: Optional[bool] = Field(
        default=False, description="Whether the location is a headquarter"
    )


class SimilarCompany(BaseModel):
    company_name: str = Field(..., description="The name of the similar company")
    company_industries: List[str] = Field(
        default_factory=list, description="The industries of the similar company"
    )


class IncomeStatement(BaseModel):
    revenue: Optional[float] = Field(
        default=None, description="The revenue of the company"
    )
    currency: Optional[str] = Field(
        default=None, description="The currency of the income statement"
    )
    net_income: Optional[float] = Field(
        default=None, description="The net income of the company"
    )
    gross_profit_margin: Optional[float] = Field(
        default=None, description="The gross profit margin of the company"
    )
    end_date: Optional[str] = Field(
        default=None, description="The end date of the period"
    )
    period_type: Optional[str] = Field(
        default=None, description="The type of the period"
    )
    ebitda: Optional[float] = Field(
        default=None, description="The EBIT of the company"
    )
    gross_profit: Optional[float] = Field(
        default=None, description="The gross profit of the company"
    )


class CompanyData(BaseModel):
    company_name: str = Field(..., description="The name of the company")
    company_domain: str = Field(
        default="", description="The domain of the company"
    )
    company_industries: List[str] = Field(
        default_factory=list, description="The industries of the company"
    )
    company_founded_year: Optional[int] = Field(
        default=None, description="The year the company was founded"
    )
    company_website_url: Optional[str] = Field(
        default=None, description="The website URL of the company"
    )
    company_funding_info: List[CompanyFundingInfo] = Field(
        default_factory=list, description="The funding information of the company"
    )
    company_logo_url: Optional[str] = Field(
        default=None, description="The logo URL of the company"
    )
    company_status: CurrentCompanyStatus = Field(
        default_factory=lambda: CurrentCompanyStatus(
            status=CompanyStatus.UNKNOWN, last_updated=None
        ),
        description="The status of the company",
    )
    company_description: Optional[str] = Field(
        default="", description="The description of the company"
    )
    key_executives: List[KeyExecutive] = Field(
        default_factory=list, description="The key executives of the company"
    )
    company_type: Optional[str] = Field(
        default=None, description="The type of the company (e.g., private, public)"
    )
    company_linkedin_url: Optional[str] = Field(
        default=None, description="The LinkedIn URL of the company"
    )
    company_twitter_url: Optional[str] = Field(
        default=None, description="The Twitter URL of the company"
    )
    company_symbol: Optional[str] = Field(
        default=None, description="The stock symbol of the company"
    )
    company_operating_metrics: List[CompanyOperatingMetric] = Field(
        default_factory=list, description="The operating metrics of the company"
    )
    company_employee_counts: List[CompanyEmployeeCount] = Field(
        default_factory=list, description="The employee counts of the company"
    )
    company_locations: List[CompanyLocation] = Field(
        default_factory=list, description="The location information of the company"
    )
    similar_companies: List[SimilarCompany] = Field(
        default_factory=list, description="The similar companies"
    )
    other_social_media_urls: Optional[Dict[OtherSocialMedia, str]] = Field(
        default=None, description="Other social media URLs of the company"
    )
    company_income_statements: List[IncomeStatement] = Field(
        default_factory=list, description="Income statements"
    )
    last_scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="The timestamp when the data was last scraped",
    )

