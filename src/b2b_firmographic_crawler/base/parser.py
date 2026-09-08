from abc import ABC, abstractmethod
from typing import Optional

from b2b_firmographic_crawler.models.company_data import CompanyData


class Parser(ABC):
    @abstractmethod
    def parse(self, data: str) -> Optional[CompanyData]:
        pass
