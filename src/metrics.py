"""Performance and risk metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def cagr(returns: pd.Series) -> float:
    total = (1 + returns).prod()
    years = len(returns) / TRADING_DAYS
    return total ** (1 / years) - 1 if years > 0 else np.nan


def ann_vol(returns: pd.Series) -> float:
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe(returns: pd.Series, rf_annual: float = 0.0) -> float:
    rf_daily = (1 + rf_annual) ** (1 / TRADING_DAYS) - 1
    excess = returns - rf_daily
    return excess.mean() / excess.std() * np.sqrt(TRADING_DAYS) if excess.std() > 0 else np.nan


def sortino(returns: pd.Series, rf_annual: float = 0.0) -> float:
    rf_daily = (1 + rf_annual) ** (1 / TRADING_DAYS) - 1
    excess = returns - rf_daily
    downside = excess[excess < 0].std()
    return excess.mean() / downside * np.sqrt(TRADING_DAYS) if downside and downside > 0 else np.nan


def max_drawdown(returns: pd.Series) -> float:
    curve = (1 + returns).cumprod()
    peak = curve.cummax()
    return float((curve / peak - 1).min())


def summary_table(strategies: dict[str, pd.Series], rf_annual: float = 0.0) -> pd.DataFrame:
    rows = {}
    for name, rets in strategies.items():
        rows[name] = {
            "CAGR": cagr(rets),
            "Ann. Vol": ann_vol(rets),
            "Sharpe": sharpe(rets, rf_annual),
            "Sortino": sortino(rets, rf_annual),
            "Max Drawdown": max_drawdown(rets),
        }
    return pd.DataFrame(rows).T.round(3)
