"""Run the momentum backtest.

Usage:
  python run_backtest.py --synthetic          # offline test with synthetic data
  python run_backtest.py                      # real ETF data via yfinance
  python run_backtest.py --lookback 6         # sensitivity: 6-month lookback
"""
from __future__ import annotations

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.data import DEFAULT_UNIVERSE, load_prices, synthetic_prices
from src.strategy import momentum_signal, top_quantile_weights
from src.backtest import run_backtest, equity_curve
from src.metrics import summary_table

RESULTS = os.path.join(os.path.dirname(__file__), "results")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--synthetic", action="store_true", help="use synthetic data (offline)")
    p.add_argument("--start", default="2015-01-01")
    p.add_argument("--end", default="2025-01-01")
    p.add_argument("--lookback", type=int, default=12, help="momentum lookback in months")
    p.add_argument("--tc-bps", type=float, default=10.0, help="transaction cost in basis points")
    p.add_argument("--quantile", type=float, default=0.2, help="top quantile held long")
    args = p.parse_args()

    os.makedirs(RESULTS, exist_ok=True)

    if args.synthetic:
        prices = synthetic_prices()
        tag = "synthetic"
        print("NOTE: synthetic data — engine test only, not real-market evidence.")
    else:
        prices = load_prices(DEFAULT_UNIVERSE, args.start, args.end)
        tag = "real"

    # --- strategy ---
    signal = momentum_signal(prices, lookback_months=args.lookback, skip_months=1)
    weights = top_quantile_weights(signal, quantile=args.quantile)
    bt = run_backtest(prices, weights, tc_bps=args.tc_bps)

    # gross version (no costs) to show cost impact
    bt_gross = run_backtest(prices, weights, tc_bps=0.0)

    # --- benchmark: equal-weight buy & hold, rebalanced monthly ---
    monthly_dates = prices.resample("ME").last().index
    ew = pd.DataFrame(1.0 / prices.shape[1], index=monthly_dates, columns=prices.columns)
    bench = run_backtest(prices, ew, tc_bps=args.tc_bps)

    # --- results ---
    table = summary_table({
        f"Momentum {args.lookback}-1 (net, {args.tc_bps:.0f}bps)": bt["ret"],
        f"Momentum {args.lookback}-1 (gross)": bt_gross["ret"],
        "Equal-weight benchmark (net)": bench["ret"],
    })
    print("\n", table, "\n")
    avg_turnover = bt.loc[bt["turnover"] > 0, "turnover"].mean()
    print(f"Average one-way turnover per rebalance: {avg_turnover:.1%}")
    table.to_csv(os.path.join(RESULTS, f"summary_{tag}_L{args.lookback}.csv"))

    # --- charts ---
    fig, ax = plt.subplots(figsize=(10, 5.5))
    equity_curve(bt["ret"]).plot(ax=ax, label=f"Momentum {args.lookback}-1 (net)")
    equity_curve(bt_gross["ret"]).plot(ax=ax, label="Momentum (gross)", linestyle="--", alpha=0.7)
    equity_curve(bench["ret"]).plot(ax=ax, label="Equal-weight benchmark")
    ax.set_title(f"Cross-sectional momentum vs. benchmark ({tag} data)")
    ax.set_ylabel("Growth of $1")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, f"equity_curve_{tag}_L{args.lookback}.png"), dpi=150)
    print(f"Saved results to {RESULTS}/")


if __name__ == "__main__":
    main()
