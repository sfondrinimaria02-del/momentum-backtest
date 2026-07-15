import pandas as pd
import pytest

from src.backtest import equity_curve, run_backtest


def test_rebalance_occurs_after_signal_date_and_charges_cost() -> None:
    dates = pd.to_datetime(["2024-01-31", "2024-02-01", "2024-02-02"])
    prices = pd.DataFrame({"A": [100.0, 110.0, 121.0]}, index=dates)
    targets = pd.DataFrame({"A": [1.0]}, index=[dates[0]])

    result = run_backtest(prices, targets, tc_bps=10.0)

    assert result.loc[dates[0], "ret"] == 0.0
    assert result.loc[dates[1], "turnover"] == 1.0
    assert result.loc[dates[1], "cost"] == pytest.approx(0.001)
    assert result.loc[dates[1], "ret"] == pytest.approx(-0.001)
    assert result.loc[dates[2], "ret"] == pytest.approx(0.1)


def test_invalid_target_weight_sum_is_rejected() -> None:
    dates = pd.to_datetime(["2024-01-31", "2024-02-01"])
    prices = pd.DataFrame({"A": [100.0, 101.0]}, index=dates)
    targets = pd.DataFrame({"A": [0.5]}, index=[dates[0]])

    with pytest.raises(ValueError, match="sum"):
        run_backtest(prices, targets)


def test_equity_curve_compounds_returns() -> None:
    returns = pd.Series([0.1, -0.1])

    curve = equity_curve(returns, initial=100.0)

    assert curve.tolist() == pytest.approx([110.0, 99.0])
