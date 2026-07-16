"""Command-line entry point for the momentum backtest."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from momentum_backtest.analysis import analyze
from momentum_backtest.backtest import equity_curve
from momentum_backtest.data import DEFAULT_UNIVERSE, load_prices, synthetic_prices

RESULTS = Path("results")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true", help="use deterministic offline data")
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2025-01-01")
    parser.add_argument("--lookback", type=int, default=12, help="momentum lookback in months")
    parser.add_argument(
        "--tc-bps", type=float, default=10.0, help="transaction cost in basis points"
    )
    parser.add_argument("--quantile", type=float, default=0.2, help="top quantile held long")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if pd.Timestamp(args.start) >= pd.Timestamp(args.end):
        raise SystemExit("--start must be earlier than --end")

    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.synthetic:
        prices = synthetic_prices()
        tag = "synthetic"
        print("NOTE: synthetic data — engine test only, not real-market evidence.")
    else:
        prices = load_prices(DEFAULT_UNIVERSE, args.start, args.end)
        tag = "real"

    result = analyze(
        prices,
        lookback_months=args.lookback,
        tc_bps=args.tc_bps,
        quantile=args.quantile,
    )

    print(f"Evaluation starts at the rebalance close on {result.evaluation_start.date()}.")
    print("\n", result.summary, "\n")
    print(f"Average one-way turnover per rebalance: {result.average_turnover:.1%}")

    stem = f"{tag}_L{args.lookback}"
    result.summary.to_csv(RESULTS / f"summary_{stem}.csv", index_label="Strategy")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    equity_curve(result.momentum["ret"]).plot(
        ax=ax,
        label=f"Momentum {args.lookback}-1 (net)",
    )
    equity_curve(result.gross["ret"]).plot(
        ax=ax,
        label="Momentum (gross)",
        linestyle="--",
        alpha=0.7,
    )
    equity_curve(result.benchmark["ret"]).plot(ax=ax, label="Equal-weight benchmark")
    ax.set_title(f"Cross-sectional momentum vs. benchmark ({tag} data)")
    ax.set_ylabel("Growth of $1")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / f"equity_curve_{stem}.png", dpi=150)
    plt.close(fig)

    metadata = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "pandas": version("pandas"),
        "numpy": version("numpy"),
        "yfinance": version("yfinance"),
        "universe": list(prices.columns),
        "start": str(prices.index.min().date()),
        "end": str(prices.index.max().date()),
        "lookback_months": args.lookback,
        "transaction_cost_bps": args.tc_bps,
        "quantile": args.quantile,
        "evaluation_start": str(result.evaluation_start.date()),
    }
    (RESULTS / f"metadata_{stem}.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved results and run metadata to {RESULTS}/")


if __name__ == "__main__":
    main()
