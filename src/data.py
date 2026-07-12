"""Data loading utilities.

Two modes:
  1. `load_prices(tickers, start, end)` — downloads adjusted close prices via
     yfinance and caches them to CSV so repeated runs don't re-download.
  2. `synthetic_prices(...)` — generates a synthetic price panel with
     regime-persistent drifts, used to test the engine without internet access.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data_cache")


def load_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Download (or load cached) daily adjusted close prices, one column per ticker."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"prices_{start}_{end}.csv")
    if os.path.exists(cache_file):
        return pd.read_csv(cache_file, index_col=0, parse_dates=True)

    import yfinance as yf  # imported lazily so the rest works offline

    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    prices = prices.dropna(how="all")
    prices.to_csv(cache_file)
    return prices


def synthetic_prices(
    n_assets: int = 20,
    n_days: int = 2520,  # ~10 years
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic daily prices with slowly-rotating drift regimes.

    Each asset's drift persists for stretches of ~1 year before re-drawing,
    which creates cross-sectional momentum by construction. This is ONLY for
    testing the engine mechanics — results on synthetic data say nothing
    about real markets.
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=n_days)
    regime_len = 252

    drifts = np.zeros((n_days, n_assets))
    for a in range(n_assets):
        d = 0.0
        for start_i in range(0, n_days, regime_len):
            d = rng.normal(0.04, 0.12) / 252  # annualised drift re-drawn each year
            drifts[start_i : start_i + regime_len, a] = d

    vol = rng.uniform(0.15, 0.35, n_assets) / np.sqrt(252)
    shocks = rng.standard_normal((n_days, n_assets)) * vol
    log_prices = np.cumsum(drifts + shocks, axis=0)
    prices = 100 * np.exp(log_prices)

    cols = [f"ASSET_{i:02d}" for i in range(n_assets)]
    return pd.DataFrame(prices, index=dates, columns=cols)


# A reasonable liquid-ETF universe for the real run
DEFAULT_UNIVERSE = [
    "SPY", "QQQ", "IWM", "EFA", "EEM", "VGK", "EWJ", "FXI",
    "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLU", "XLY",
    "TLT", "IEF", "LQD", "HYG", "GLD", "SLV", "DBC", "VNQ",
]
