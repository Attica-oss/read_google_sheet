import marimo

__generated_with = "0.20.1"
app = marimo.App(width="medium")

with app.setup:
    import polars as pl
    import marimo as mo
    from functools import partial
    from read_google_sheet import load_google_sheet
    from polars_result import Ok,Err,Result,ValidationError


@app.cell
def _():
    by_catch_transfer = load_google_sheet(sheet_id="1VbfiiWsp8yxs6KSR1CXpw1S_35tYlWV8UjjWah9Afpw",sheet_name="IPHSBycatchTransfer")
    return (by_catch_transfer,)


@app.class_definition
class SheetYearFilter:
    """Filter a Google Sheet LazyFrame by year and display in marimo."""

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

    def display(self, selected_year: int | str) -> mo.ui.table | mo.Html:
        """Filter and return a marimo table or error callout."""
        match self.filter(selected_year):
            case Ok(df):
                return mo.ui.table(
                    df.collect(), freeze_columns_left=[self.date_column]
                )
            case Err(e):
                return mo.callout(mo.md(f"**Error:** {e}"), kind="danger")

    @staticmethod
    def _filter_year(
        data: pl.LazyFrame,
        selected_year: int | str,
        date_column: str,
    ) -> Result[pl.LazyFrame, Exception]:
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
                        f"selected_year must be int or str, "
                        f"got {type(selected_year).__name__}"
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
                available_years = (
                    data.select(pl.col(date_column).dt.year().unique())
                    .collect()
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


@app.cell
def _():
    return


@app.cell
def _(by_catch_transfer):
    result = SheetYearFilter(data=by_catch_transfer).display("2026")
    return (result,)


@app.cell
def _():
    return


@app.cell
def _(result):
    result
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
