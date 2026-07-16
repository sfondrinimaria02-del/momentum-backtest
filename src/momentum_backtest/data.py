"""Validated market-data loading and deterministic synthetic data."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

CACHE_DIR = Path(__file__).resolve().parent.parent / "data_cache"


def _normalized_tickers(tickers: Sequence[str]) -> list[str]:
    normalized = [str(ticker).strip().upper() for ticker in tickers]
    if not normalized or any(not ticker for ticker in normalized):
        raise ValueError("tickers must contain at least one non-empty symbol")
    if len(normalized) != len(set(normalized)):
        raise ValueError("tickers must be unique")
    return normalized


def _validate_prices(prices: pd.DataFrame, tickers: Sequence[str]) -> pd.DataFrame:
    expected = _normalized_tickers(tickers)
    if prices.empty:
        raise ValueError("the data source returned no price observations")

    clean = prices.copy()
    clean.columns = [str(column).strip().upper() for column in clean.columns]
    missing_columns = sorted(set(expected) - set(clean.columns))
    unexpected_columns = sorted(set(clean.columns) - set(expected))
    if missing_columns or unexpected_columns:
        raise ValueError(
            "price columns do not match the requested universe; "
            f"missing={missing_columns}, unexpected={unexpected_columns}"
        )

    clean = clean.reindex(columns=expected)
    if not isinstance(clean.index, pd.DatetimeIndex):
        clean.index = pd.to_datetime(clean.index, errors="raise")
    if clean.index.tz is not None:
        clean.index = clean.index.tz_localize(None)
    clean = clean.sort_index()
    if not clean.index.is_unique:
        raise ValueError("price dates must be unique")

    clean = clean.apply(pd.to_numeric, errors="raise").astype(float)
    if clean.isna().to_numpy().any():
        missing = clean.isna().sum()
        details = {column: int(count) for column, count in missing.items() if count}
        raise ValueError(f"prices contain missing observations: {details}")
    if not np.isfinite(clean.to_numpy()).all():
        raise ValueError("prices contain non-finite values")
    if (clean <= 0.0).to_numpy().any():
        raise ValueError("prices must be strictly positive")
    if len(clean) < 2:
        raise ValueError("at least two price observations are required")
    return clean


def _cache_path(tickers: Sequence[str], start: str, end: str) -> Path:
    normalized = _normalized_tickers(tickers)
    start_date = pd.Timestamp(start).date().isoformat()
    end_date = pd.Timestamp(end).date().isoformat()
    digest = hashlib.sha256(",".join(sorted(normalized)).encode()).hexdigest()[:12]
    return CACHE_DIR / f"prices_{start_date}_{end_date}_{digest}.csv"


def load_prices(tickers: Sequence[str], start: str, end: str) -> pd.DataFrame:
    """Download adjusted closes or load a validated, universe-specific cache."""
    normalized = _normalized_tickers(tickers)
    if pd.Timestamp(start) >= pd.Timestamp(end):
        raise ValueError("start must be earlier than end")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(normalized, start, end)
    if cache_file.exists():
        try:
            cached = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            return _validate_prices(cached, normalized)
        except (OSError, TypeError, ValueError):
            cache_file.unlink(missing_ok=True)

    import yfinance as yf

    yf.set_tz_cache_location(str(CACHE_DIR / ".yfinance"))
    raw = yf.download(
        normalized,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    # yfinance returns (Price, Ticker) MultiIndex columns even for a single-ticker
    # list request (verified empirically against yfinance 1.5.x) - the flat-column
    # branch below is a defensive fallback in case a different yfinance version
    # ever collapses to a plain Index for a single ticker.
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" not in raw.columns.get_level_values(0):
            raise ValueError("the data source response does not contain adjusted close prices")
        prices = raw.xs("Close", axis=1, level=0)
    else:
        if "Close" not in raw.columns or len(normalized) != 1:
            raise ValueError("the data source response has an unexpected column layout")
        prices = raw[["Close"]].rename(columns={"Close": normalized[0]})

    clean = _validate_prices(prices, normalized)
    temporary = cache_file.with_suffix(cache_file.suffix + ".tmp")
    try:
        clean.to_csv(temporary)
        temporary.replace(cache_file)
    finally:
        temporary.unlink(missing_ok=True)
    return clean


def synthetic_prices(
    n_assets: int = 20,
    n_days: int = 2520,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate positive prices with persistent, deterministic drift regimes."""
    if n_assets <= 0 or n_days <= 1:
        raise ValueError("n_assets must be positive and n_days must be greater than one")

    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=n_days)
    regime_len = 252

    drifts = np.zeros((n_days, n_assets))
    for asset in range(n_assets):
        for start_i in range(0, n_days, regime_len):
            drift = rng.normal(0.04, 0.12) / 252
            drifts[start_i : start_i + regime_len, asset] = drift

    vol = rng.uniform(0.15, 0.35, n_assets) / np.sqrt(252)
    shocks = rng.standard_normal((n_days, n_assets)) * vol
    prices = 100 * np.exp(np.cumsum(drifts + shocks, axis=0))

    columns = [f"ASSET_{index:02d}" for index in range(n_assets)]
    return pd.DataFrame(prices, index=dates, columns=columns)


DEFAULT_UNIVERSE = [
    "SPY",
    "QQQ",
    "IWM",
    "EFA",
    "EEM",
    "VGK",
    "EWJ",
    "FXI",
    "XLF",
    "XLK",
    "XLE",
    "XLV",
    "XLI",
    "XLP",
    "XLU",
    "XLY",
    "TLT",
    "IEF",
    "LQD",
    "HYG",
    "GLD",
    "SLV",
    "DBC",
    "VNQ",
]
