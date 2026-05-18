"""scripts/backtest_ma_crossover_grid.py -- WP-SIGNAL-MA-CROSSOVER-GRID-V1.

5-combo parameter grid sweep of the MA crossover family on the 10
ASX blue-chip universe with 60/40 train/test holdout at 2024-07-01.

Locked decisions (orchestrator chat, not re-litigated):
- Param grid: 5 combos covering short-term + medium-term + long-term.
- Universe: same 10 ASX blue chips as V1, same order.
- Holdout cutoff 2024-07-01 (verified uniform across all 10 tickers
  in Phase A; train <= cutoff, test > cutoff).
- Aggregate-only optimisation on TRAIN Sharpe; tie-breaker train total
  return. Per-ticker tuning is curve-fitting (banked as anti-pattern
  in _ideas.md).
- Costs + capital + B&H baseline: unchanged from V1 (engine defaults).
- Output: grid_metrics.csv (5 combos x 2 windows = 10 rows) + winner
  equity curves (10 ticker files, full-window single sim for visual
  continuity).
- stdout ASCII-only per CLAUDE.md item 8.

Engine + signal + paginated-fetch are extracted modules (V2 IS the
second consumer — extraction shipped in this WP).
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
from src.backtest.signals import ma_crossover_signal
from src.data.yfinance_utils import fetch_prices_full

HOLDOUT_CUTOFF = pd.Timestamp("2024-07-01")
PARAM_GRID: list[tuple[int, int]] = [
    (10, 30),
    (20, 50),
    (30, 100),
    (50, 100),
    (50, 200),
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


# ----- Aggregation -----

def aggregate_window(window_results: dict[str, dict]) -> dict:
    """Aggregate per-ticker results into combo-level metrics for one window."""
    n = len(window_results)
    metrics = [r["metrics"] for r in window_results.values()]
    bh = [r["bh_metrics"] for r in window_results.values()]

    avg_total_return = sum(m["total_return_pct"] for m in metrics) / n
    ann_vals = [m["ann_return"] for m in metrics if not pd.isna(m["ann_return"])]
    avg_ann_return = float(np.mean(ann_vals)) if ann_vals else float("nan")
    sharpes = [m["sharpe"] for m in metrics if not pd.isna(m["sharpe"])]
    avg_sharpe = float(np.mean(sharpes)) if sharpes else float("nan")
    avg_max_dd = sum(m["max_dd_pct"] for m in metrics) / n
    avg_alpha = sum(
        m["total_return_pct"] - b["total_return_pct"]
        for m, b in zip(metrics, bh)
    ) / n
    total_trades = sum(m["n_trades"] for m in metrics)
    num_beating_bh = sum(
        1 for m, b in zip(metrics, bh)
        if m["total_return_pct"] > b["total_return_pct"]
    )
    return {
        "avg_total_return": avg_total_return,
        "avg_annualized_return": avg_ann_return,
        "avg_sharpe": avg_sharpe,
        "avg_max_dd": avg_max_dd,
        "avg_alpha_over_bh": avg_alpha,
        "total_trades": total_trades,
        "num_beating_bh": num_beating_bh,
    }


# ----- Main -----

def main() -> int:
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    client = create_client(url, key)

    resp = client.table("stocks").select("ticker").order("ticker").execute()
    tickers = sorted({r["ticker"] for r in resp.data})

    print(f"Universe ({len(tickers)} tickers): {tickers}")
    print(f"Param grid: {PARAM_GRID}")
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

    # Prefetch each per-ticker series ONCE (10 fetches total, not 50).
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
    grid_summary: dict[tuple[int, int], dict] = {}
    per_ticker_winner_inputs: dict[tuple[int, int], dict[str, dict]] = {}

    for short, long in PARAM_GRID:
        train_results: dict[str, dict] = {}
        test_results: dict[str, dict] = {}
        per_ticker_winner_inputs[(short, long)] = {}

        for t in tickers:
            df = prices_cache[t]
            signal = ma_crossover_signal(df, short=short, long=long)
            mask_train = df["trade_date"] <= HOLDOUT_CUTOFF

            train_df = df[mask_train].reset_index(drop=True)
            test_df = df[~mask_train].reset_index(drop=True)
            train_signal = signal[mask_train].reset_index(drop=True)
            test_signal = signal[~mask_train].reset_index(drop=True)

            tr = run_backtest(t, train_df, train_signal)
            te = run_backtest(t, test_df, test_signal)

            train_results[t] = tr
            test_results[t] = te
            per_ticker_winner_inputs[(short, long)][t] = {
                "train_sharpe": tr["metrics"]["sharpe"],
                "test_sharpe": te["metrics"]["sharpe"],
            }

        grid_summary[(short, long)] = {
            "train": aggregate_window(train_results),
            "test": aggregate_window(test_results),
        }

    # Winner: max aggregate train Sharpe, tiebreak avg_total_return.
    def winner_key(combo: tuple[int, int]) -> tuple[float, float]:
        agg = grid_summary[combo]["train"]
        sharpe = agg["avg_sharpe"]
        if pd.isna(sharpe):
            sharpe = float("-inf")
        return (sharpe, agg["avg_total_return"])

    winner = max(PARAM_GRID, key=winner_key)
    w_short, w_long = winner

    # Build grid_metrics.csv (10 rows: 5 combos x 2 windows).
    RESULTS_DIR.mkdir(exist_ok=True)
    grid_rows: list[dict] = []
    for combo in PARAM_GRID:
        for window_name in ("train", "test"):
            agg = grid_summary[combo][window_name]
            grid_rows.append({
                "short": combo[0],
                "long": combo[1],
                "window": window_name,
                "avg_total_return": agg["avg_total_return"],
                "avg_annualized_return": agg["avg_annualized_return"],
                "avg_sharpe": agg["avg_sharpe"],
                "avg_max_dd": agg["avg_max_dd"],
                "avg_alpha_over_bh": agg["avg_alpha_over_bh"],
                "total_trades": agg["total_trades"],
                "num_beating_bh": agg["num_beating_bh"],
                "is_winner_window": (combo == winner and window_name == "train"),
            })
    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(RESULTS_DIR / "grid_metrics.csv", index=False)

    # Winner equity curves: ONE fresh sim per ticker over the FULL window
    # using the winning (short, long). Train/test split metrics already
    # captured in grid_metrics.csv; the curves are for visual continuity.
    print(f"Writing winner equity curves (short={w_short}, long={w_long})...")
    for t in tickers:
        df = prices_cache[t]
        signal = ma_crossover_signal(df, short=w_short, long=w_long)
        result = run_backtest(t, df, signal)
        eq = result["equity_curve"]

        first_valid = signal.first_valid_index()
        pos_eval = signal.iloc[first_valid:].reset_index(drop=True).astype(int)

        out = pd.DataFrame({
            "trade_date": eq["trade_date"].dt.strftime("%Y-%m-%d"),
            "position": pos_eval.values,
            "equity_strategy": eq["signal_equity"].values,
            "equity_bh": eq["buy_hold_equity"].values,
        })
        csv_name = t.replace(".", "_")
        out.to_csv(RESULTS_DIR / f"equity_curve_{csv_name}_winner.csv",
                   index=False)

    # ----- stdout headline -----
    print()
    print("==== GRID HONESTY TABLE (aggregate train + test per combo) ====")
    print(
        f"  {'combo':<14} "
        f"{'train Sharpe':<14} {'test Sharpe':<14} "
        f"{'train alpha':<14} {'test alpha':<14}"
    )
    for combo in PARAM_GRID:
        s = grid_summary[combo]
        tag = "  *WINNER*" if combo == winner else ""
        print(
            f"  {str(combo):<14} "
            f"{_fmt_sharpe(s['train']['avg_sharpe']):<14} "
            f"{_fmt_sharpe(s['test']['avg_sharpe']):<14} "
            f"{_fmt_pct(s['train']['avg_alpha_over_bh']):<14} "
            f"{_fmt_pct(s['test']['avg_alpha_over_bh']):<14}"
            f"{tag}"
        )

    print()
    print(f"==== WINNER: short={w_short}, long={w_long} ====")
    w = grid_summary[winner]
    print("  TRAIN aggregate:")
    print(f"    avg total return:  {_fmt_pct(w['train']['avg_total_return'])}")
    print(f"    avg ann. return:   {_fmt_pct(w['train']['avg_annualized_return'])}")
    print(f"    avg Sharpe:        {_fmt_sharpe(w['train']['avg_sharpe'])}")
    print(f"    avg max DD:        {_fmt_pct(w['train']['avg_max_dd'])}")
    print(f"    avg alpha vs B&H:  {_fmt_pct(w['train']['avg_alpha_over_bh'])}")
    print(f"    total trades:      {w['train']['total_trades']}")
    print(
        f"    beats B&H on:      "
        f"{w['train']['num_beating_bh']} / {len(tickers)} tickers"
    )
    print("  TEST aggregate (out-of-sample holdout-honesty check):")
    print(f"    avg total return:  {_fmt_pct(w['test']['avg_total_return'])}")
    print(f"    avg ann. return:   {_fmt_pct(w['test']['avg_annualized_return'])}")
    print(f"    avg Sharpe:        {_fmt_sharpe(w['test']['avg_sharpe'])}")
    print(f"    avg max DD:        {_fmt_pct(w['test']['avg_max_dd'])}")
    print(f"    avg alpha vs B&H:  {_fmt_pct(w['test']['avg_alpha_over_bh'])}")
    print(f"    total trades:      {w['test']['total_trades']}")
    print(
        f"    beats B&H on:      "
        f"{w['test']['num_beating_bh']} / {len(tickers)} tickers"
    )

    print()
    print(
        f"==== PER-TICKER TRAIN/TEST SHARPE for WINNER "
        f"(short={w_short}, long={w_long}) ===="
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
    print(
        f"Outputs: {RESULTS_DIR / 'grid_metrics.csv'} "
        f"(10 rows: 5 combos x 2 windows)"
    )
    print(
        f"Outputs: {RESULTS_DIR}/equity_curve_<TICKER_AX>_winner.csv "
        f"(10 files for winner)"
    )
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
