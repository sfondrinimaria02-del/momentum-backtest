"""Close-to-close backtesting engine with transaction costs.

Signals dated at month-end are scheduled for the close of the first trading
session strictly after the signal date. New weights therefore earn returns
starting with the following close-to-close interval. This conservative timing
avoids assigning an overnight return to a portfolio that was not yet tradable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _validate_inputs(
    prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    tc_bps: float,
) -> pd.DataFrame:
    if tc_bps < 0:
        raise ValueError("tc_bps must be non-negative")
    if prices.empty:
        raise ValueError("prices must not be empty")
    if target_weights.empty:
        raise ValueError("target_weights must not be empty")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise TypeError("prices must use a DatetimeIndex")
    if not isinstance(target_weights.index, pd.DatetimeIndex):
        raise TypeError("target_weights must use a DatetimeIndex")
    if not prices.index.is_monotonic_increasing or not prices.index.is_unique:
        raise ValueError("prices index must be sorted and unique")
    if not target_weights.index.is_monotonic_increasing or not target_weights.index.is_unique:
        raise ValueError("target_weights index must be sorted and unique")
    if set(prices.columns) != set(target_weights.columns):
        raise ValueError("target_weights columns must exactly match prices columns")

    numeric_prices = prices.astype(float)
    if not np.isfinite(numeric_prices.to_numpy()).all():
        raise ValueError("prices must contain only finite values")
    if (numeric_prices <= 0.0).to_numpy().any():
        raise ValueError("prices must be strictly positive")

    weights = target_weights.reindex(columns=prices.columns).astype(float)
    if not np.isfinite(weights.to_numpy()).all():
        raise ValueError("target_weights must contain only finite values")
    if (weights < 0.0).to_numpy().any():
        raise ValueError("target_weights must be long-only")

    row_sums = weights.sum(axis=1).to_numpy()
    valid_sums = np.isclose(row_sums, 0.0) | np.isclose(row_sums, 1.0)
    if not valid_sums.all():
        raise ValueError("each target_weights row must sum to either zero or one")
    return weights


def run_backtest(
    prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    tc_bps: float = 10.0,
) -> pd.DataFrame:
    """Return daily portfolio returns, costs, and one-way turnover.

    Rebalances occur at the close of the first trading day after each target
    date. Existing holdings earn that day's close-to-close return before the
    portfolio is rebalanced.
    """
    weights = _validate_inputs(prices, target_weights, tc_bps)
    daily_ret = prices.astype(float).pct_change(fill_method=None).fillna(0.0)
    tc = tc_bps / 1e4

    dates = daily_ret.index
    schedule: dict[pd.Timestamp, pd.Timestamp] = {}
    positions = dates.searchsorted(weights.index, side="right")
    for target_date, position in zip(weights.index, positions, strict=True):
        if position >= len(dates):
            continue
        execution_date = dates[position]
        if execution_date in schedule:
            raise ValueError("multiple target dates map to the same execution date")
        schedule[execution_date] = target_date

    current = pd.Series(0.0, index=prices.columns)
    rows: list[tuple[float, float, float]] = []

    for date, asset_returns in daily_ret.iterrows():
        portfolio_return = float((current * asset_returns).sum())

        gross_weights = current * (1.0 + asset_returns)
        total = float(gross_weights.sum())
        drifted = gross_weights / total if total > 0.0 else gross_weights

        cost = 0.0
        turnover = 0.0
        if date in schedule:
            target = weights.loc[schedule[date]]
            turnover = float((target - drifted).abs().sum())
            cost = turnover * tc
            current = target.copy()
        else:
            current = drifted

        rows.append((portfolio_return - cost, cost, turnover))

    return pd.DataFrame(rows, index=dates, columns=["ret", "cost", "turnover"])


def equity_curve(returns: pd.Series, initial: float = 1.0) -> pd.Series:
    """Compound a return series from an initial portfolio value."""
    if initial <= 0.0:
        raise ValueError("initial must be positive")
    return initial * (1.0 + returns).cumprod()
