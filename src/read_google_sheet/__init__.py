"""Read Google Sheets Package"""

from polars_result import Result

from read_google_sheet.core.exceptions import (
    ConfigurationError,
    GoogleSheetError,
    InvalidSheetIDError,
    NetworkError,
    SheetFetchError,
    SheetTransformError,
    ValidationError,
)
from read_google_sheet.integrations.fetcher import GoogleSheetConfig
from read_google_sheet.integrations.loader import load_google_sheet

__version__ = "0.1.0"

__all__ = [
    "ConfigurationError",
    "GoogleSheetConfig",
    "GoogleSheetError",
    "InvalidSheetIDError",
    "NetworkError",
    "Result",
    "SheetFetchError",
    "SheetTransformError",
    "ValidationError",
    "load_google_sheet",
]
