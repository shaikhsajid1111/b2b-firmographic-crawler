from abc import ABC, abstractmethod
from typing import Optional

from b2b_firmographic_crawler.models.company_data import CompanyData


class DataExporter(ABC):
    @abstractmethod
    def export_data(self, data: CompanyData, filepath: Optional[str] = None):
        pass
