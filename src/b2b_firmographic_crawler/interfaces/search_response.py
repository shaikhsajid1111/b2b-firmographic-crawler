from pydantic import BaseModel, Field
from typing import Optional


class ISearchResponse(BaseModel):
    company_name: str = Field(min_length=1)
    source_url: str
    logo_url: Optional[str] = None
    slug: str = Field(min_length=1)
