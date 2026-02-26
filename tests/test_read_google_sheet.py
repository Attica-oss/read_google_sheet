"""Tests for read_google_sheet package."""

from io import StringIO
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from read_google_sheet import (
    GoogleSheetConfig,
    read_google_sheet,
)
from read_google_sheet.core.exceptions import ConfigurationError, NetworkError, SheetFetchError


def as_df(lf: pl.LazyFrame) -> pl.DataFrame:
    """Collect a LazyFrame and assert it is a DataFrame."""
    df = lf.collect()
    assert isinstance(df, pl.DataFrame)
    return df


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_SHEET_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
VALID_SHEET_NAME = "Sheet1"
VALID_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
    "/edit?gid=0#gid=0"
)

SAMPLE_CSV = (
    "date,vessel,amount\n"
    "2025-01-01,MV Pacific Star,100.0\n"
    "2025-06-15,FV Albatross,200.0\n"
    "2024-03-10,MV Pacific Star,150.0\n"
)


@pytest.fixture
def sample_csv() -> str:
    return SAMPLE_CSV


@pytest.fixture
def sample_lazyframe() -> pl.LazyFrame:
    return pl.LazyFrame(
        {
            "date": ["2025-01-01", "2025-06-15", "2024-03-10"],
            "vessel": ["MV Pacific Star", "FV Albatross", "MV Pacific Star"],
            "amount": [100.0, 200.0, 150.0],
        }
    ).with_columns(pl.col("date").str.to_date())


@pytest.fixture
def valid_config() -> GoogleSheetConfig:
    return GoogleSheetConfig(sheet_id=VALID_SHEET_ID, sheet_name=VALID_SHEET_NAME)


@pytest.fixture
def mock_response(sample_csv: str) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.text = sample_csv
    return response


# ── GoogleSheetConfig validation ──────────────────────────────────────────────


class TestGoogleSheetConfigValidation:
    """Test GoogleSheetConfig construction and validation."""

    def test_valid_config(self) -> None:
        config = GoogleSheetConfig(sheet_id=VALID_SHEET_ID, sheet_name=VALID_SHEET_NAME)
        assert config.sheet_id == VALID_SHEET_ID
        assert config.sheet_name == VALID_SHEET_NAME
        assert config.timeout == 10

    def test_custom_timeout(self) -> None:
        config = GoogleSheetConfig(
            sheet_id=VALID_SHEET_ID, sheet_name=VALID_SHEET_NAME, timeout=30
        )
        assert config.timeout == 30

    def test_invalid_timeout_raises(self) -> None:
        with pytest.raises(ConfigurationError):
            GoogleSheetConfig(sheet_id=VALID_SHEET_ID, sheet_name=VALID_SHEET_NAME, timeout=0)

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ConfigurationError):
            GoogleSheetConfig(sheet_id=VALID_SHEET_ID, sheet_name=VALID_SHEET_NAME, timeout=-1)

    def test_empty_sheet_name_raises(self) -> None:
        with pytest.raises(ConfigurationError):
            GoogleSheetConfig(sheet_id=VALID_SHEET_ID, sheet_name="")

    def test_blank_sheet_name_raises(self) -> None:
        with pytest.raises(ConfigurationError):
            GoogleSheetConfig(sheet_id=VALID_SHEET_ID, sheet_name="   ")

    def test_empty_sheet_id_raises(self) -> None:
        with pytest.raises(ConfigurationError):
            GoogleSheetConfig(sheet_id="", sheet_name=VALID_SHEET_NAME)


# ── GoogleSheetConfig.from_url ────────────────────────────────────────────────


class TestGoogleSheetConfigFromUrl:
    """Test URL parsing via from_url classmethod."""

    def test_valid_url(self) -> None:
        result = GoogleSheetConfig.from_url(VALID_URL, VALID_SHEET_NAME)
        assert result.is_ok()
        assert result.unwrap().sheet_id == VALID_SHEET_ID

    def test_url_with_gid(self) -> None:
        url = f"https://docs.google.com/spreadsheets/d/{VALID_SHEET_ID}/edit?gid=1675360555#gid=1675360555"
        result = GoogleSheetConfig.from_url(url, VALID_SHEET_NAME)
        assert result.is_ok()
        assert result.unwrap().sheet_id == VALID_SHEET_ID

    def test_invalid_url_returns_err(self) -> None:
        result = GoogleSheetConfig.from_url("https://google.com", VALID_SHEET_NAME)
        assert result.is_err()
        assert isinstance(result.unwrap_err(), ConfigurationError)

    def test_empty_url_returns_err(self) -> None:
        result = GoogleSheetConfig.from_url("", VALID_SHEET_NAME)
        assert result.is_err()

    def test_custom_timeout_from_url(self) -> None:
        result = GoogleSheetConfig.from_url(VALID_URL, VALID_SHEET_NAME, timeout=20)
        assert result.is_ok()
        assert result.unwrap().timeout == 20


# ── GoogleSheetConfig.create_url ─────────────────────────────────────────────


class TestCreateUrl:
    """Test URL construction."""

    def test_creates_correct_url(self, valid_config: GoogleSheetConfig) -> None:
        result = valid_config.create_url()
        assert result.is_ok()
        url = result.unwrap()
        assert VALID_SHEET_ID in url
        assert VALID_SHEET_NAME in url
        assert "gviz/tq?tqx=out:csv" in url

    def test_url_format(self, valid_config: GoogleSheetConfig) -> None:
        result = valid_config.create_url()
        expected = (
            f"https://docs.google.com/spreadsheets/d/{VALID_SHEET_ID}"
            f"/gviz/tq?tqx=out:csv&sheet={VALID_SHEET_NAME}"
        )
        assert result.unwrap() == expected


