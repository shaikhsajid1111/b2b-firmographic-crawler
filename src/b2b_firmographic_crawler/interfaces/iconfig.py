from pydantic import BaseModel, Field, model_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any


class ICrawlerConfig(BaseModel):
    request_timeout: float = Field(default=30.0, gt=0)
    user_agent: str = ""
    proxy: Optional[str] = None
    headless: bool = True
    uc: bool = True
    company_cache_expiry_time_days: int = Field(default=90)
    search_cache_expiry_time_days: int = Field(default=90)
    force_rescrape: bool = Field(
        default=False,
        description="When set to true, will always bypass cache and scrape the data. Recommended to keep it False",
    )


class IQuery(BaseModel):
    company_name: str = Field(default="")
    stock_ticket: str = Field(default="")

    @model_validator(mode="after")
    def check_at_least_one(self):
        values = [self.company_name, self.stock_ticket]
        if not any(v is not None and v != "" for v in values):
            raise ValueError("At least one field must be provided and non-empty.")
        return self


class IDatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_", extra="allow", env_nested_delimiter="__"
    )

    # Core required fields (Now safer and optional for local/SQLite/Mongo)
    driver: str = Field(
        description="Database driver/protocol (e.g., postgresql, mongodb, mysql)"
    )
    name: str = Field(description="Database or scheme name")
    host: str = "localhost"
    port: Optional[int] = None  # None allows us to fallback cleanly based on the driver
    user: Optional[str] = None
    password: Optional[str] = None

    @computed_field
    @property
    def dsn(self) -> str:
        """Dynamically assembles an accurate DSN for both SQL and NoSQL systems."""
        # 1. Handle credentials safely
        auth = ""
        if self.user and self.password:
            auth = f"{self.user}:{self.password}@"
        elif self.user:
            auth = f"{self.user}@"

        # 2. Handle MongoDB Cloud / Atlas exception (+srv handles ports internally)
        if "+srv" in self.driver or self.driver == "mongodb+srv":
            return f"{self.driver}://{auth}{self.host}/{self.name}"

        # 3. Determine the correct network port if not explicitly provided
        resolved_port = self.port
        if resolved_port is None:
            if "postgres" in self.driver:
                resolved_port = 5432
            elif "mysql" in self.driver:
                resolved_port = 3306
            elif "mongo" in self.driver:
                resolved_port = 27017

        # 4. Return standard connection string format
        if resolved_port:
            return f"{self.driver}://{auth}{self.host}:{resolved_port}/{self.name}"

        # Fallback for systems like SQLite which may just use host/paths
        return f"{self.driver}://{auth}{self.host}/{self.name}"

    @property
    def extra_options(self) -> Dict[str, Any]:
        """Safely extract all loose, unmapped configuration settings."""
        all_extras = self.__pydantic_extra__ or {}
        return all_extras
