# Systematic Momentum Strategy — Backtesting Engine

[![CI](https://github.com/sfondrinimaria02-del/momentum-backtest/actions/workflows/ci.yml/badge.svg)](https://github.com/sfondrinimaria02-del/momentum-backtest/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A transparent Python backtesting engine for a classic **12-1 cross-sectional momentum
strategy** on a diversified ETF universe. The project emphasizes reproducible research,
explicit execution assumptions, transaction costs, and tests for common backtesting errors.

*Maria Sfondrini — Master in Finance, Peking University HSBC Business School;
B.Sc. Computer System Engineering, Politecnico di Milano.*

## What the engine models

- **Signal:** trailing 12-month return excluding the most recent month, calculated on the
  actual final trading observation of each calendar month.
- **Portfolio:** equal-weight long allocation to the top quintile of valid signals.
- **Execution:** the signal is scheduled for the close of the first trading session after
  month-end. New weights earn returns from the following close-to-close interval.
- **Weight drift:** holdings move with asset returns between monthly rebalances.
- **Transaction costs:** linear costs are charged on actual one-way turnover,
  `sum(abs(target_weight - drifted_weight))`.
- **Benchmark:** a monthly rebalanced equal-weight portfolio using the same universe,
  cost model, execution convention, and investable start date.

The shared investable start is important: neither the benchmark nor a shorter-lookback
variant receives additional market exposure during another strategy's signal warm-up.

## Reproducing results

Requires Python 3.10 or newer.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python run_backtest.py
python run_backtest.py --synthetic
python run_backtest.py --lookback 6 --tc-bps 10 --quantile 0.2
```

Real-data runs download adjusted closing prices through `yfinance`. Downloads are
validated before use and cached by date range **and exact ticker universe**. An empty,
partial, duplicated, non-finite, or non-positive dataset causes the run to fail rather
than produce misleading output.

Each successful run writes the following ignored artifacts under `results/`:

- a summary CSV;
- an equity-curve PNG;
- a JSON record containing parameters, package versions, universe, and evaluation dates.

## Reference run

Corrected close-only methodology, 10 bps transaction costs, prices requested from Yahoo
Finance on 14 July 2026, common evaluation window 1 February 2016–31 December 2024:

| Portfolio | CAGR | Ann. vol | Sharpe | Sortino | Max drawdown |
|---|---:|---:|---:|---:|---:|
| Momentum 12-1, net | **10.0%** | 15.6% | 0.69 | 0.96 | **−22.9%** |
| Momentum 12-1, gross | 10.7% | 15.6% | 0.73 | 1.02 | −22.6% |
| Equal-weight benchmark, net | 9.7% | **13.0%** | **0.78** | **1.08** | −27.6% |

Average one-way momentum turnover was 53.0% per rebalance. Momentum delivered a slightly
higher net CAGR and a shallower drawdown, but the diversified benchmark had the stronger
risk-adjusted performance. This is not evidence of a robust selection premium.

Historical adjusted prices can be revised. Regenerated claims should therefore be tied
to the output metadata file and a specific Git commit.

## Repository structure

```text
.
├── .github/workflows/ci.yml  # lint and unit tests on Python 3.10 and 3.12
├── src/
│   ├── analysis.py           # aligned strategy/benchmark orchestration
│   ├── backtest.py           # execution, drift, turnover, and transaction costs
│   ├── data.py               # validated yfinance cache and synthetic generator
│   ├── metrics.py            # CAGR, volatility, Sharpe, Sortino, drawdown
│   └── strategy.py           # month-end signals and portfolio construction
├── tests/                    # deterministic offline tests
├── Momentum_Backtest.ipynb   # research workflow using the shared source modules
├── RESEARCH_NOTE.md          # methodology and interpretation framework
└── run_backtest.py           # command-line entry point
```

## Development checks

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

The test suite covers signal timing, actual trading-month ends, portfolio normalization,
rebalance timing, transaction costs, aligned evaluation periods, data validation,
compounding, and drawdown from initial capital. CI has read-only repository permissions.

## Research limitations

- A long-only ETF portfolio is not the academic long-short momentum factor and retains
  substantial market beta.
- The fixed ETF universe mitigates delisting churn but remains selected with hindsight.
- Yahoo Finance is convenient rather than an institutional-grade point-in-time database.
- Linear costs omit market impact, bid-ask variation, taxes, and capacity constraints.
- A ten-year monthly sample is too short to establish a statistically robust edge.
- The engine does not model intraday fills; its close-only execution rule is intentionally
  conservative and explicit.

See [RESEARCH_NOTE.md](RESEARCH_NOTE.md) for the research design and interpretation rules.

## Disclaimer

This repository is an educational research project, not investment advice.

## License

Released under the [MIT License](LICENSE).
