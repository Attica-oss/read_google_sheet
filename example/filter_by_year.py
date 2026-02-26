"""Filter a Google Sheet LazyFrame by year and display"""

from functools import partial

import polars as pl
from polars_result import Err, Ok, Result
from src.read_google_sheet import ValidationError


class FilterByYear:
    """Filter a Google Sheet LazyFrame by year and display"""

    def __init__(
        self,
        data: Result[pl.LazyFrame, Exception],
        date_column: str = "date",
    ) -> None:
        self.data = data
        self.date_column = date_column

    def filter(self, selected_year: int | str) -> Result[pl.LazyFrame, Exception]:
        """Filter the data to a specific year."""
        return self.data.and_then(
            partial(
                self._filter_year,
                selected_year=selected_year,
                date_column=self.date_column,
            )
        )

    def display(self, selected_year: int | str) -> pl.DataFrame:
        """Filter and return a marimo table or error callout."""
        match self.filter(selected_year):
            case Ok(df):
                return df.unwrap()
            case Err(e):
                return pl.DataFrame(f"**Error:** {e}")

    @staticmethod
    def _filter_year(
        data: pl.LazyFrame,
        selected_year: int | str,
        date_column: str,
    ) -> Result[pl.LazyFrame, Exception]:
        """Filter the data to a specific year."""
        match selected_year:
            case str():
                try:
                    selected_year = int(selected_year)
                except ValueError:
                    return Err(
                        ValidationError(
                            f"Cannot parse '{selected_year}' as a year — "
                            f"expected a number like 2026"
                        )
                    )
            case int():
                pass
            case _:
                return Err(
                    ValidationError(
                        f"selected_year must be int or str, got {type(selected_year).__name__}"
                    )
                )

        match data.collect_schema():
            case schema if date_column not in schema:
                return Err(
                    ValidationError(
                        f"Column '{date_column}' not found in schema.\n"
                        f"Available columns: {list(schema.names())}"
                    )
                )
            case _:
                filtered = data.filter(pl.col(date_column).dt.year().eq(selected_year))
                assert isinstance(data, pl.DataFrame)
                available_years = (
                    data.select(pl.col(date_column).dt.year().unique())
                    .collect()
                    # .to_frame()
                    .to_series()
                    .to_list()
                )
                match selected_year in available_years:
                    case False:
                        return Err(
                            ValidationError(
                                f"Year {selected_year} not found in '{date_column}'.\n"
                                f"Available years: {sorted(available_years)}"
                            )
                        )
                    case True:
                        return Ok(filtered)
