"""Shared experiment orchestration for the CLI and research notebook."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.backtest import run_backtest
from src.metrics import summary_table
from src.strategy import momentum_signal, month_end_prices, top_quantile_weights


@dataclass(frozen=True)
class AnalysisResult:
    """Aligned strategy and benchmark results for a single specification."""

    momentum: pd.DataFrame
    gross: pd.DataFrame
    benchmark: pd.DataFrame
    summary: pd.DataFrame
    evaluation_start: pd.Timestamp
    signal_start: pd.Timestamp
    average_turnover: float


def investable_signal_date(
    prices: pd.DataFrame,
    lookback_months: int,
    quantile: float,
) -> pd.Timestamp:
    """Return the first month-end with a fully formed, invested target."""
    signal = momentum_signal(prices, lookback_months=lookback_months, skip_months=1)
    weights = top_quantile_weights(signal, quantile=quantile)
    invested = weights.abs().sum(axis=1) > 0.0
    if not invested.any():
        raise ValueError("not enough price history to form the requested momentum signal")
    return pd.Timestamp(weights.index[invested][0])


def analyze(
    prices: pd.DataFrame,
    lookback_months: int = 12,
    tc_bps: float = 10.0,
    quantile: float = 0.2,
    start_signal_date: pd.Timestamp | None = None,
) -> AnalysisResult:
    """Run momentum and benchmark over the same investable period.

    ``start_signal_date`` supports fair sensitivity comparisons: pass the
    latest first-signal date among all tested specifications.
    """
    signal = momentum_signal(prices, lookback_months=lookback_months, skip_months=1)
    weights = top_quantile_weights(signal, quantile=quantile)

    first_signal = investable_signal_date(prices, lookback_months, quantile)
    requested_start = pd.Timestamp(start_signal_date) if start_signal_date is not None else first_signal
    eligible = weights.loc[weights.index >= requested_start]
    invested = eligible.abs().sum(axis=1) > 0.0
    if not invested.any():
        raise ValueError("start_signal_date leaves no investable target weights")
    signal_start = pd.Timestamp(eligible.index[invested][0])
    weights = weights.loc[weights.index >= signal_start]

    execution_position = prices.index.searchsorted(signal_start, side="right")
    if execution_position >= len(prices.index):
        raise ValueError("no trading session exists after the first investable signal")
    evaluation_start = pd.Timestamp(prices.index[execution_position])

    momentum = run_backtest(prices, weights, tc_bps=tc_bps).loc[evaluation_start:]
    gross = run_backtest(prices, weights, tc_bps=0.0).loc[evaluation_start:]

    benchmark_dates = month_end_prices(prices).index
    benchmark_weights = pd.DataFrame(
        1.0 / prices.shape[1],
        index=benchmark_dates,
        columns=prices.columns,
    ).loc[signal_start:]
    benchmark = run_backtest(prices, benchmark_weights, tc_bps=tc_bps).loc[evaluation_start:]

    summary = summary_table(
        {
            f"Momentum {lookback_months}-1 (net, {tc_bps:.0f}bps)": momentum["ret"],
            f"Momentum {lookback_months}-1 (gross)": gross["ret"],
            "Equal-weight benchmark (net)": benchmark["ret"],
        }
    )
    turnover = momentum.loc[momentum["turnover"] > 0.0, "turnover"]
    average_turnover = float(turnover.mean()) if not turnover.empty else 0.0

    return AnalysisResult(
        momentum=momentum,
        gross=gross,
        benchmark=benchmark,
        summary=summary,
        evaluation_start=evaluation_start,
        signal_start=signal_start,
        average_turnover=average_turnover,
    )
