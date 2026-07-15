"""Cross-sectional momentum signal and portfolio construction."""
from __future__ import annotations

import numpy as np
import pandas as pd


def month_end_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Return observations from the final trading day of each calendar month."""
    if prices.empty:
        raise ValueError("prices must not be empty")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise TypeError("prices must use a DatetimeIndex")
    if not prices.index.is_monotonic_increasing or not prices.index.is_unique:
        raise ValueError("prices index must be sorted and unique")

    return prices.groupby(prices.index.to_period("M"), sort=True).tail(1)


def momentum_signal(
    prices: pd.DataFrame,
    lookback_months: int = 12,
    skip_months: int = 1,
) -> pd.DataFrame:
    """Compute cross-sectional momentum on actual month-end trading dates.

    A 12-1 signal compares the price one month before the signal date with
    the price twelve months before the signal date.
    """
    if lookback_months <= 0:
        raise ValueError("lookback_months must be positive")
    if skip_months < 0 or skip_months >= lookback_months:
        raise ValueError("skip_months must satisfy 0 <= skip_months < lookback_months")

    monthly = month_end_prices(prices)
    return monthly.shift(skip_months) / monthly.shift(lookback_months) - 1.0


def top_quantile_weights(signal: pd.DataFrame, quantile: float = 0.2) -> pd.DataFrame:
    """Build an equal-weight long portfolio from the strongest signals."""
    if not 0.0 < quantile <= 1.0:
        raise ValueError("quantile must satisfy 0 < quantile <= 1")

    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for date, row in signal.iterrows():
        valid = row.replace([np.inf, -np.inf], np.nan).dropna()
        if valid.empty:
            continue
        n_top = max(1, int(np.ceil(len(valid) * quantile)))
        top = valid.nlargest(n_top).index
        weights.loc[date, top] = 1.0 / n_top
    return weights
