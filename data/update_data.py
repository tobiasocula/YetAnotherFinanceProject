"""
Update a local OHLCV CSV file with fresh data from yfinance.

Expected existing CSV format (no header row, columns in this order):
    Date,Open,High,Low,Close,Volume

Usage:
    python update_price_data.py

Just set TICKER and CSV_PATH below to match your setup.
"""

import pandas as pd
import yfinance as yf
from datetime import timedelta, date

# ---- Configuration -----------------------------------------------------
TICKER = "XXXX"                 # <-- set this to your actual ticker symbol
CSV_PATH = "data.csv"           # <-- path to your existing CSV file
COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
# -------------------------------------------------------------------------


def load_existing_data(path: str) -> pd.DataFrame:
    """Load the existing CSV (no header assumed) into a DataFrame."""
    try:
        df = pd.read_csv(path, header=None, names=COLUMNS)
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    except FileNotFoundError:
        print(f"No existing file found at '{path}'. Starting fresh.")
        return pd.DataFrame(columns=COLUMNS)


def fetch_new_data(ticker: str, start_date: date) -> pd.DataFrame:
    """Fetch data from yfinance starting the day after start_date, up to today."""
    fetch_start = start_date + timedelta(days=1)
    today = date.today()

    if fetch_start > today:
        print("Data is already up to date. Nothing to fetch.")
        return pd.DataFrame(columns=COLUMNS)

    print(f"Fetching {ticker} data from {fetch_start} to {today}...")
    new_data = yf.download(
        ticker,
        start=fetch_start.isoformat(),
        end=(today + timedelta(days=1)).isoformat(),  # end is exclusive in yfinance
        progress=False,
        auto_adjust=False,
    )

    if new_data.empty:
        print("No new data returned (e.g. weekend/holiday gap, or already current).")
        return pd.DataFrame(columns=COLUMNS)

    # yfinance may return a MultiIndex column structure for single tickers
    # depending on version; flatten it if necessary.
    if isinstance(new_data.columns, pd.MultiIndex):
        new_data.columns = new_data.columns.get_level_values(0)

    new_data = new_data.reset_index()
    new_data = new_data.rename(columns={"Adj Close": "AdjClose"})

    new_data = new_data[["Date", "Open", "High", "Low", "Close", "Volume"]]
    return new_data


def merge_and_save(existing: pd.DataFrame, new: pd.DataFrame, path: str) -> pd.DataFrame:
    """Merge new rows into existing data, drop duplicate dates, sort, and save."""
    combined = pd.concat([existing, new], ignore_index=True)
    combined = combined.drop_duplicates(subset="Date", keep="last")
    combined = combined.sort_values("Date").reset_index(drop=True)

    # Save back out in the same format as the original file (no header, no index)
    combined.to_csv(path, header=False, index=False)
    return combined


def main():
    existing = load_existing_data(CSV_PATH)

    if existing.empty:
        print("No existing data to base the update on. Please check CSV_PATH.")
        return

    last_date = existing["Date"].max().date()
    print(f"Last date in existing file: {last_date}")

    new_data = fetch_new_data(TICKER, last_date)

    if new_data.empty:
        print("No update performed.")
        return

    combined = merge_and_save(existing, new_data, CSV_PATH)
    added_rows = len(combined) - len(existing)
    print(f"Added {added_rows} new row(s). File now has {len(combined)} rows total.")
    print(f"Saved to: {CSV_PATH}")


if __name__ == "__main__":
    main()