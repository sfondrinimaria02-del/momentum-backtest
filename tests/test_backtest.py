import pandas as pd
import pytest

from momentum_backtest.backtest import equity_curve, run_backtest


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


def test_equity_curve_rejects_non_positive_initial_value() -> None:
    with pytest.raises(ValueError, match="initial"):
        equity_curve(pd.Series([0.1]), initial=0.0)


@pytest.mark.parametrize(
    ("prices", "targets", "tc_bps", "match"),
    [
        (
            pd.DataFrame({"A": [100.0]}, index=pd.to_datetime(["2024-01-01"])),
            pd.DataFrame({"A": [1.0]}, index=pd.to_datetime(["2024-01-01"])),
            -1.0,
            "tc_bps",
        ),
        (
            pd.DataFrame({"A": []}, dtype=float),
            pd.DataFrame({"A": [1.0]}, index=pd.to_datetime(["2024-01-01"])),
            10.0,
            "prices must not be empty",
        ),
        (
            pd.DataFrame({"A": [100.0]}, index=[0]),
            pd.DataFrame({"A": [1.0]}, index=pd.to_datetime(["2024-01-01"])),
            10.0,
            "DatetimeIndex",
        ),
        (
            pd.DataFrame({"A": [100.0, 100.0]}, index=pd.to_datetime(["2024-01-02", "2024-01-01"])),
            pd.DataFrame({"A": [1.0]}, index=pd.to_datetime(["2024-01-01"])),
            10.0,
            "sorted and unique",
        ),
        (
            pd.DataFrame({"A": [100.0]}, index=pd.to_datetime(["2024-01-01"])),
            pd.DataFrame({"B": [1.0]}, index=pd.to_datetime(["2024-01-01"])),
            10.0,
            "columns must exactly match",
        ),
        (
            pd.DataFrame({"A": [float("inf")]}, index=pd.to_datetime(["2024-01-01"])),
            pd.DataFrame({"A": [1.0]}, index=pd.to_datetime(["2024-01-01"])),
            10.0,
            "finite",
        ),
        (
            pd.DataFrame({"A": [-1.0]}, index=pd.to_datetime(["2024-01-01"])),
            pd.DataFrame({"A": [1.0]}, index=pd.to_datetime(["2024-01-01"])),
            10.0,
            "strictly positive",
        ),
        (
            pd.DataFrame({"A": [100.0]}, index=pd.to_datetime(["2024-01-01"])),
            pd.DataFrame({"A": [-1.0]}, index=pd.to_datetime(["2024-01-01"])),
            10.0,
            "long-only",
        ),
    ],
)
def test_run_backtest_rejects_invalid_inputs(prices, targets, tc_bps, match) -> None:
    with pytest.raises((ValueError, TypeError), match=match):
        run_backtest(prices, targets, tc_bps=tc_bps)
