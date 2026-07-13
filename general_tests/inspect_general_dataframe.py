import pandas as pd
from pathlib import Path

dir = Path.cwd() / "data" / "OHCL" / "latest_data"
file = dir / "CUSS ETF Stock Price History.csv"
df = pd.read_csv(file, index_col=0)
print(df)