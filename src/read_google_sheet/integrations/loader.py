"""High-level Google Sheets loader interface."""

from typing import cast

import polars as pl
from polars_result import Err, Ok, Result

from read_google_sheet.core.exceptions import ConfigurationError
from read_google_sheet.integrations.fetcher import GoogleSheetConfig

# def read_google_sheet(
#     sheet_id: str,
#     sheet_name: str,
#     as_dataframe: bool = False,
#     parse_dates: bool = True,
# ) -> Result[pl.LazyFrame | pl.DataFrame, Exception]:
#     """
#     Load a public Google Sheet into a Polars LazyFrame or DataFrame.

#     Args:
#         sheet_id:     44-character Google Sheet ID from the sheet URL
#         sheet_name:   Tab name within the spreadsheet
#         as_dataframe: Return a collected DataFrame instead of a LazyFrame
#         parse_dates:  Attempt to parse date columns automatically

#     Returns:
#         Result containing a LazyFrame or DataFrame, or an Err on failure

#     Example:
#         >>> result = read_google_sheet(
#         ...     sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
#         ...     sheet_name="IPHSBycatchTransfer",
#         ... )
#         >>> if result.is_ok():
#         ...     df = result.unwrap().collect()
#     """
#     config = GoogleSheetConfig(sheet_id=sheet_id, sheet_name=sheet_name)

#     if as_dataframe:
#         return cast(
#             Result[pl.LazyFrame | pl.DataFrame, Exception],
#             config.to_dataframe(parse_dates),
#         )
#     return cast(
#         Result[pl.LazyFrame | pl.DataFrame, Exception],
#         config.to_lazyframe(parse_dates),
#     )


def read_google_sheet(
    sheet_name: str,
    sheet_id: str | None = None,
    url: str | None = None,
    as_dataframe: bool = False,
    parse_dates: bool = True,
) -> Result[pl.LazyFrame | pl.DataFrame, Exception]:
    """Load a public Google Sheet by ID or full URL."""
    match (sheet_id, url):
        case (None, None):
            return Err(ConfigurationError("Provide either sheet_id or url"))
        case (_, None):
            assert sheet_id is not None
            config_result: Result[GoogleSheetConfig, Exception] = Ok(
                GoogleSheetConfig(sheet_id=sheet_id, sheet_name=sheet_name)
            )
        case (None, _):
            assert url is not None
            config_result = GoogleSheetConfig.from_url(url, sheet_name)
        case _:
            return Err(ConfigurationError("Provide either sheet_id or url, not both"))

    if as_dataframe:
        return config_result.and_then(
            lambda c: cast(
                Result[pl.LazyFrame | pl.DataFrame, Exception], c.to_dataframe(parse_dates)
            )
        )
    return config_result.and_then(
        lambda c: cast(Result[pl.LazyFrame | pl.DataFrame, Exception], c.to_lazyframe(parse_dates))
    )
