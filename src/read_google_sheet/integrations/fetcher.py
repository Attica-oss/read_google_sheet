"""Google Sheet fetching and transformation."""

from dataclasses import dataclass
from io import StringIO

import polars as pl
import requests
from polars_result import Err, Ok, Result

from read_google_sheet.core import exceptions


@dataclass
class GoogleSheetConfig:
    """Configuration for loading a Google Sheet."""

    sheet_id: str
    sheet_name: str
    timeout: int = 10

    def __post_init__(self) -> None:
        validation_result = self._validate()
        if not validation_result.is_ok():
            raise exceptions.ConfigurationError(str(validation_result.unwrap_err()))

    def _validate(self) -> Result[bool, Exception]:
        if not isinstance(self.sheet_id, str) or not self.sheet_id.strip():
            return Err(exceptions.ConfigurationError("sheet_id must be a non-empty string"))
        if not isinstance(self.sheet_name, str) or not self.sheet_name.strip():
            return Err(exceptions.ConfigurationError("sheet_name must be a non-empty string"))
        if self.timeout <= 0:
            return Err(exceptions.ConfigurationError("Timeout must be positive"))
        return Ok(True)

    def create_url(self) -> Result[str, Exception]:
        """Create URL for Google Sheets CSV export."""
        base_url = "https://docs.google.com/spreadsheets/d/"
        url = f"{base_url}{self.sheet_id}/gviz/tq?tqx=out:csv&sheet={self.sheet_name}"
        return Ok(url)

    def fetch_data(self) -> Result[StringIO, Exception]:
        """Fetch raw CSV data from Google Sheets."""

        def make_request(url: str) -> Result[StringIO, Exception]:
            try:
                response = requests.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    return Ok(StringIO(response.text))
                return Err(
                    exceptions.SheetFetchError(
                        f"Failed to fetch data. Status: {response.status_code}, "
                        f"Reason: {response.reason}"
                    )
                )
            except requests.exceptions.Timeout:
                return Err(
                    exceptions.SheetFetchError(f"Request timed out after {self.timeout} seconds")
                )
            except requests.exceptions.RequestException as e:
                return Err(exceptions.NetworkError(f"Network error: {e}"))

        return self.create_url().and_then(make_request)

    def to_lazyframe(self, parse_dates: bool = True) -> Result[pl.LazyFrame, Exception]:
        """Load sheet data as a Polars LazyFrame."""

        def create_lazyframe(csv_data: StringIO) -> Result[pl.LazyFrame, Exception]:
            try:
                lf = pl.scan_csv(
                    csv_data,
                    try_parse_dates=parse_dates,
                    infer_schema=True,
                    infer_schema_length=10_000_000,
                )
                return Ok(lf)
            except Exception as e:
                return Err(exceptions.SheetTransformError(f"Failed to parse CSV data: {e}"))

        return self.fetch_data().and_then(create_lazyframe)

    def to_dataframe(self, parse_dates: bool = True) -> Result[pl.DataFrame, Exception]:
        """Load sheet data as a collected Polars DataFrame."""

        def collect(lf: pl.LazyFrame) -> Result[pl.DataFrame, Exception]:
            try:
                df = lf.collect()
                if not isinstance(df, pl.DataFrame):
                    return Err(
                        exceptions.SheetTransformError(
                            "collect() returned an unexpected type — use collect(streaming=False)"
                        )
                    )
                return Ok(df)
            except Exception as e:
                return Err(exceptions.SheetTransformError(f"Failed to collect LazyFrame: {e}"))

        return self.to_lazyframe(parse_dates).and_then(collect)
