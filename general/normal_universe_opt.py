import pandas as pd
import numpy as np
from pathlib import Path
from further_opts.objectives import weights
from further_opts.rollingwindow_and_eval import compute_statistics_rolling

snp = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "CSPX ETF Stock Price History.csv")
china = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "CNYA ETF Stock Price History.csv")
em = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "EIMI ETF Stock Price History.csv")
gold = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "XAD5 ETF Stock Price History.csv")
india = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "INR ETF Stock Price History.csv")
mscieurope = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "XMEU ETF Stock Price History.csv")
smallcapeurope = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "SXRJ ETF Stock Price History.csv")


dfs = [snp, china, em, gold, india, mscieurope, smallcapeurope]

N = len(dfs)
T = len(dfs[0]) - 1

dfs = [df[["Date", "Price", "Vol."]] for df in dfs]

# Convert Date to datetime
dfs_new = []
for df in dfs:
    df["Date"] = pd.to_datetime(df["Date"])
    dfs_new.append(df)

dfs = dfs_new

names = ["snp", "china", "em", "gold", "india", "mscieurope",
         "smallcapeurope", "ussmallcap", "silver"]

dfs_renamed = []

for name, df in zip(names, dfs):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    
    df = df.rename(columns={
        "Price": f"Price_{name}",
        "Vol.": f"Vol_{name}"
    })
    
    dfs_renamed.append(df)

dfs = dfs_renamed

# Merge all on Date
df_merged = dfs[0]
for df in dfs[1:]:
    df_merged = df_merged.merge(df, on="Date", how="inner", suffixes=("", "_x"))

# Sort by date
df_merged = df_merged.sort_values("Date")

def correct_volume(vol_value):
    if isinstance(vol_value, (float, int)):
        return vol_value
    if vol_value[-1] == "K":
        return 1000 * float(vol_value[:-1])
    if vol_value[-1] == "M":
        return 1_000_000 * float(vol_value[:-1])
    return float(vol_value)

df_merged = df_merged.set_index("Date")

price_cols = [col for col in df_merged.columns if col.startswith("Price_")]
vol_cols = [col for col in df_merged.columns if col.startswith("Vol_")]

prices_df = df_merged[price_cols].apply(pd.to_numeric, errors="coerce")
volumes_df = df_merged[vol_cols].copy()

for col in volumes_df.columns:
    volumes_df[col] = volumes_df[col].apply(correct_volume)

volumes_df = volumes_df.fillna(0.0)

prices = prices_df.values  # shape: (T+1, N)
volumes = volumes_df.values  # shape: (T+1, N)

returns = prices[1:] / prices[:-1] - 1
prices = prices[1:]
volumes = volumes[1:]         # (T, N)
dates = df_merged.index[1:]       # (T,)



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
MOMENTUM WITH CVAR:
[0.08762273 0.08762273 0.21139544 0.08762273 0.08762273 0.08762273
 0.08762273 0.26286819]
"""