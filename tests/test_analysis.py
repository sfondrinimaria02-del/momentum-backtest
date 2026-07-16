from momentum_backtest.analysis import analyze
from momentum_backtest.data import synthetic_prices


def test_strategy_and_benchmark_share_the_same_investable_period() -> None:
    prices = synthetic_prices(n_assets=5, n_days=700, seed=3)

    result = analyze(prices, lookback_months=12, tc_bps=10.0, quantile=0.4)

    assert result.momentum.index.equals(result.benchmark.index)
    assert result.momentum.index[0] == result.evaluation_start
    assert result.momentum.iloc[0]["turnover"] == 1.0
    assert result.benchmark.iloc[0]["turnover"] == 1.0
