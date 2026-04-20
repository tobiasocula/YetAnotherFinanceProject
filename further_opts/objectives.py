import numpy as np
import tensorflow as tf
from scipy.optimize import minimize
from scipy.cluster.hierarchy import linkage, leaves_list
from further_opts.helpers import *

def risk_parity_weights(returns):
    
    # Compute volatilities for each asset
    volatilities = np.std(returns, axis=0)  # (N,)
    inverse_volatilities = 1.0 / (volatilities + 1e-8)  # Avoid division by zero

    # Normalize to get weights
    weights = inverse_volatilities / np.sum(inverse_volatilities)
    return weights


def hrp_weights(returns):
    # Compute correlation matrix
    corr = np.corrcoef(returns, rowvar=False)

    # Convert correlation to distance
    distance = np.sqrt(0.5 * (1 - corr))

    # Perform hierarchical clustering
    #link = linkage(squareform(distance), method='single')
    link = linkage(distance, method="single")

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

def weights(returns, gamma, alpha, lambda_, volumes, m_params, Sigma,
            min_weight,
            stress_corr_weight,
            global_corr_mean, global_corr_std,
            global_vola_mean, global_vola_std,
            max_cash_alloc,
            cash_alloc_param
            ):

    mu = np.mean(returns, axis=0)  # N
    T, N = returns.shape

    momentum = np.mean(returns[-60:], axis=0) # N
    volatility = np.std(returns[-60:], axis=0) # N
    vol_short = np.mean(volumes[-10:], axis=0)
    vol_long = np.mean(volumes[-60:], axis=0)
    volume_signal = (vol_short - vol_long) / (vol_long + 1e-8)
    risk_adj_momentum = momentum / (volatility + 1e-8)
    m1 = normalize(momentum)
    m2 = normalize(risk_adj_momentum)
    m3 = normalize(volume_signal)
    m = m1*m_params[0] + m2*m_params[1] + m3*m_params[2] # N

    # combine (N,)
    final_momentum = rank_transform(m)

    corr = np.corrcoef(returns, rowvar=False)
    this_session_mean_corr = lower_part_mean(corr)
    corr_standardized = (this_session_mean_corr - global_corr_mean) / global_corr_std

    def ER(w):
        return -(np.dot(mu, w) - gamma * np.dot(w, w))

    def ER_cvar(w):
        portfolio_returns = returns @ w
        losses = -portfolio_returns
        t = np.quantile(losses, alpha)  # VaR at level alpha
        cvar = t + (1 / (1 - alpha)) * np.mean(np.maximum(losses - t, 0))
        return -(np.dot(mu, w) - lambda_ * cvar - gamma * np.dot(w, w))  # Negative for maximization
    
    def sharpe(w):
        vola = np.sqrt(w.T @ Sigma @ w)
        return -(np.dot(mu, w) / vola - gamma * np.dot(w, w))
    
    def sharpe_cvar(w):
        vola = np.sqrt(w.T @ Sigma @ w)
        portfolio_returns = returns @ w
        losses = -portfolio_returns
        t = np.quantile(losses, alpha)  # VaR at level alpha
        cvar = t + (1 / (1 - alpha)) * np.mean(np.maximum(losses - t, 0))
        return -(np.dot(mu, w) / vola - lambda_ * cvar - gamma * np.dot(w, w))
    
    def momentum_based(w):
        return -(np.dot(final_momentum, w) - gamma * np.dot(w, w))
    
    def momentum_cvar(w):
        portfolio_returns = returns @ w
        losses = -portfolio_returns
        t = np.quantile(losses, alpha)  # VaR at level alpha
        cvar = t + (1 / (1 - alpha)) * np.mean(np.maximum(losses - t, 0))
        return -(np.dot(final_momentum, w) - lambda_ * cvar - gamma * np.dot(w, w))
    
    def balance_weights(w):
        volatility_standardized = (np.std(returns @ w) - global_vola_mean) / global_vola_std
        stress_score = sigmoid(
            stress_corr_weight * corr_standardized + 
            (1 - stress_corr_weight) * volatility_standardized
        )
        chosen_w = stress_score * np.ones(N) / N + (1 - stress_score) * w
        cash_pct = min(max_cash_alloc, cash_alloc_param * stress_score)
        w_with_cash = np.empty(chosen_w.shape[0] + 1)
        w_with_cash[:-1] = (1 - cash_pct) * chosen_w
        w_with_cash[-1] = cash_pct
        return stress_score, w_with_cash
    
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    w0 = np.ones(N) / N
    bounds = [(0, 1) for _ in range(N)]

    funcs = [ER, ER_cvar, sharpe, sharpe_cvar, momentum_based, momentum_cvar]
    w = [minimize(f, w0, constraints=constraints, bounds=bounds).x for f in funcs]
    w += [risk_parity_weights(returns), hrp_weights(returns)]
    w_new = []
    stresses = []
    for w_entry in w:
        stress, wnew = balance_weights(w_entry)
        wnew = np.clip(wnew, a_min = min_weight, a_max = 1.0)
        w_new.append(wnew / np.sum(wnew))
        stresses.append(stress)

    stress_eqw, w_eqw = balance_weights(np.ones(N) / N)
    w_eqw = np.clip(w_eqw, a_min = min_weight, a_max = 1.0)
    stresses.append(stress_eqw)
    w_new.append(w_eqw / np.sum(w_eqw))

    return w_new, stresses