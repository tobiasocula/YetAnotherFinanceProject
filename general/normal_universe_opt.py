import pandas as pd
import numpy as np
from pathlib import Path
from extended_portfolio.objectives import weights
from extended_portfolio.rollingwindow_and_eval import compute_statistics_rolling
import sys

"""
python3 -m general.normal_universe_opt
"""

datadir = Path.cwd() / "data" / "OHCL" / "latest_data"

snp = pd.read_csv(datadir / "CSPX ETF Stock Price History.csv", index_col=0)
china = pd.read_csv(datadir / "CNYA ETF Stock Price History.csv", index_col=0)
em = pd.read_csv(datadir / "EIMI ETF Stock Price History.csv", index_col=0)
gold = pd.read_csv(datadir / "XAD5 ETF Stock Price History.csv", index_col=0)
india = pd.read_csv(datadir / "INR ETF Stock Price History.csv", index_col=0)
mscieurope = pd.read_csv(datadir / "XMEU ETF Stock Price History.csv", index_col=0)
smallcapeurope = pd.read_csv(datadir / "SXRJ ETF Stock Price History.csv", index_col=0)


dfs = [snp, china, em, gold, india, mscieurope, smallcapeurope]
N = len(dfs)
T = len(dfs[0]) - 1

dfs = [df[["Close", "Volume"]] for df in dfs]

names = ["snp", "china", "em", "gold", "india", "mscieurope",
         "smallcapeurope", "ussmallcap", "silver"]

new_dfs = []
for name, df in zip(names, dfs):
    df_new = df.copy()
    df_new.index = pd.to_datetime(df_new.index)
    df_new["Volume"].ffill()
    df_new = df_new.rename(columns={
        "Close": f"Close_{name}",
        "Volume": f"Volume_{name}"
    })
    
    new_dfs.append(df_new)

# Merge all on Date
df_merged = new_dfs[0]
# for df in dfs[1:]:
#     df_merged = df_merged.merge(df, on="Date", how="inner", suffixes=("", "_x"))

for df in new_dfs[1:]:
    df_merged = df_merged.merge(
        df,
        left_index=True,
        right_index=True,
        how="inner"
    )

# Sort by date
#df_merged = df_merged.sort_values("Date")
print(df_merged)

def correct_volume(vol_value):
    if isinstance(vol_value, (float, int)):
        return vol_value
    if vol_value[-1] == "K":
        return 1000 * float(vol_value[:-1])
    if vol_value[-1] == "M":
        return 1_000_000 * float(vol_value[:-1])
    return float(vol_value)

# df_merged = df_merged.set_index("Date")

price_cols = [col for col in df_merged.columns if col.startswith("Close_")]
vol_cols = [col for col in df_merged.columns if col.startswith("Volume_")]

prices_df = df_merged[price_cols].apply(pd.to_numeric, errors="coerce")
volumes_df = df_merged[vol_cols].copy()

# for col in volumes_df.columns:
#     volumes_df[col] = volumes_df[col].apply(correct_volume)

#volumes_df = volumes_df.fillna(0.0)

prices = prices_df.values  # shape: (T+1, N)
volumes = volumes_df.values  # shape: (T+1, N)

returns = prices[1:] / prices[:-1] - 1
prices = prices[1:]
volumes = volumes[1:]         # (T, N)
dates = df_merged.index[1:]       # (T,)

print("HERE")
print(returns.shape)
print(prices.shape)
print(volumes.shape)
print(dates.shape)

"""
Best performing strategy: momentum-based with CVAR
γ = 0.04, λ = 0.5, stress_corr_weight = 0.2
m_params = [0.33,0.33,0.33], cash_alloc_param = 0.5
"""


"""
def only_run_main(returns, gamma, alpha, lambda_, volumes, m_params, Sigma,
                  min_weight,
            stress_corr_weight,
            global_corr_mean, global_corr_std,
            global_vola_mean, global_vola_std,
            max_cash_alloc,
            cash_alloc_param
):
"""
# for vola and corr est
window_size = 60
stepsize = 30

all_corrs, all_volas = compute_statistics_rolling(returns, window_size, stepsize)
global_corr_mean = np.mean(all_corrs)
global_corr_std = np.std(all_corrs)
global_vola_mean = np.mean(all_volas)
global_vola_std = np.std(all_volas)

Sigma = np.cov(returns, rowvar=False)



gamma = 0.04
lambda_ = 0.5
stress_corr_weight = 0.2
m_params = [0.33,0.33,0.33]
cash_alloc_param = 0.5
alpha = 0.02
max_cash_alloc = 0.3
min_weight = 0.1

returns_actual_frame = returns[-255:] # last 255 days


ws, stresses = weights(returns, gamma, alpha, lambda_,
                       volumes, m_params, Sigma, min_weight,
                       stress_corr_weight, global_corr_mean,
                       global_corr_std, global_vola_mean,
                       global_vola_std, max_cash_alloc,
                       cash_alloc_param)

strat_labels = ["ER", "ER_cvar", "sharpe", "sharpe_cvar", "momentum_based", "momentum_cvar"]

for w,s,l in zip(ws, stresses, strat_labels):
    print('strategy', l, ':')
    print(w)
    print('stress:', s)


"""
strategy ER :
[0.09839524 0.09839524 0.09839524 0.09839524 0.11444283 0.09839524
 0.09839524 0.29518572]
stress: 0.9404958399608861
strategy ER_cvar :
[0.09836244 0.09836244 0.09836244 0.09836244 0.11473801 0.09836244
 0.09836244 0.29508733]
stress: 0.9380884572242277
strategy sharpe :
[0.17250746 0.08439242 0.08439242 0.20525521 0.08439242 0.10143489
 0.08439242 0.18323277]
stress: 0.43423988971968086
strategy sharpe_cvar :
[0.17274723 0.08440632 0.08440632 0.20506064 0.08440632 0.10130488
 0.08440632 0.18326198]
stress: 0.4342375948203957
strategy momentum_based :
[0.07647049 0.07647049 0.07647049 0.07647049 0.07647049 0.37442283
 0.07647049 0.16675424]
stress: 0.43612704897452703
strategy momentum_cvar :
[0.07647049 0.07647049 0.07647049 0.07647049 0.07647049 0.37442283
 0.07647049 0.16675424]
stress: 0.43612704897452703
"""