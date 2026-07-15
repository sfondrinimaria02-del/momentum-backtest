import numpy as np
import pandas as pd

from src.strategy import momentum_signal, month_end_prices, top_quantile_weights


def test_momentum_signal_uses_only_prior_months() -> None:
    dates = pd.date_range("2020-01-31", periods=14, freq="ME")
    prices = pd.DataFrame({"A": np.arange(1.0, 15.0)}, index=dates)

    signal = momentum_signal(prices, lookback_months=12, skip_months=1)

    assert signal.loc[dates[12], "A"] == 12.0 / 1.0 - 1.0


def test_top_quantile_weights_are_equal_and_normalized() -> None:
    signal = pd.DataFrame(
        [[1.0, 4.0, 3.0, 2.0, np.nan]],
        index=[pd.Timestamp("2024-01-31")],
        columns=list("ABCDE"),
    )

    weights = top_quantile_weights(signal, quantile=0.5).iloc[0]

    assert weights.sum() == 1.0
    assert weights["B"] == 0.5
    assert weights["C"] == 0.5
    assert weights.drop(["B", "C"]).eq(0.0).all()


def test_month_end_prices_preserve_actual_trading_dates() -> None:
    dates = pd.to_datetime(["2024-03-28", "2024-04-01", "2024-04-30"])
    prices = pd.DataFrame({"A": [100.0, 101.0, 102.0]}, index=dates)

    monthly = month_end_prices(prices)

    assert monthly.index.tolist() == [dates[0], dates[2]]