# ── GoogleSheetConfig.fetch_data ─────────────────────────────────────────────


class TestFetchData:
    """Test HTTP fetching behaviour."""

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_successful_fetch(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig, mock_response: MagicMock
    ) -> None:
        mock_get.return_value = mock_response
        result = valid_config.fetch_data()
        assert result.is_ok()
        assert isinstance(result.unwrap(), StringIO)

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_non_200_status_returns_err(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig
    ) -> None:
        response = MagicMock()
        response.status_code = 403
        response.reason_phrase = "Forbidden"
        mock_get.return_value = response
        result = valid_config.fetch_data()
        assert result.is_err()
        assert isinstance(result.unwrap_err(), SheetFetchError)

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_timeout_returns_err(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig
    ) -> None:
        import httpx

        mock_get.side_effect = httpx.TimeoutException("timed out")
        result = valid_config.fetch_data()
        assert result.is_err()
        assert isinstance(result.unwrap_err(), SheetFetchError)
        assert "timed out" in str(result.unwrap_err()).lower()

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_network_error_returns_err(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig
    ) -> None:
        import httpx

        mock_get.side_effect = httpx.RequestError("connection refused")
        result = valid_config.fetch_data()
        assert result.is_err()
        assert isinstance(result.unwrap_err(), NetworkError)


# ── GoogleSheetConfig.to_lazyframe ───────────────────────────────────────────


class TestToLazyFrame:
    """Test LazyFrame construction from fetched data."""

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_returns_lazyframe(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig, mock_response: MagicMock
    ) -> None:
        mock_get.return_value = mock_response
        result = valid_config.to_lazyframe()
        assert result.is_ok()
        assert isinstance(result.unwrap(), pl.LazyFrame)

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_columns_match_csv(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig, mock_response: MagicMock
    ) -> None:
        mock_get.return_value = mock_response
        result = valid_config.to_lazyframe()
        assert result.is_ok()
        assert set(result.unwrap().collect_schema().names()) == {"date", "vessel", "amount"}

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_row_count(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig, mock_response: MagicMock
    ) -> None:
        mock_get.return_value = mock_response
        result = valid_config.to_lazyframe()
        assert result.is_ok()
        assert isinstance(result.unwrap(), pl.LazyFrame)
        df = as_df(result.unwrap())
        assert df.shape[0] == 3

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_fetch_failure_propagates(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig
    ) -> None:
        mock_get.return_value = MagicMock(status_code=500, reason_phrase="Server Error")
        result = valid_config.to_lazyframe()
        assert result.is_err()
        assert isinstance(result.unwrap_err(), SheetFetchError)


# ── GoogleSheetConfig.to_dataframe ───────────────────────────────────────────


class TestToDataFrame:
    """Test DataFrame construction from fetched data."""

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_returns_dataframe(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig, mock_response: MagicMock
    ) -> None:
        mock_get.return_value = mock_response
        result = valid_config.to_dataframe()
        assert result.is_ok()
        assert isinstance(result.unwrap(), pl.DataFrame)

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_dataframe_row_count(
        self, mock_get: MagicMock, valid_config: GoogleSheetConfig, mock_response: MagicMock
    ) -> None:
        mock_get.return_value = mock_response
        result = valid_config.to_dataframe()
        assert result.is_ok()
        assert result.unwrap().height == 3


# ── read_google_sheet ─────────────────────────────────────────────────────────


class TestReadGoogleSheet:
    """Test the top-level read_google_sheet convenience function."""

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_load_by_id_returns_lazyframe(
        self, mock_get: MagicMock, mock_response: MagicMock
    ) -> None:
        mock_get.return_value = mock_response
        result = read_google_sheet(sheet_id=VALID_SHEET_ID, sheet_name=VALID_SHEET_NAME)
        assert result.is_ok()
        assert isinstance(result.unwrap(), pl.LazyFrame)

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_load_by_url_returns_lazyframe(
        self, mock_get: MagicMock, mock_response: MagicMock
    ) -> None:
        mock_get.return_value = mock_response
        result = read_google_sheet(url=VALID_URL, sheet_name=VALID_SHEET_NAME)
        assert result.is_ok()
        assert isinstance(result.unwrap(), pl.LazyFrame)

    @patch("read_google_sheet.integrations.fetcher.httpx.get")
    def test_load_as_dataframe(self, mock_get: MagicMock, mock_response: MagicMock) -> None:
        mock_get.return_value = mock_response
        result = read_google_sheet(
            sheet_id=VALID_SHEET_ID, sheet_name=VALID_SHEET_NAME, as_dataframe=True
        )
        assert result.is_ok()
        assert isinstance(result.unwrap(), pl.DataFrame)

    def test_no_id_or_url_returns_err(self) -> None:
        result = read_google_sheet(sheet_name=VALID_SHEET_NAME)
        assert result.is_err()
        assert isinstance(result.unwrap_err(), ConfigurationError)

    def test_both_id_and_url_returns_err(self) -> None:
        result = read_google_sheet(
            sheet_id=VALID_SHEET_ID, url=VALID_URL, sheet_name=VALID_SHEET_NAME
        )
        assert result.is_err()
        assert isinstance(result.unwrap_err(), ConfigurationError)
