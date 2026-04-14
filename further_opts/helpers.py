import tensorflow as tf
import numpy as np
import pandas as pd

def max_drawdown(prices, weights):
    # prices (T,N)
    # weights (N,)
    T, N = prices.shape
    portfolio_values = prices @ weights # (T,)
    highest_peak = -1
    worst_pct = 0.0
    for t in range(T):
        highest_peak = max(highest_peak, portfolio_values[t])
        worst_pct = min(worst_pct, portfolio_values[t] / highest_peak - 1)
    return worst_pct

def lower_part_mean(matrix):
    n, _ = matrix.shape
    s = 0.0
    for i in range(1,n):
        for j in range(i):
            s += matrix[i,j]
    N = (n-1)*n/2
    return s / N

def sigmoid(x):
    return 1/(1+np.exp(-x))

def normalize(x):
    return (x - tf.reduce_mean(x)) / (tf.math.reduce_std(x) + 1e-8)

def rank_transform(x):
    ranks = tf.argsort(tf.argsort(x)) # first argsort gives sorted indices, second gives rank
    return tf.cast(ranks, tf.float32) / tf.cast(tf.size(x), tf.float32)

def stress_values_to_dict(strategy_labels, stresses):
    return {l: np.mean(x) for l,x in zip(strategy_labels, stresses)}

def costs_to_dict(strategy_labels, costs):
    return {l: np.mean(x) for l,x in zip(strategy_labels, costs)}

def cash_allocs_to_dict(strategy_labels, allocs):
    return {l: np.mean(x) for l,x in zip(strategy_labels, allocs)}