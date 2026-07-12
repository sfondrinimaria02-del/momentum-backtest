# Cross-Sectional Momentum on Liquid ETFs: Does It Survive Transaction Costs?

*Maria Sfondrini — July 2026*
*Master in Finance, Peking University HSBC Business School · B.Sc. Computer System Engineering, Politecnico di Milano*

## 1. Question

Does a simple 12-1 cross-sectional momentum strategy add value over buy-and-hold on a
diversified ETF universe, after realistic transaction costs?

## 2. Data and Method

**Universe.** 24 liquid US-listed ETFs spanning regional equities (SPY, QQQ, IWM, EFA,
EEM, VGK, EWJ, FXI), US sectors (XLF, XLK, XLE, XLV, XLI, XLP, XLU, XLY), rates and
credit (TLT, IEF, LQD, HYG), commodities (GLD, SLV, DBC) and real estate (VNQ).
Daily adjusted closes, January 2015 – December 2024 (2,516 trading days), via Yahoo Finance.

**Signal.** Classic 12-1 momentum: trailing 12-month return excluding the most recent
month, computed on month-end prices. The one-month skip avoids contamination from
short-term reversal (Jegadeesh & Titman, 1993).

**Portfolio.** Equal-weight long the top quintile (5 of 24 assets), rebalanced monthly.
Benchmark: equal-weight buy-and-hold of the same 24 ETFs, rebalanced monthly, same costs.

**Backtest design.** The engine was built from scratch (pandas/numpy) with three explicit
anti-bias choices: (i) signals computed at month-end *t* trade only on the first trading
day after *t* — no look-ahead; (ii) between rebalances, weights drift with returns rather
than being implicitly rebalanced daily; (iii) transaction costs of 10 bps are charged on
actual one-way turnover Σ|w_target − w_drifted|.

## 3. Results

| Strategy | CAGR | Ann. Vol | Sharpe | Sortino | Max DD |
|---|---|---|---|---|---|
| Momentum 12-1 (net, 10 bps) | **9.0%** | 14.7% | **0.66** | 0.81 | −23.3% |
| Momentum 12-1 (gross) | 9.6% | 14.7% | 0.70 | 0.86 | −23.2% |
| Equal-weight benchmark (net) | 7.8% | 12.9% | 0.65 | 0.79 | −27.7% |

Average one-way turnover: **52.9% per monthly rebalance**. Costs consume ~0.6 pp of CAGR
and ~0.04 of Sharpe — material, but not fatal at institutional cost levels.

**Sensitivity to lookback window (net of costs):**

| Lookback | CAGR | Sharpe | Max DD |
|---|---|---|---|
| 6-1 | 5.9% | 0.43 | −33.2% |
| 9-1 | 7.9% | 0.58 | −26.4% |
| 12-1 | 9.0% | 0.66 | −23.3% |

Performance improves monotonically with the lookback horizon on this sample: shorter
windows produce noisier rankings, higher turnover, and deeper drawdowns.

## 4. Interpretation

The strategy beats the benchmark by ~1.2 pp of CAGR with a *smaller* maximum drawdown
(−23.3% vs −27.7%), but at higher volatility (14.7% vs 12.9%) — so the risk-adjusted
edge is modest (Sharpe 0.66 vs 0.65). The honest reading: on this universe and decade,
long-only ETF momentum improved returns and tail behaviour, but most of its Sharpe is
market beta rather than pure selection skill. The concentration effect (5 assets vs 24)
explains the higher volatility.

## 5. Limitations

With ~120 monthly rebalances, the Sharpe difference of 0.01 between strategy and
benchmark is far from statistically significant; my evidence is consistent with the
momentum literature rather than independent proof of it. The long-only top-quintile
construction retains full market beta, unlike the academic long-short factor. Costs are
linear with no slippage model. The ETF universe was chosen ex-post among funds that
survived the full decade, embedding a subtle hindsight bias I flag rather than hide.
With more time I would test the long-short version, add volatility targeting, and
bootstrap confidence intervals on the Sharpe ratio.
