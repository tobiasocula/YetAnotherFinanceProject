import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

ticker = "MIND.L"
days_back = 30  # Change this (e.g., 14, 60, 90)

end_date = datetime.now() - timedelta
start_date = end_date - timedelta(days=days_back)

data = yf.download(ticker, start=start_date, end=end_date, progress=False, interval="1d")
print(data)

# Simplify: Drop multi-index, reorder to Open/Low/High/Close/Volume
if len(data.columns.levels[1]) > 1:  # Multi-ticker case
    data.columns = data.columns.droplevel(1)  # Remove 'Ticker'
data = data[['Open', 'Low', 'High', 'Close', 'Volume']]  # Reorder/select
data.index.name = 'Date'

print(data.head())
print(f"From {data.index[0].date()} to {data.index[-1].date()} ({len(data)} trading days)")
#data.to_csv("XMEU_simple.csv")