[![PyPI version](https://img.shields.io/pypi/v/read-google-sheet)](https://pypi.org/project/read-google-sheet/)
[![Python](https://img.shields.io/pypi/pyversions/read-google-sheet)](https://pypi.org/project/read-google-sheet/)
[![License](https://img.shields.io/github/license/Attica-oss/read_google_sheet)](https://github.com/Attica-oss/read_google_sheet/blob/main/LICENSE)

# read-google-sheet

Load public Google Sheets directly into Polars `LazyFrame` or `DataFrame` — with railway-oriented error handling via [`polars-result`](https://pypi.org/project/polars-result/).

> **Requires Python 3.14+**

## Features

- 📊 **Polars-native** — returns `LazyFrame` by default, `DataFrame` on request
- 🚂 **Railway-oriented** — every operation returns `Result[T, Exception]`, never raises
- 🔑 **Config-driven** — store sheet IDs and names in `.env`, load by name
- ✅ **Validated types** — `SheetId` enforces the 44-character Google Sheet ID format at construction
- 📦 **Minimal dependencies** — Polars, requests, python-dotenv, polars-result

## Installation

```bash
uv add read-google-sheet
```

```bash
pip install read-google-sheet
```

## Quick Start

### Load a sheet directly

```python
from polars_result import Ok, Err
from read_google_sheet import load_google_sheet

result = load_google_sheet("sales")

match result:
    case Ok(lf):
        print(lf.collect())
    case Err(e):
        print(f"Failed: {e}")
```

### Configure sheets in `.env`

Store your sheet configurations once and refer to them by name:

```bash
# .env
SALES_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
SALES_NAME=Sheet1

INVENTORY_ID=2CyiNWt1YSB6oGNLlBeCaijhnVrquumct85PhWF3vqnt
INVENTORY_NAME=Stock
```

```python
from read_google_sheet import load_google_sheet, GoogleSheetsLoader

# Load as LazyFrame (default)
result = load_google_sheet("sales")

# Load as collected DataFrame
result = load_google_sheet("inventory", as_dataframe=True)

# List all configured sheets
sheets = GoogleSheetsLoader.list_available_sheets()
```

### Save a new sheet config programmatically

```python
from polars_result import Ok, Err
from read_google_sheet import GoogleSheetsLoader

result = GoogleSheetsLoader.save_sheet_config(
    config_name="vessels",
    sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
    sheet_name="Berthing",
)

match result:
    case Ok(msg):
        print(msg)   # "Sheet config 'vessels' saved to .env"
    case Err(e):
        print(f"Failed: {e}")
```

---

## API Reference

### `load_google_sheet`

```python
def load_google_sheet(
    config_name: str,
    env_file: str = ".env",
    as_dataframe: bool = False,
    parse_dates: bool = True,
) -> Result[pl.LazyFrame | pl.DataFrame, Exception]
```

Convenience function for scripts and notebooks. Reads the sheet config from `.env` and returns the data.

| Parameter | Description |
|---|---|
| `config_name` | Name of the config entry (e.g. `"sales"` matches `SALES_ID` / `SALES_NAME`) |
| `env_file` | Path to `.env` file (default: `".env"`) |
| `as_dataframe` | Return a collected `DataFrame` instead of a `LazyFrame` |
| `parse_dates` | Attempt to parse date columns automatically |

---

### `GoogleSheetConfig`

Low-level dataclass for direct sheet access without `.env`:

```python
from read_google_sheet import GoogleSheetConfig

config = GoogleSheetConfig(
    sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
    sheet_name="Sheet1",
    timeout=10,
)

result = config.to_lazyframe()    # Result[pl.LazyFrame, Exception]
result = config.to_dataframe()    # Result[pl.DataFrame, Exception]
url    = config.create_url()      # Result[str, Exception]
data   = config.fetch_data()      # Result[StringIO, Exception]
```

---

### `GoogleSheetsLoader`

High-level interface for `.env`-based operations:

```python
from read_google_sheet import GoogleSheetsLoader

# Load a sheet
result = GoogleSheetsLoader.load_sheet("sales", as_dataframe=True)

# Create a config object from .env without loading data
config = GoogleSheetsLoader.from_env("sales")

# List all sheets in .env
sheets = GoogleSheetsLoader.list_available_sheets()

# Save a new config entry
result = GoogleSheetsLoader.save_sheet_config("sales", sheet_id, sheet_name)
```

---

### `SheetId`

A validated `str` subclass that enforces the Google Sheet ID format — 44 alphanumeric characters, hyphens, and underscores:

```python
from read_google_sheet import SheetId

# Validate and return Result
result = SheetId.validate("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms")  # Ok(SheetId(...))
result = SheetId.validate("bad-id")                                           # Err(ValueError(...))

# Quick boolean check
SheetId.is_valid("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms")  # True
```

---

### Exceptions

All exceptions inherit from `GoogleSheetError`:

| Exception | Raised when |
|---|---|
| `ConfigurationError` | `.env` missing, malformed, or sheet config not found |
| `InvalidSheetIDError` | Sheet ID fails the 44-character validation |
| `SheetFetchError` | HTTP request fails or returns a non-200 status |
| `NetworkError` | Connection error or timeout |
| `SheetTransformError` | CSV parsing or LazyFrame collection fails |
| `EnvError` | Reading or writing the `.env` file fails |
| `ValidationError` | General validation failure |

---

## Error Handling Patterns

### Pattern 1: Match on result

```python
from read_google_sheet import load_google_sheet, ConfigurationError, NetworkError

match load_google_sheet("sales"):
    case Ok(lf):
        df = lf.collect()
    case Err(ConfigurationError() as e):
        print(f"Config problem: {e}")
    case Err(NetworkError() as e):
        print(f"Network problem: {e}")
    case Err(e):
        print(f"Unexpected error: {e}")
```

### Pattern 2: Chain operations

```python
import polars as pl
from polars_result import Ok
from read_google_sheet import load_google_sheet

result = (
    load_google_sheet("sales")
    .map(lambda lf: lf.filter(pl.col("amount") > 0))
    .map(lambda lf: lf.select("vessel", "service", "amount"))
    .and_then(lambda lf: Ok(lf.collect()))
)
```

### Pattern 3: Fallback to another sheet

```python
result = (
    load_google_sheet("sales_live")
    .or_else(lambda _: load_google_sheet("sales_backup"))
    .unwrap_or(pl.LazyFrame())
)
```

### Pattern 4: Unwrap with default

```python
lf = load_google_sheet("sales").unwrap_or(pl.LazyFrame())
```

---

## Usage in Marimo Notebooks

```python
import marimo as mo
from polars_result import Ok, Err
from read_google_sheet import load_google_sheet

result = load_google_sheet("sales", as_dataframe=True)

match result:
    case Ok(df):
        mo.ui.table(df)
    case Err(e):
        mo.callout(mo.md(f"**Failed to load sheet:** {e}"), kind="danger")
```

---

## How It Works

The package uses Google Sheets' public CSV export endpoint — no API key or OAuth required. The sheet must be set to **"Anyone with the link can view"**.

The URL format used internally:

```
https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}
```

---

## Development

```bash
uv sync                                                           # install dependencies
uv run pytest                                                     # run tests
uv run pytest --cov=src/read_google_sheet --cov-report=html      # with coverage
uv run ruff check src/ tests/                                     # lint
uv run ruff format src/ tests/                                    # format
uv run ty check                                                   # type check
```

## Contributing

Contributions welcome — please open an issue or PR on [GitHub](https://github.com/Attica-oss/read_google_sheet).

## License

MIT — see [LICENSE](LICENSE) for details.
