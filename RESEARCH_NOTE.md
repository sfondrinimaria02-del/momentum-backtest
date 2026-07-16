# Cross-Sectional Momentum on Liquid ETFs: Research Design

*Maria Sfondrini — July 2026*

## 1. Research question

Does a simple long-only 12-1 cross-sectional momentum rule improve risk-adjusted
performance relative to an equal-weight ETF benchmark after transaction costs?

The repository treats this as an empirical question, not as a claim that momentum must
outperform in the selected sample.

## 2. Universe and data

The default universe contains 24 US-listed ETFs spanning regional equities, US sectors,
rates, credit, commodities, and real estate:

`SPY, QQQ, IWM, EFA, EEM, VGK, EWJ, FXI, XLF, XLK, XLE, XLV, XLI, XLP, XLU,
XLY, TLT, IEF, LQD, HYG, GLD, SLV, DBC, VNQ`.

Adjusted daily closing prices are downloaded through Yahoo Finance. The loader requires
all requested assets and rejects missing, duplicated, non-finite, non-positive, or empty
observations. Cached datasets are keyed by the exact ticker universe and date range.

Yahoo Finance can revise adjusted historical prices. A defensible reported result should
therefore include the generated metadata file and the Git commit used for the run.

## 3. Signal and portfolio

For each asset, the 12-1 signal is:

```text
price at t-1 month / price at t-12 months - 1
```

The calculation uses the actual final trading observation of each calendar month. Assets
with insufficient history are excluded. The portfolio holds the top signal quintile at
equal weight and is rebalanced monthly.

Parameters such as lookback, transaction costs, and portfolio quantile are validated.
Invalid settings fail explicitly instead of being silently coerced.

## 4. Execution and look-ahead control

A month-end signal cannot be calculated and filled at the same closing price without an
execution assumption. This engine uses a conservative close-only convention:

1. calculate the signal from the last observed close of month `t`;
2. schedule the rebalance for the close of the first trading day after that signal;
3. apply the new weights beginning with the following close-to-close return.

Existing holdings earn the execution day's return before rebalancing. Turnover is measured
against those drifted weights, and transaction costs are charged at the rebalance close.

This convention avoids assigning the previous close-to-close or overnight return to a
portfolio that was not yet tradable. A future engine using open prices could instead model
an explicit next-open fill.

## 5. Fair benchmark and sensitivity comparisons

The equal-weight benchmark uses the same:

- asset universe;
- monthly execution schedule;
- transaction-cost model;
- first investable signal date.

The momentum portfolio is uninvested while its signal warms up. Those zero-return days are
excluded from both strategy and benchmark metrics, preventing unequal market exposure.

When comparing several lookbacks, use the latest first-signal date across all variants as
`start_signal_date`. This puts 6-1, 9-1, and 12-1 results on the same evaluation window.

## 6. Metrics

The project reports CAGR, annualized volatility, Sharpe ratio, Sortino ratio, and maximum
drawdown.

- Sortino uses the root mean square of returns below the minimum acceptable return over
  the full sample.
- Maximum drawdown includes the initial portfolio value, so an immediate loss is captured.
- Empty or non-finite return series are rejected.

## 7. Corrected reference results

Prices were requested from Yahoo Finance on 14 July 2026 and independently reproduced
bit-for-bit against a fresh pull on 16 July 2026. The common evaluation window runs from
1 February 2016 through 31 December 2024. Transaction costs are 10 bps.

| Portfolio | CAGR | Ann. vol | Sharpe | Sortino | Max drawdown |
|---|---:|---:|---:|---:|---:|
| Momentum 12-1, net | 10.0% | 15.6% | 0.69 | 0.96 | −22.9% |
| Momentum 12-1, gross | 10.7% | 15.6% | 0.73 | 1.02 | −22.6% |
| Equal-weight benchmark, net | 9.7% | 13.0% | 0.78 | 1.08 | −27.6% |

Average one-way turnover for 12-1 momentum was 53.0% per monthly rebalance.

Sensitivity was evaluated over the same 1 February 2016 start for every lookback:

| Lookback | CAGR | Sharpe | Max drawdown | Avg. turnover |
|---|---:|---:|---:|---:|
| 6-1 | 7.7% | 0.52 | −34.2% | 72.2% |
| 9-1 | 9.7% | 0.67 | −26.5% | 56.7% |
| 12-1 | 10.0% | 0.69 | −22.9% | 53.0% |

The 12-1 rule has the highest return and shallowest drawdown in this sensitivity set, but
its Sharpe ratio remains below the equal-weight benchmark. The result supports a modest
return/drawdown benefit in this sample, not a strong risk-adjusted edge.

## 8. Interpretation rules

A professional interpretation should separate raw performance from evidence strength:

- Compare strategy and benchmark over identical dates.
- Report net and gross results together with average turnover.
- Avoid treating a small Sharpe difference as economically or statistically decisive.
- Explain how concentration changes volatility and drawdowns.
- Record data, package, and code versions.
- Use robustness checks such as alternative lookbacks and transaction costs.
- Prefer confidence intervals or bootstrap analysis before making inferential claims.

## 9. Limitations and extensions

The long-only portfolio retains market beta and is not equivalent to the academic
long-short momentum factor. The fixed surviving ETF universe embeds hindsight. Linear
costs omit spread variation, market impact, taxes, and capacity. Ten years provide only
about 120 monthly decisions.

Useful extensions include:

- a point-in-time universe and institutional data source;
- a long-short specification with financing and borrow constraints;
- volatility targeting and exposure controls;
- walk-forward or out-of-sample analysis;
- bootstrap confidence intervals;
- explicit open-price execution and slippage;
- parameter stability plots generated from a common evaluation window.

## Reference

Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers:
Implications for stock market efficiency. *The Journal of Finance, 48*(1), 65–91.
