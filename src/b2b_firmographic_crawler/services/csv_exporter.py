from typing import Optional

import pandas as pd

from b2b_firmographic_crawler.models.company_data import CompanyData


class CSVExporter:
    """Export CompanyData to CSV (flat, single-row) format.

    Requires the ``export`` extra (pandas). Nested structures are
    flattened with ``pandas.json_normalize`` using dotted column names.
    """

    def export_data(self, data: CompanyData, filepath: Optional[str] = None):
        """Write ``data`` as a one-row CSV file.

        Args:
            data: Company record (or an already-serialized mapping).
            filepath: Destination path. Defaults to
                ``"company_data.csv"``.

        Returns:
            The filepath written.
        """
        payload = (
            data.model_dump(mode="json") if isinstance(data, CompanyData) else data
        )
        df = pd.json_normalize(payload)
        output = filepath or "company_data.csv"
        df.to_csv(output, index=False)
        return output
