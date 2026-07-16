import pandas as pd
import pytest

from momentum_backtest.metrics import cagr, max_drawdown


def test_cagr_for_one_trading_year() -> None:
    daily_return = 1.1 ** (1 / 252) - 1
    returns = pd.Series([daily_return] * 252)

    assert cagr(returns) == pytest.approx(0.1)


def test_max_drawdown() -> None:
    returns = pd.Series([0.1, -0.2, 0.1])

    assert max_drawdown(returns) == pytest.approx(-0.2)


def test_max_drawdown_includes_initial_capital() -> None:
    returns = pd.Series([-0.2, 0.1])

    assert max_drawdown(returns) == pytest.approx(-0.2)
