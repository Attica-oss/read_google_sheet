[![PyPI version](https://img.shields.io/pypi/v/read-google-sheet)](https://pypi.org/project/read-google-sheet/)
[![Python](https://img.shields.io/pypi/pyversions/read-google-sheet)](https://pypi.org/project/read-google-sheet/)
[![License](https://img.shields.io/github/license/Attica-oss/read_google_sheet)](https://github.com/Attica-oss/read_google_sheet/blob/main/LICENSE)

# read-google-sheet

Load public Google Sheets directly into Polars `LazyFrame` or `DataFrame` — with railway-oriented error handling via [`polars-result`](https://pypi.org/project/polars-result/).

> **Requires Python 3.14+**

## Features

- 📊 **Polars-native** — returns `LazyFrame` by default, `DataFrame` on request
- 🚂 **Railway-oriented** — every operation returns `Result[T, Exception]`, never raises
- ✅ **Validated** — sheet ID and name are validated before any network request
- 📦 **Minimal dependencies** — Polars, requests, polars-result

## Installation

```bash
uv add read-google-sheet
```

```bash
pip install read-google-sheet
```

## Quick Start

```python
from polars_result import Ok, Err
from read_google_sheet import read_google_sheet

result = read_google_sheet(
    sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
    sheet_name="Sheet1",
)

match result:
    case Ok(lf):
        print(lf.collect())
    case Err(e):
        print(f"Failed: {e}")
```

---

## API Reference

### `read_google_sheet`

```python
def read_google_sheet(
    sheet_id: str,
    sheet_name: str,
    as_dataframe: bool = False,
    parse_dates: bool = True,
) -> Result[pl.LazyFrame | pl.DataFrame, Exception]
```

| Parameter | Description |
|---|---|
| `sheet_id` | 44-character Google Sheet ID from the sheet URL |
| `sheet_name` | Tab name within the spreadsheet |
| `as_dataframe` | Return a collected `DataFrame` instead of a `LazyFrame` |
| `parse_dates` | Attempt to parse date columns automatically |

---

### `GoogleSheetConfig`

Low-level dataclass for direct access and step-by-step control:

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

### Exceptions

All exceptions inherit from `GoogleSheetError`:

| Exception | Raised when |
|---|---|
| `ConfigurationError` | Invalid sheet ID or empty sheet name |
| `SheetFetchError` | HTTP request fails or returns a non-200 status |
| `NetworkError` | Connection error or timeout |
| `SheetTransformError` | CSV parsing or LazyFrame collection fails |
| `ValidationError` | General validation failure |

---

## Error Handling Patterns

### Pattern 1: Match on result

```python
from read_google_sheet import read_google_sheet, ConfigurationError, NetworkError

match read_google_sheet(sheet_id="...", sheet_name="Sheet1"):
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
from read_google_sheet import read_google_sheet

result = (
    read_google_sheet(sheet_id="...", sheet_name="Sheet1")
    .map(lambda lf: lf.filter(pl.col("amount") > 0))
    .map(lambda lf: lf.select("vessel", "service", "amount"))
    .and_then(lambda lf: Ok(lf.collect()))
)
```

### Pattern 3: Fallback to another sheet

```python
result = (
    read_google_sheet(sheet_id="...", sheet_name="live")
    .or_else(lambda _: read_google_sheet(sheet_id="...", sheet_name="backup"))
    .unwrap_or(pl.LazyFrame())
)
```

### Pattern 4: Unwrap with default

```python
lf = read_google_sheet(sheet_id="...", sheet_name="Sheet1").unwrap_or(pl.LazyFrame())
```

---

## Usage in Marimo Notebooks

```python
import marimo as mo
from polars_result import Ok, Err
from read_google_sheet import read_google_sheet

result = read_google_sheet(
    sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
    sheet_name="Sheet1",
    as_dataframe=True,
)

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
