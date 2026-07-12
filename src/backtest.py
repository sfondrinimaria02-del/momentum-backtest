"""Vectorized backtesting engine with transaction costs.

The engine takes daily prices and a panel of target weights (indexed by
rebalance dates) and produces daily portfolio returns net of costs.

Key design choices (worth explaining in interviews):
  * Weights decided at month-end t are applied from the FIRST trading day
    after t (no look-ahead bias).
  * Between rebalances, weights drift with asset returns (buy-and-hold drift)
    rather than being implicitly rebalanced daily.
  * Transaction costs are charged on turnover: cost = tc_bps * sum(|w_new - w_drifted|).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def run_backtest(
    prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    tc_bps: float = 10.0,
) -> pd.DataFrame:
    """Returns a DataFrame with daily strategy returns, costs and turnover."""
    daily_ret = prices.pct_change().fillna(0.0)
    tc = tc_bps / 1e4

    dates = daily_ret.index
    cols = prices.columns
    w_current = pd.Series(0.0, index=cols)  # holdings weights, drifting daily

    # Map each rebalance date to the first trading day strictly after it
    rebal_dates = {}
    for rd in target_weights.index:
        nxt = dates[dates > rd]
        if len(nxt):
            rebal_dates[nxt[0]] = rd

    out = pd.DataFrame(index=dates, columns=["ret", "cost", "turnover"], dtype=float)

    for d in dates:
        # 1. rebalance at the open of day d if scheduled (cost charged on day d)
        cost = 0.0
        turnover = 0.0
        if d in rebal_dates:
            w_target = target_weights.loc[rebal_dates[d]].fillna(0.0)
            turnover = float((w_target - w_current).abs().sum())
            cost = turnover * tc
            w_current = w_target.copy()

        # 2. earn the day's return on current holdings
        r = float((w_current * daily_ret.loc[d]).sum()) - cost
        out.loc[d] = [r, cost, turnover]

        # 3. drift weights with returns
        gross = w_current * (1.0 + daily_ret.loc[d])
        total = gross.sum()
        w_current = gross / total if total > 0 else gross

    return out


def equity_curve(returns: pd.Series, initial: float = 1.0) -> pd.Series:
    return initial * (1.0 + returns).cumprod()
