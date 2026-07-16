import numpy as np
import pandas as pd
import pytest

from momentum_backtest.strategy import momentum_signal, month_end_prices, top_quantile_weights


def test_month_end_prices_rejects_empty_frame() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        month_end_prices(pd.DataFrame())


def test_month_end_prices_rejects_non_datetime_index() -> None:
    prices = pd.DataFrame({"A": [100.0]}, index=[0])
    with pytest.raises(TypeError, match="DatetimeIndex"):
        month_end_prices(prices)


def test_month_end_prices_rejects_unsorted_index() -> None:
    dates = pd.to_datetime(["2024-01-31", "2024-01-15"])
    prices = pd.DataFrame({"A": [1.0, 2.0]}, index=dates)
    with pytest.raises(ValueError, match="sorted and unique"):
        month_end_prices(prices)


@pytest.mark.parametrize(
    ("lookback_months", "skip_months", "match"),
    [
        (0, 1, "lookback_months must be positive"),
        (12, -1, "skip_months"),
        (12, 12, "skip_months"),
    ],
)
def test_momentum_signal_rejects_invalid_windows(lookback_months, skip_months, match) -> None:
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"A": [1.0, 2.0, 3.0]}, index=dates)
    with pytest.raises(ValueError, match=match):
        momentum_signal(prices, lookback_months=lookback_months, skip_months=skip_months)


@pytest.mark.parametrize("quantile", [0.0, -0.1, 1.1])
def test_top_quantile_weights_rejects_out_of_range_quantile(quantile) -> None:
    signal = pd.DataFrame([[1.0]], index=[pd.Timestamp("2024-01-31")], columns=["A"])
    with pytest.raises(ValueError, match="quantile"):
        top_quantile_weights(signal, quantile=quantile)


def test_top_quantile_weights_handles_a_date_with_no_valid_signal() -> None:
    signal = pd.DataFrame(
        [[np.nan, np.nan]],
        index=[pd.Timestamp("2024-01-31")],
        columns=["A", "B"],
    )

    weights = top_quantile_weights(signal, quantile=0.5)

    assert (weights == 0.0).all().all()


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
