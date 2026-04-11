from objectives import weights
import numpy as np
import pandas as pd
from helpers import *

def perform_validation(w, validation_returns, validation_prices, risk_free):
    
    # validation data is shape (T, N)

    # Reshape w to (N+1, 1) for matrix multiplication
    # perform metrics
    total_return = validation_returns @ w[:-1] + w[-1] * risk_free / 255

    std = np.std(total_return)
    downside = total_return[total_return < 0]
    downside_std = np.std(downside) if len(downside) > 0 else 0.0

    cumulative_returns = np.cumprod(total_return + 1) - 1
    sharpe = (255 * np.mean(total_return) - risk_free) / (np.sqrt(255) * std)
    sortino = (255 * np.mean(total_return) - risk_free) / (np.sqrt(255) * downside_std + 1e-4)


    alpha = 0.10

    var_alpha = np.quantile(total_return, alpha)
    cvar = total_return[total_return <= var_alpha].mean()
    mean_return = np.mean(total_return)

    md = max_drawdown(validation_prices, w[:-1])

    print('PRINTING STATS'); print()
    print("Mean daily return:", np.mean(total_return))
    print("Annualized mean return:", 255 * np.mean(total_return))
    print("Daily std:", std)
    print("Annualized std:", np.sqrt(255) * std)
    print("Daily risk-free rate:", risk_free / 255)
    print("Annualized risk-free rate:", risk_free)
    print("Excess return (annualized):", 255 * np.mean(total_return) - risk_free / 255)
    print("Sharpe ratio:", (255 * np.mean(total_return) - risk_free / 255) / (np.sqrt(255) * std))

    return var_alpha, cvar, sharpe, sortino, cumulative_returns, mean_return, md

def compute_statistics_rolling(returns, window_size, stepsize):

    all_corrs = []
    all_volas = []
    T, N = returns.shape
    w = np.ones(N) / N
    for idx in range(0, T - window_size, stepsize):
        section = returns[idx:idx+window_size,:]

        corr = np.corrcoef(section, rowvar=False) # (N,N)

        all_corrs.append(lower_part_mean(corr))
        returns_total = section @ w

        std = np.std(returns_total)
        all_volas.append(std)
    
    all_corrs = np.array(all_corrs)
    all_volas = np.array(all_volas)
    return all_corrs, all_volas

def rolling_window(returns, volume, price, window_size,
                    stepsize,
                    validation_size,
                    gamma, alpha, lambda_, m_params, risk_free, etf_spreads,
                    weight_diff_rebalance,
                    stress_corr_weight,
                    max_cash_alloc, cash_alloc_param,
                       min_weight):

    
    num_strats = 9
    all_corrs, all_volas = compute_statistics_rolling(returns, window_size, window_size)
    global_corr_mean = np.mean(all_corrs)
    global_corr_std = np.std(all_corrs)
    global_vola_mean = np.mean(all_volas)
    global_vola_std = np.std(all_volas)

    track_num_rebalances = np.zeros(num_strats)
    track_cash_allocs = [[] for _ in range(num_strats)]

    T, N = returns.shape

    mean_stats = np.zeros((num_strats, 6))
    # 6 statistics: var_alpha, cvar, sharpe, sortino, mean_return, md
    
    w_prev = [np.full(N+1, None) for _ in range(num_strats)]
    count_iters = 0
    
    total_stress_values = [[] for _ in range(num_strats)]
    total_costs = [[] for _ in range(num_strats)]

    for idx in range(window_size, T, window_size):

        returns_train = returns[idx-window_size:idx]
        returns_val = returns[idx:idx+window_size]
        prices_val = price[idx:idx+window_size]

        volumes_train = volume[idx-window_size:idx]
        Sigma = np.cov(returns_train, rowvar=False)

        count_iters += 1

        # includes cash
        ws, stresses = weights(returns_train, gamma, alpha, lambda_,
                               volumes_train, m_params, Sigma,
                               min_weight,
                               stress_corr_weight, global_corr_mean,
                               global_corr_std, global_vola_mean, global_vola_std,
                               max_cash_alloc, cash_alloc_param)
        
        for i,stress in enumerate(stresses):
            total_stress_values[i].append(stress)

        # iterate strategies

        for i, (w, wprev) in enumerate(zip(ws, w_prev)):
            if wprev[0] is None: # meaning all are None
                wprev = w

            diff = np.abs(wprev - w)
            if not diff[diff >= weight_diff_rebalance].any():
                cost = 0.0
            else:
                turnover_vector = np.abs(w[:-1] - wprev[:-1])  # exclude cash
                cost = np.sum(turnover_vector * etf_spreads)

            track_cash_allocs[i].append(w[-1])

            total_costs[i].append(cost)
            var_alpha, cvar, sharpe, sortino, _, mean_return, md = perform_validation(w, returns_val, prices_val, risk_free)
            mean_return_adj = mean_return - cost
            perf_stats = np.array([var_alpha, cvar, sharpe, sortino, mean_return_adj, md])
            mean_stats[i, :] += perf_stats
            if cost == 0.0:
                track_num_rebalances[i] += 1

            w_prev[i] = w

    track_num_rebalances /= count_iters

    mean_stats /= count_iters
    labels = ["ER", "ER_cvar", "sharpe", "sharpe_cvar", "momentum_based", "momentum_cvar",
              "risk_parity", "hrp_weights", "equal_weights"]
    stats_labels = ["var_alpha", "cvar", "sharpe", "sortino", "mean_return", "md"]
    df = pd.DataFrame(mean_stats, index=labels, columns=stats_labels)
    return df, total_costs, total_stress_values, track_num_rebalances, track_cash_allocs