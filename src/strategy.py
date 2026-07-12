"""Cross-sectional momentum signal and portfolio construction."""
from __future__ import annotations

import numpy as np
import pandas as pd


def momentum_signal(prices: pd.DataFrame, lookback_months: int = 12, skip_months: int = 1) -> pd.DataFrame:
    """Classic 12-1 momentum: return over the past `lookback` months,
    excluding the most recent `skip` month (short-term reversal).

    Computed on month-end prices; returns a DataFrame of signals indexed by
    rebalance date (month end).
    """
    monthly = prices.resample("ME").last()
    mom = monthly.shift(skip_months) / monthly.shift(lookback_months) - 1.0
    return mom


def top_quantile_weights(signal: pd.DataFrame, quantile: float = 0.2) -> pd.DataFrame:
    """Equal-weight long portfolio of the top `quantile` of assets by signal.

    Assets with missing signal (insufficient history) are excluded.
    Weights sum to 1 on each rebalance date with at least one valid asset.
    """
    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for date, row in signal.iterrows():
        valid = row.dropna()
        if valid.empty:
            continue
        n_top = max(1, int(np.ceil(len(valid) * quantile)))
        top = valid.nlargest(n_top).index
        weights.loc[date, top] = 1.0 / n_top
    return weights
