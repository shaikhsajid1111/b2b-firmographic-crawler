from typing import Optional

import pandas as pd

from b2b_firmographic_crawler.models.company_data import CompanyData


class ExcelExporter:
    """Export CompanyData to Excel (.xlsx) format.

    Requires the ``export`` extra (pandas + openpyxl). The record is
    flattened with ``pandas.json_normalize`` first, mirroring
    :class:`CSVExporter`.
    """

    def export_data(self, data: CompanyData, filepath: Optional[str] = None):
        """Write ``data`` as a single-sheet ``.xlsx`` workbook.

        Args:
            data: Company record (or an already-serialized mapping).
            filepath: Destination path. Defaults to
                ``"company_data.xlsx"``.

        Returns:
            The filepath written.
        """
        payload = (
            data.model_dump(mode="json") if isinstance(data, CompanyData) else data
        )
        df = pd.json_normalize(payload)
        output = filepath or "company_data.xlsx"
        df.to_excel(output, index=False, engine="openpyxl")
        return output
