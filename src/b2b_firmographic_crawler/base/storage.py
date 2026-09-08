from abc import ABC, abstractmethod

from b2b_firmographic_crawler.models.company_data import CompanyData


class DataStorage(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def store_data(self, company_data: CompanyData):
        pass
