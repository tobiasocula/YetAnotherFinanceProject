import pandas as pd
from pathlib import Path
import numpy as np
import yfinance as yf
import sys

base = Path.cwd() / "data"
old_data = base / "OHCL" / "investing_dot_com_transformed"
new_data = base / "OHCL" / "latest_data_new"
new_data.mkdir(exist_ok=True)

equities = [
    "INR ETF Stock Price History.csv",
    "SXRJ ETF Stock Price History.csv",
    "EIMI ETF Stock Price History.csv",
    "XAD5 ETF Stock Price History.csv",
    "CSPX ETF Stock Price History.csv",
    "XMEU ETF Stock Price History.csv",
    "SSLN ETF Stock Price History.csv",
    "CUSS ETF Stock Price History.csv",
    "CNYA ETF Stock Price History.csv",
    ]

# TEMP
#equities = [x.split('.')[0] + "_merged." + x.split('.')[-1] for x in equities]

to_fetch = [
"MIND.L", # india
"SXRJ.DE", # small cap europe
"EIMI.L", # em
"XGLD.L", # gold
"CSPX.L", # SNP
"XMEU.L", # MSCI Europe
"SSLN.L", # silver
"CUSS.L", # us small cap
"CNYA.L" # china
]

from datetime import datetime, timedelta

def clean_df(df):
    # Drop rows where index is NaT/NaN or columns are all NaN/non-numeric
    df = df[df.index.notna()]
    df = df[~df.index.isin(['Date', 'Ticker', np.nan])]
    df = df.dropna(how='all')  # Drop fully empty rows
    
    # Convert numeric columns (handles weird floats)
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    existing_cols = [col for col in numeric_cols if col in df.columns]
    
    for col in existing_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows missing ALL price new (only existing cols)
    if existing_cols:  # Only if we have some price cols
        df = df.dropna(subset=existing_cols, how='all')
    
    return df

days_back = 30
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)

for ticker, actual_name in zip(to_fetch, equities):
    print()
    print('ticker:', ticker, 'and actname:', actual_name)
    new = yf.download(ticker, start=start_date, end=end_date, progress=False, interval="1d")
    print('downloaded')

    if isinstance(new.columns, pd.MultiIndex):
        new.columns = new.columns.droplevel(1)  # Remove the 'Ticker' level
    new = new[['Open', 'Low', 'High', 'Close', 'Volume']]  # Reorder/select
    new.index.name = 'Date'

    old = pd.read_csv(old_data / actual_name, index_col=0)
    old = old.rename({"Price": "Close"}, axis=1)
    print('DOWNLOADED:'); print(new)
    if new.empty:
        raise AssertionError(f"doesn't exist: {ticker}")
    print(); print('OLD:'); print(old)
    print('COLS OLD:'); print(old.columns)
    print('COLS NEW:'); print(new.columns)

    old = clean_df(old)
    print('cleaned old')
    new = clean_df(new)
    print('cleaned new')

    common_cols = ["Open", "High", "Low", "Close"]  # Exclude Volume for now
    old = old[common_cols].reindex(columns=common_cols)
    new = new[common_cols].reindex(columns=common_cols)

    new.index = pd.to_datetime(new.index)
    old.index = pd.to_datetime(old.index)

    merged = pd.concat([old, new])
    merged = merged[~merged.index.duplicated(keep='last')]
    merged.sort_index(inplace=True)

    merged.to_csv(new_data / actual_name)
