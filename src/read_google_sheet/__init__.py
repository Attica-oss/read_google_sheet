"""Read Google Sheets Package"""

from polars_result import Result
from src.read_google_sheet.config.datasets import OperationDataset
from src.read_google_sheet.core.exceptions import (
    ConfigurationError,
    EnvError,
    GoogleSheetError,
    InvalidSheetIDError,
    NetworkError,
    SheetFetchError,
    SheetTransformError,
    ValidationError,
)
from src.read_google_sheet.integrations.env_manager import SheetEnvironmentManager
from src.read_google_sheet.integrations.fetcher import GoogleSheetConfig
from src.read_google_sheet.integrations.loader import GoogleSheetsLoader, load_google_sheet

__version__ = "0.1.0"

__all__ = [
    "ConfigurationError",
    "EnvError",
    "GoogleSheetConfig",
    "GoogleSheetError",
    "GoogleSheetsLoader",
    "InvalidSheetIDError",
    "NetworkError",
    "OperationDataset",
    "Result",
    "SheetEnvironmentManager",
    "SheetFetchError",
    "SheetTransformError",
    "ValidationError",
    "load_google_sheet",
]
