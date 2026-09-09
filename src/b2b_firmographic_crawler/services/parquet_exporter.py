from typing import Optional

import pandas as pd

from b2b_firmographic_crawler.models.company_data import CompanyData


class ParquetExporter:
    """Export CompanyData to Parquet (Snappy-compressed, PyArrow engine).

    Requires the ``export`` extra (pandas + PyArrow). The record is
    flattened with ``pandas.json_normalize`` first, mirroring
    :class:`CSVExporter`.
    """

    def export_data(self, data: CompanyData, filepath: Optional[str] = None):
        """Write ``data`` as a Parquet dataset.

        Args:
            data: Company record (or an already-serialized mapping).
            filepath: Destination path. Defaults to
                ``"company_data.parquet"``.

        Returns:
            The filepath written.
        """
        payload = (
            data.model_dump(mode="json") if isinstance(data, CompanyData) else data
        )
        df = pd.json_normalize(payload)
        output = filepath or "company_data.parquet"
        df.to_parquet(path=output, engine="pyarrow", compression="snappy")
        return output
