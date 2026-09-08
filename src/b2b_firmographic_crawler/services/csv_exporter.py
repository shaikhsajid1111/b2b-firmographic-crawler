from typing import Optional

import pandas as pd

from b2b_firmographic_crawler.models.company_data import CompanyData


class CSVExporter:
    def export_data(self, data: CompanyData, filepath: Optional[str] = None):
        payload = data.model_dump(mode="json") if isinstance(data, CompanyData) else data
        df = pd.json_normalize(payload)
        output = filepath or "company_data.csv"
        df.to_csv(output, index=False)
        return output
