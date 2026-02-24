import marimo

__generated_with = "0.20.1"
app = marimo.App(width="medium")

with app.setup:
    import polars as pl
    import marimo as mo
    from read_google_sheet import load_google_sheet


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
