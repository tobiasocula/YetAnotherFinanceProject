import pandas as pd
import numpy as np
from objectives import weights
from rollingwindow_and_eval import perform_validation

def stress_test(df_volmume, df_prices, start_train, end_train, end_valid,
                 gamma, alpha, lambda_, m_params, Sigma,
                 min_weight, stress_corr_weight, global_corr_mean,
                 global_corr_std, global_vola_mean,
                 global_vola_std, max_cash_alloc,
                 cash_alloc_param, risk_free):
    
    num_strats = 9

    train_volume = df_volmume[(df_volmume.index >= pd.to_datetime(start_train)) & (df_volmume.index <= pd.to_datetime(end_train))].values
    valid_volume = df_volmume[(df_volmume.index > pd.to_datetime(end_train)) & (df_volmume.index <= pd.to_datetime(end_valid))].values
    
    train_prices = df_prices[(df_prices.index >= pd.to_datetime(start_train)) & (df_prices.index <= pd.to_datetime(end_train))].values
    valid_prices = df_prices[(df_prices.index > pd.to_datetime(end_train)) & (df_prices.index <= pd.to_datetime(end_valid))].values

    returns_train = train_prices[1:] / train_prices[:-1] - 1
    returns_valid = valid_prices[1:] / valid_prices[:-1] - 1

    ws, stress_values = weights(returns_train, gamma, alpha, lambda_, train_volume, m_params, Sigma,
                 min_weight, stress_corr_weight, global_corr_mean,
                 global_corr_std, global_vola_mean,
                 global_vola_std, max_cash_alloc,
                 cash_alloc_param)
    
    stats = np.zeros((num_strats, 6))
    cumreturns_all = []
    # 6 statistics: var_alpha, cvar, sharpe, sortino, mean_return, md
    for i,w in enumerate(ws):
        var_alpha, cvar, sharpe, sortino, cumreturns, mean_return, md = perform_validation(w, returns_valid, valid_prices, risk_free)
        cumreturns_all.append(cumreturns)
        stats[i] = [var_alpha, cvar, sharpe, sortino, mean_return, md]

    labels = ["ER", "ER_cvar", "sharpe", "sharpe_cvar", "momentum_based", "momentum_cvar",
              "risk_parity", "hrp_weights", "equal_weights"]
    stats_labels = ["var_alpha", "cvar", "sharpe", "sortino", "mean_return", "md"]
    df = pd.DataFrame(stats, index=labels, columns=stats_labels)

    return df, cumreturns_all, ws, stress_values
    

    
