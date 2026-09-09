from typing import Optional

import pandas as pd

from b2b_firmographic_crawler.models.company_data import CompanyData


class ExcelExporter:
    """Export CompanyData to Excel (.xlsx) format."""

    def export_data(self, data: CompanyData, filepath: Optional[str] = None):
        """Export CompanyData to an Excel file.
        
        Args:
            data: CompanyData instance to export
            filepath: Output file path. Defaults to "company_data.xlsx"
            
        Returns:
            The filepath of the exported file
        """
        payload = data.model_dump(mode="json") if isinstance(data, CompanyData) else data
        df = pd.json_normalize(payload)
        output = filepath or "company_data.xlsx"
        df.to_excel(output, index=False, engine="openpyxl")
        return output