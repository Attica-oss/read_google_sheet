"""High-level Google Sheets loader interface."""

from typing import cast

import polars as pl
from polars_result import Result

from read_google_sheet.integrations.fetcher import GoogleSheetConfig


def read_google_sheet(
    sheet_id: str,
    sheet_name: str,
    as_dataframe: bool = False,
    parse_dates: bool = True,
) -> Result[pl.LazyFrame | pl.DataFrame, Exception]:
    """
    Load a public Google Sheet into a Polars LazyFrame or DataFrame.

    Args:
        sheet_id:     44-character Google Sheet ID from the sheet URL
        sheet_name:   Tab name within the spreadsheet
        as_dataframe: Return a collected DataFrame instead of a LazyFrame
        parse_dates:  Attempt to parse date columns automatically

    Returns:
        Result containing a LazyFrame or DataFrame, or an Err on failure

    Example:
        >>> result = load_google_sheet(
        ...     sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
        ...     sheet_name="IPHSBycatchTransfer",
        ... )
        >>> if result.is_ok():
        ...     df = result.unwrap().collect()
    """
    config = GoogleSheetConfig(sheet_id=sheet_id, sheet_name=sheet_name)

    if as_dataframe:
        return cast(
            Result[pl.LazyFrame | pl.DataFrame, Exception],
            config.to_dataframe(parse_dates),
        )
    return cast(
        Result[pl.LazyFrame | pl.DataFrame, Exception],
        config.to_lazyframe(parse_dates),
    )
