"""Performance and risk metrics with explicit input validation."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _validated_returns(returns: pd.Series) -> pd.Series:
    clean = returns.astype(float)
    if clean.empty:
        raise ValueError("returns must not be empty")
    if not np.isfinite(clean.to_numpy()).all():
        raise ValueError("returns must contain only finite values")
    if (clean <= -1.0).any():
        raise ValueError("returns must be greater than -100%")
    return clean


def cagr(returns: pd.Series) -> float:
    clean = _validated_returns(returns)
    total = float((1.0 + clean).prod())
    years = len(clean) / TRADING_DAYS
    return total ** (1.0 / years) - 1.0


def ann_vol(returns: pd.Series) -> float:
    clean = _validated_returns(returns)
    return float(clean.std() * np.sqrt(TRADING_DAYS))


def sharpe(returns: pd.Series, rf_annual: float = 0.0) -> float:
    clean = _validated_returns(returns)
    rf_daily = (1.0 + rf_annual) ** (1.0 / TRADING_DAYS) - 1.0
    excess = clean - rf_daily
    volatility = float(excess.std())
    return float(excess.mean() / volatility * np.sqrt(TRADING_DAYS)) if volatility > 0 else np.nan


def sortino(returns: pd.Series, rf_annual: float = 0.0) -> float:
    clean = _validated_returns(returns)
    rf_daily = (1.0 + rf_annual) ** (1.0 / TRADING_DAYS) - 1.0
    excess = clean - rf_daily
    downside = np.minimum(excess.to_numpy(), 0.0)
    downside_deviation = float(np.sqrt(np.mean(np.square(downside))))
    if downside_deviation == 0.0:
        return np.nan
    return float(excess.mean() / downside_deviation * np.sqrt(TRADING_DAYS))


def max_drawdown(returns: pd.Series) -> float:
    clean = _validated_returns(returns)
    curve = np.concatenate(([1.0], (1.0 + clean).cumprod().to_numpy()))
    peak = np.maximum.accumulate(curve)
    return float(np.min(curve / peak - 1.0))


def summary_table(strategies: dict[str, pd.Series], rf_annual: float = 0.0) -> pd.DataFrame:
    if not strategies:
        raise ValueError("strategies must not be empty")

    rows = {}
    for name, returns in strategies.items():
        rows[name] = {
            "CAGR": cagr(returns),
            "Ann. Vol": ann_vol(returns),
            "Sharpe": sharpe(returns, rf_annual),
            "Sortino": sortino(returns, rf_annual),
            "Max Drawdown": max_drawdown(returns),
        }
    return pd.DataFrame(rows).T.round(3)
