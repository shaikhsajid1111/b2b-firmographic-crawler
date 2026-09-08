from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import UpdateResult

from b2b_firmographic_crawler.base.storage import DataStorage
from b2b_firmographic_crawler.interfaces.iconfig import IDatabaseConfig
from b2b_firmographic_crawler.models.company_data import CompanyData


class MongoDBStorage(DataStorage):
    def __init__(self, config: IDatabaseConfig) -> None:
        self.config = config

    def connect(self) -> None:
        self.mongo_connection = MongoClient(
            self.config.dsn, **self.config.extra_options
        )
        self.db: Database = self.mongo_connection[self.config.name]
        self.company_data_collection: Collection = self.db["company_data"]

    def store_data(self, company_data: CompanyData) -> UpdateResult:
        filter_q = {"company_domain": company_data.company_domain}
        # mode="json" keeps the payload BSON-encodable: nested enums (e.g.
        # CompanyStatus) become their values and datetimes become ISO strings.
        set_q = {"$set": company_data.model_dump(mode="json")}
        result = self.company_data_collection.update_one(
            filter=filter_q, update=set_q, upsert=True
        )
        return result
