"""Dotenv operations with Result-based error handling."""

from pathlib import Path

from polars_result import Err, Ok, Result
from src.read_google_sheet.core import exceptions

# Try to import python-dotenv
try:
    from dotenv import load_dotenv, set_key

    DOTENV_AVAILABLE = True
    DOTENV_ERROR: exceptions.ConfigurationError | None = None
except ImportError:
    DOTENV_AVAILABLE = False
    DOTENV_ERROR = exceptions.ConfigurationError(
        "python-dotenv library is required for .env file support. "
        "Install it with: `uv add python-dotenv`"
    )
    load_dotenv = None  # type: ignore
    set_key = None  # type: ignore


class DotenvLoader:
    """Handles python-dotenv operations with Result-based error handling."""

    @staticmethod
    def _check_availability() -> Result[bool, Exception]:
        """Check if python-dotenv is available."""
        if not DOTENV_AVAILABLE:
            assert DOTENV_ERROR is not None
            return Err(DOTENV_ERROR)
        return Ok(True)

    @staticmethod
    def load_dotenv(env_path: Path) -> Result[bool, Exception]:
        """Load .env file using python-dotenv."""

        def do_load(_: bool) -> Result[bool, Exception]:
            result: bool = load_dotenv(env_path)
            return Ok(result)

        return DotenvLoader._check_availability().and_then(do_load)

    @staticmethod
    def set_key(
        env_path: str, key: str, value: str
    ) -> Result[tuple[bool | None, str, str], Exception]:
        """Set a key in .env file."""

        def do_set(_: bool) -> Result[tuple[bool | None, str, str], Exception]:
            result: tuple[bool | None, str, str] = set_key(env_path, key, value)
            return Ok(result)

        return DotenvLoader._check_availability().and_then(do_set)
