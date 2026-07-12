# Systematic Momentum Strategy — Backtesting Engine

A vectorized backtesting engine built from scratch in Python (pandas/numpy), used to
evaluate a classic **12-1 cross-sectional momentum strategy** on a universe of 24 liquid
ETFs over 10 years, net of transaction costs.

*Author: Maria Sfondrini — Master in Finance, Peking University HSBC Business School;
B.Sc. Computer System Engineering, Politecnico di Milano.*

## Why build the engine from scratch?

Off-the-shelf backtesters hide the decisions that matter. Building the engine myself
forced me to handle explicitly:

- **Look-ahead bias** — signals computed at month-end *t* are only traded on the first
  trading day after *t*.
- **Weight drift** — between rebalances, holdings drift with returns instead of being
  implicitly rebalanced daily (a subtle bug in many naive backtests).
- **Transaction costs** — charged on actual turnover `Σ|w_new − w_drifted|`, so the
  cost of the strategy's ~50% monthly one-way turnover is measured, not assumed away.

## Strategy

- **Signal:** 12-1 momentum — trailing 12-month return excluding the most recent month
  (to avoid short-term reversal), computed on month-end prices.
- **Portfolio:** equal-weight long the top quintile; monthly rebalance.
- **Universe:** 24 liquid ETFs across equities (regional + sector), rates, credit,
  commodities and real estate.
- **Benchmark:** equal-weight buy-and-hold of the same universe, same costs.

## Results (real data, 2015–2024)

| Strategy | CAGR | Ann. Vol | Sharpe | Sortino | Max DD |
|---|---|---|---|---|---|
| Momentum 12-1 (net, 10 bps) | **9.0%** | 14.7% | **0.66** | 0.81 | −23.3% |
| Momentum 12-1 (gross) | 9.6% | 14.7% | 0.70 | 0.86 | −23.2% |
| Equal-weight benchmark (net) | 7.8% | 12.9% | 0.65 | 0.79 | −27.7% |

Average one-way turnover: 52.9% per monthly rebalance. Sensitivity: performance
improves monotonically with lookback (6-1: Sharpe 0.43 → 9-1: 0.58 → 12-1: 0.66).
Full analysis and honest interpretation in [RESEARCH_NOTE.md](RESEARCH_NOTE.md).

Run `python run_backtest.py` to reproduce (downloads data via yfinance, cached).

## Honest limitations

- Long-only top-quintile on ETFs is a blunt version of the academic long-short factor;
  results are driven partly by beta, not pure momentum.
- No slippage model beyond linear costs; no borrow constraints tested.
- Survivorship is mitigated (ETF universe fixed ex-ante) but the universe choice itself
  embeds hindsight.
- 10 years is a short sample for a monthly-rebalanced strategy (~120 independent bets).

## Structure

```
src/data.py       # yfinance loader with CSV cache + synthetic generator for offline tests
src/strategy.py   # momentum signal and portfolio construction
src/backtest.py   # vectorized engine: rebalancing, weight drift, transaction costs
src/metrics.py    # CAGR, Sharpe, Sortino, max drawdown, summary table
run_backtest.py   # CLI entry point
```

## Setup

```bash
pip install -r requirements.txt
python run_backtest.py              # real data (downloads via yfinance, cached)
python run_backtest.py --synthetic  # offline engine test
```
