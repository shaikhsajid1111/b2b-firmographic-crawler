import json
from typing import Optional

from b2b_firmographic_crawler.models.company_data import CompanyData


class JSONExporter:
    def export_data(self, data: CompanyData, filepath: Optional[str] = None):
        payload = data.model_dump(mode="json") if isinstance(data, CompanyData) else data
        if filepath:
            with open(filepath, "w", encoding="utf-8") as file:
                json.dump(payload, fp=file, indent=2)
            return filepath
        return json.dumps(payload)
