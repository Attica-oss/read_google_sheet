"""High-level Google Sheets loader interface."""

from typing import cast

import polars as pl
from polars_result import Ok, Result
from src.read_google_sheet.config.datasets import ConfigName
from src.read_google_sheet.integrations.env_manager import SheetEnvironmentManager
from src.read_google_sheet.integrations.fetcher import GoogleSheetConfig
from src.read_google_sheet.integrations.types import SheetConfig, SheetConfigs


class GoogleSheetsLoader:
    """High-level interface for loading Google Sheets."""

    @staticmethod
    def from_env(
        config_name: ConfigName, env_file: str = ".env"
    ) -> Result[GoogleSheetConfig, Exception]:
        """Create a GoogleSheetConfig from an environment configuration entry."""

        def create_google_config(config: SheetConfig) -> Result[GoogleSheetConfig, Exception]:
            return Ok(
                GoogleSheetConfig(sheet_id=str(config.sheet_id), sheet_name=config.sheet_name)
            )

        return SheetEnvironmentManager.get_sheet_config(config_name, env_file).and_then(
            create_google_config
        )

    @staticmethod
    def load_sheet(
        config_name: ConfigName,
        env_file: str = ".env",
        as_dataframe: bool = False,
        parse_dates: bool = True,
    ) -> Result[pl.LazyFrame | pl.DataFrame, Exception]:
        """Load a Google Sheet directly from environment config."""

        def load_data(
            config: GoogleSheetConfig,
        ) -> Result[pl.LazyFrame | pl.DataFrame, Exception]:
            if as_dataframe:
                return cast(
                    Result[pl.LazyFrame | pl.DataFrame, Exception],
                    config.to_dataframe(parse_dates),
                )
            return cast(
                Result[pl.LazyFrame | pl.DataFrame, Exception],
                config.to_lazyframe(parse_dates),
            )

        return GoogleSheetsLoader.from_env(config_name, env_file).and_then(load_data)

    @staticmethod
    def list_available_sheets(env_file: str = ".env") -> Result[SheetConfigs, Exception]:
        """List all available sheet configurations from the .env file."""
        return SheetEnvironmentManager.load_sheet_configs(env_file)

    @staticmethod
    def save_sheet_config(
        config_name: ConfigName, sheet_id: str, sheet_name: str, env_file: str = ".env"
    ) -> Result[str, Exception]:
        """Save a new sheet configuration to the .env file."""
        return SheetEnvironmentManager.save_sheet_config(
            config_name, sheet_id, sheet_name, env_file
        )


def load_google_sheet(
    config_name: ConfigName,
    env_file: str = ".env",
    as_dataframe: bool = False,
    parse_dates: bool = True,
) -> Result[pl.LazyFrame | pl.DataFrame, Exception]:
    """
    Convenience function to load a Google Sheet in marimo notebooks.

    Args:
        config_name: Name of the configuration in .env
                     (e.g. 'SALES' matches SALES_ID and SALES_NAME)
        env_file: Path to .env file (default: '.env')
        as_dataframe: Return a collected DataFrame instead of a LazyFrame
        parse_dates: Attempt to parse date columns automatically

    Returns:
        Result containing a LazyFrame or DataFrame, or an Err on failure

    Example:
        >>> result = load_google_sheet("sales")
        >>> if result.is_ok():
        ...     df = result.unwrap().collect()
        ...     print(df)
    """
    return GoogleSheetsLoader.load_sheet(config_name, env_file, as_dataframe, parse_dates)
