"""scripts/backtest_mean_reversion_grid_asx200.py -- WP-SIGNAL-MEAN-REVERSION-ZSCORE-V2.

V1 spec (bfbae14) re-run verbatim on ASX 200 filtered to mature listings
(>= MIN_HISTORY_PRE_CUTOFF rows of price history pre-2024-07-01).

V1 was 10 ASX blue chips. V2 is the only variable changed: the universe.
Same signal function (mean_reversion_zscore_signal), same engine
(run_backtest), same 6-combo grid, same mean-touch exit (z >= 0), same
60/40 holdout at 2024-07-01 (train_mask uses <=, inclusive of cutoff),
same long-only V1 constraint, same $10k/ticker capital, same costs
(0.1% brokerage per side + $0.01/share slippage), same winner selection
(aggregate TRAIN Sharpe, test REPORTED as held-out validation, never
optimised over).

Universe source: src.data.universe.ASX_200 (200 tickers, shipped in
WP-DATA-UNIVERSE-ASX200, 2146b34). Survivor filter excludes tickers
with insufficient pre-cutoff history (zero-row orphans + recent IPOs);
expected to leave ~185 survivors based on session-7 Phase A probe.

Locked decisions (carried from V1 / session-6 chat, unchanged):
- 6 (window, threshold) combos centered on classic Bollinger (20, 2.0).
- Holdout cutoff 2024-07-01 with train-includes-cutoff convention.
- Aggregate-only optimisation on TRAIN Sharpe; tiebreak avg train
  total return. Test metrics REPORTED for the winner as held-out
  validation, not used for selection (test-set leakage guardrail).
- Costs + capital + B&H baseline: engine defaults, unchanged from
  V1/V2/V3.
- Stdout ASCII-only per CLAUDE.md item 8.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.backtest.engine import (
    BROKERAGE_PCT,
    SLIPPAGE_PER_SHARE,
    STARTING_CAPITAL,
    run_backtest,
)
from src.backtest.signals import mean_reversion_zscore_signal
from src.data.universe import ASX_200
from src.data.yfinance_utils import fetch_prices_full


REGIME_TICKER_EXCLUDE = "^AXJO"
HOLDOUT_CUTOFF = pd.Timestamp("2024-07-01")
MIN_HISTORY_PRE_CUTOFF = 504  # roughly 2 years of trading days
PARAM_GRID: list[tuple[int, float]] = [
    (10, 2.0),
    (20, 1.5),
    (20, 2.0),
    (20, 2.5),
    (30, 2.0),
    (50, 2.0),
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"


# ----- Output helpers (ASCII only) -----

def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v * 100:+.2f}%"


def _fmt_sharpe(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.3f}"


# ----- Aggregation (verbatim from V1) -----

def aggregate_window(window_results: dict[str, dict]) -> dict:
    """Aggregate per-ticker results for one window (train or test)."""
    n = len(window_results)
    metrics = [r["metrics"] for r in window_results.values()]
    bh = [r["bh_metrics"] for r in window_results.values()]

    avg_total_return = sum(m["total_return_pct"] for m in metrics) / n
    sharpes = [m["sharpe"] for m in metrics if not pd.isna(m["sharpe"])]
    avg_sharpe = float(np.mean(sharpes)) if sharpes else float("nan")
    bh_sharpes = [b["sharpe"] for b in bh if not pd.isna(b["sharpe"])]
    avg_bh_sharpe = float(np.mean(bh_sharpes)) if bh_sharpes else float("nan")
    avg_alpha = sum(
        m["total_return_pct"] - b["total_return_pct"]
        for m, b in zip(metrics, bh)
    ) / n
    total_entries = sum(m["n_trades"] for m in metrics)
    num_beating_bh = sum(
        1 for m, b in zip(metrics, bh)
        if m["total_return_pct"] > b["total_return_pct"]
    )
    return {
        "avg_total_return": avg_total_return,
        "avg_sharpe": avg_sharpe,
        "avg_bh_sharpe": avg_bh_sharpe,
        "avg_alpha_over_bh": avg_alpha,
        "total_entries": total_entries,
        "num_beating_bh": num_beating_bh,
    }


# ----- Survivor filter (delta vs V1: replaces stocks-table sweep) -----

def survivor_filter(client, candidates: list[str]) -> tuple[list[str], list[tuple[str, int]]]:
    """Return (survivors, excluded) per >= MIN_HISTORY_PRE_CUTOFF rule.

    survivors: tickers with >= MIN_HISTORY_PRE_CUTOFF rows where
    trade_date <= HOLDOUT_CUTOFF, sorted ascending.
    excluded: [(ticker, count), ...] sorted by count then ticker.
    """
    cutoff_iso = HOLDOUT_CUTOFF.date().isoformat()
    survivors: list[str] = []
    excluded: list[tuple[str, int]] = []
    for t in candidates:
        r = (
            client.table("prices")
            .select("ticker", count="exact")
            .eq("ticker", t)
            .lte("trade_date", cutoff_iso)
            .limit(0)
            .execute()
        )
        if r.count >= MIN_HISTORY_PRE_CUTOFF:
            survivors.append(t)
        else:
            excluded.append((t, r.count))
    return sorted(survivors), sorted(excluded, key=lambda x: (x[1], x[0]))


# ----- Main -----

def main() -> int:
    load_dotenv()
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

    candidates = [t for t in ASX_200 if t != REGIME_TICKER_EXCLUDE]
    print(
        f"Universe source: src.data.universe.ASX_200 "
        f"({len(candidates)} candidates after ^AXJO exclusion)"
    )
    print(
        f"Survivor filter: >= {MIN_HISTORY_PRE_CUTOFF} rows where "
        f"trade_date <= {HOLDOUT_CUTOFF.strftime('%Y-%m-%d')}"
    )
    tickers, excluded = survivor_filter(client, candidates)
    print(f"  Survivors: {len(tickers)}")
    print(f"  Excluded ({len(excluded)} tickers):")
    for t, n in excluded:
        print(f"    {t:<10}  {n:>4} rows")
    print()
    print(f"Param grid (window, threshold): {PARAM_GRID}")
    print(
        f"Holdout cutoff: {HOLDOUT_CUTOFF.strftime('%Y-%m-%d')} "
        f"(train <= cutoff, test > cutoff)"
    )
    print(
        f"Capital: ${STARTING_CAPITAL:,.0f} per ticker. "
        f"Brokerage: {BROKERAGE_PCT * 100}%/side. "
        f"Slippage: ${SLIPPAGE_PER_SHARE}/share/side."
    )
    print()

    print("Prefetching prices...")
    prices_cache: dict[str, pd.DataFrame] = {}
    for t in tickers:
        records = fetch_prices_full(client, t)
        df = pd.DataFrame(records)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df["adj_close"] = pd.to_numeric(df["adj_close"])
        df = df.sort_values("trade_date").reset_index(drop=True)
        prices_cache[t] = df
    n_rows_total = sum(len(d) for d in prices_cache.values())
    print(f"  Cached {n_rows_total} rows across {len(tickers)} tickers.")
    print()

    # Grid sweep: per combo, per ticker, two sims (train + test); aggregate.
    grid_summary: dict[tuple[int, float], dict] = {}
    per_ticker_winner_inputs: dict[tuple[int, float], dict[str, dict]] = {}

    for window, threshold in PARAM_GRID:
        train_results: dict[str, dict] = {}
        test_results: dict[str, dict] = {}
        per_ticker_winner_inputs[(window, threshold)] = {}

        for t in tickers:
            df = prices_cache[t]
            signal = mean_reversion_zscore_signal(
                df, window=window, threshold=threshold
            )
            mask_train = df["trade_date"] <= HOLDOUT_CUTOFF

            train_df = df[mask_train].reset_index(drop=True)
            test_df = df[~mask_train].reset_index(drop=True)
            train_signal = signal[mask_train].reset_index(drop=True)
            test_signal = signal[~mask_train].reset_index(drop=True)

            tr = run_backtest(t, train_df, train_signal)
            te = run_backtest(t, test_df, test_signal)
            train_results[t] = tr
            test_results[t] = te
            per_ticker_winner_inputs[(window, threshold)][t] = {
                "train_sharpe": tr["metrics"]["sharpe"],
                "test_sharpe": te["metrics"]["sharpe"],
            }

        grid_summary[(window, threshold)] = {
            "train": aggregate_window(train_results),
            "test": aggregate_window(test_results),
        }

    # Winner: highest aggregate TRAIN Sharpe; tiebreak avg train total return.
    # Test metrics REPORTED but NOT used for selection (avoid test-set leakage).
    def winner_key(combo):
        agg = grid_summary[combo]["train"]
        sharpe = agg["avg_sharpe"]
        if pd.isna(sharpe):
            sharpe = float("-inf")
        return (sharpe, agg["avg_total_return"])

    winner = max(PARAM_GRID, key=winner_key)
    w_window, w_threshold = winner

    print("==== GRID HONESTY TABLE (aggregate train + test per combo) ====")
    print(
        f"  {'combo':<12} "
        f"{'tr Sh':<8} {'te Sh':<8} "
        f"{'tr alpha':<10} {'te alpha':<10} "
        f"{'tr ent':<7} {'te ent':<7} "
        f"{'bh tr Sh':<10} {'bh te Sh':<10}"
    )
    for combo in PARAM_GRID:
        s = grid_summary[combo]
        tag = "  *WINNER*" if combo == winner else ""
        print(
            f"  {str(combo):<12} "
            f"{_fmt_sharpe(s['train']['avg_sharpe']):<8} "
            f"{_fmt_sharpe(s['test']['avg_sharpe']):<8} "
            f"{_fmt_pct(s['train']['avg_alpha_over_bh']):<10} "
            f"{_fmt_pct(s['test']['avg_alpha_over_bh']):<10} "
            f"{s['train']['total_entries']:<7} "
            f"{s['test']['total_entries']:<7} "
            f"{_fmt_sharpe(s['train']['avg_bh_sharpe']):<10} "
            f"{_fmt_sharpe(s['test']['avg_bh_sharpe']):<10}"
            f"{tag}"
        )

    print()
    print(
        f"==== WINNER (highest aggregate TRAIN Sharpe): "
        f"window={w_window}, threshold={w_threshold} ===="
    )
    w = grid_summary[winner]
    print("  TRAIN aggregate (used for selection):")
    print(f"    avg total return:  {_fmt_pct(w['train']['avg_total_return'])}")
    print(f"    avg Sharpe:        {_fmt_sharpe(w['train']['avg_sharpe'])}")
    print(f"    avg B&H Sharpe:    {_fmt_sharpe(w['train']['avg_bh_sharpe'])}")
    print(f"    avg alpha vs B&H:  {_fmt_pct(w['train']['avg_alpha_over_bh'])}")
    print(f"    total entries:     {w['train']['total_entries']}")
    print(
        f"    beats B&H on:      "
        f"{w['train']['num_beating_bh']} / {len(tickers)} tickers"
    )
    print("  TEST aggregate (held-out validation; NOT used for selection):")
    print(f"    avg total return:  {_fmt_pct(w['test']['avg_total_return'])}")
    print(f"    avg Sharpe:        {_fmt_sharpe(w['test']['avg_sharpe'])}")
    print(f"    avg B&H Sharpe:    {_fmt_sharpe(w['test']['avg_bh_sharpe'])}")
    print(f"    avg alpha vs B&H:  {_fmt_pct(w['test']['avg_alpha_over_bh'])}")
    print(f"    total entries:     {w['test']['total_entries']}")
    print(
        f"    beats B&H on:      "
        f"{w['test']['num_beating_bh']} / {len(tickers)} tickers"
    )

    print()
    print(
        f"==== PER-TICKER TRAIN/TEST SHARPE for WINNER "
        f"(window={w_window}, threshold={w_threshold}) ===="
    )
    print(f"  {'ticker':<10} {'train Sharpe':<14} {'test Sharpe':<14}")
    for t in tickers:
        s = per_ticker_winner_inputs[winner][t]
        print(
            f"  {t:<10} "
            f"{_fmt_sharpe(s['train_sharpe']):<14} "
            f"{_fmt_sharpe(s['test_sharpe']):<14}"
        )

    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
