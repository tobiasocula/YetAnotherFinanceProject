import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
import numpy as np
from scipy.cluster.hierarchy import linkage, leaves_list

snp = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "CSPX ETF Stock Price History.csv")
china = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "CNYA ETF Stock Price History.csv")
em = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "EIMI ETF Stock Price History.csv")
gold = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "XAD5 ETF Stock Price History.csv")
india = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "INR ETF Stock Price History.csv")
mscieurope = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "XMEU ETF Stock Price History.csv")
smallcapeurope = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "SXRJ ETF Stock Price History.csv")
ussmallcap = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "CUSS ETF Stock Price History.csv")
silver = pd.read_csv(Path.cwd() / "data" / "OHCL" / "investing_dot_com_transformed" / "SSLN ETF Stock Price History.csv")

dfs = [snp, china, em, gold, india, mscieurope, smallcapeurope, ussmallcap, silver]
labels = ["SNP", "China", "EM", "Gold", "India", "MSCI-Europe", "SmallCapEurope", "USSmallCap", "Silver"]
date_sets = [set(df["Date"]) for df in dfs]

# Find the intersection of all date sets
common_dates = set.intersection(*date_sets)
# Filter each DataFrame to include only common dates
dfs = [df[df["Date"].isin(common_dates)] for df in dfs]
print([len(x) for x in dfs])

N = len(dfs)
T = len(dfs[0]) - 1

returns_all = np.empty((T, N))
for i, df in enumerate(dfs):
    returns_all[:, i] = df["Price"].pct_change().values[1:]


def hrp_weights(returns):
    # Compute correlation matrix
    corr = np.corrcoef(returns, rowvar=False)

    # Convert correlation to distance
    distance = np.sqrt(0.5 * (1 - corr))

    # Perform hierarchical clustering
    link = linkage(distance, method='single')

    # Get the order of assets from clustering
    order = leaves_list(link)

    # Allocate weights using recursive bisection
    n_assets = len(order)
    weights = np.zeros(n_assets)

    def get_weights(cluster, total_weight):
        if len(cluster) == 1:
            return {cluster[0]: total_weight}
        else:
            # Split the cluster into two sub-clusters
            left = cluster[:len(cluster)//2]
            right = cluster[len(cluster)//2:]

            # Allocate half the weight to each sub-cluster
            left_weights = get_weights(left, total_weight / 2)
            right_weights = get_weights(right, total_weight / 2)

            # Combine weights
            return {**left_weights, **right_weights}

    # Start with all assets in one cluster
    cluster = list(range(n_assets))
    weight_dict = get_weights(cluster, 1.0)

    # Assign weights to the ordered assets
    for i in range(n_assets):
        weights[order[i]] = weight_dict[i]

    return weights

# Example usage
returns = returns_all  # Your returns matrix (T x N)
weights = hrp_weights(returns)
print("HRP weights:", weights)