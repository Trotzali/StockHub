"""scripts/backtest_ma_crossover_regime_grid.py -- WP-SIGNAL-MA-CROSSOVER-REGIME-FILTER-V1.

V3 grid sweep: same 5 (short, long) MA-crossover combos as V2, same
60/40 train/test holdout at 2024-07-01, but the primary signal is
AND-ed with a regime filter that requires the S&P/ASX 200 index
(^AXJO) to be above its own MA-200.

Combined signal via date-aligned element-wise multiplication:
  combined = ma_crossover_signal(stock) * regime_above_ma(XJO, 200)
NaN propagates through the multiplication, so the engine treats
"either side undefined" as warm-up (slices past).

Locked decisions (orchestrator chat):
- Regime ticker ^AXJO seeded at 1260 rows (2021-05-18..2026-05-15)
  via scripts/seed_xjo.py before this WP fires.
- Regime window: 200 trading days (same as the longer MA in V1/V2).
- Aggregate-only optimisation on TRAIN Sharpe; tiebreak avg_total_return.
- ASCII-only stdout per CLAUDE.md item 8.
- V2 outputs (results/grid_metrics.csv + winner CSVs) are read-only
  reference for the side-by-side comparison; not modified.
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
from src.backtest.signals import ma_crossover_signal, regime_above_ma
from src.data.yfinance_utils import fetch_prices_full

HOLDOUT_CUTOFF = pd.Timestamp("2024-07-01")
PARAM_GRID: list[tuple[int, int]] = [
    (10, 30),
    (20, 50),
    (30, 100),
    (50, 100),
    (50, 200),
]
REGIME_WINDOW = 200
REGIME_TICKER = "^AXJO"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"


def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v * 100:+.2f}%"


def _fmt_sharpe(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.3f}"


def _fmt_delta_sharpe(v3: float, v2: float) -> str:
    if pd.isna(v3) or pd.isna(v2):
        return "N/A"
    delta = v3 - v2
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.3f}"


def _fmt_delta_pct(v3: float, v2: float) -> str:
    if pd.isna(v3) or pd.isna(v2):
        return "N/A"
    delta = v3 - v2
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta * 100:.2f}%"


def load_price_df(client, ticker: str) -> pd.DataFrame:
    records = fetch_prices_full(client, ticker)
    df = pd.DataFrame(records)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["adj_close"] = pd.to_numeric(df["adj_close"])
    return df.sort_values("trade_date").reset_index(drop=True)


def aggregate_window(window_results: dict[str, dict]) -> dict:
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


def build_combined_signal(stock_df: pd.DataFrame,
                          regime_signal_by_date: pd.Series,
                          short: int, long: int) -> pd.Series:
    """ma_crossover_signal AND-ed with XJO regime, date-aligned.

    Returns a Series indexed 0..N-1 of length len(stock_df).

    Mid-series NaN handling: the regime series (indexed by XJO dates)
    is reindexed onto stock dates first, then forward-filled. This
    carries the most recent known regime state forward through any
    stock dates that XJO is missing (5 historical zero-volume days
    dropped at seed time + the 1-day calendar misalignment at the
    series start). That matches the realistic semantics of "no XJO
    data today, carry yesterday's regime forward." Without ffill,
    a regime gap mid-position would cause spurious exit + re-entry
    transactions in the engine.

    Initial NaN (stock dates before the first XJO row, or warm-up)
    propagates through naturally — the engine slices past the first
    non-NaN.
    """
    stock_signal_raw = ma_crossover_signal(stock_df, short=short, long=long)
    stock_dates = pd.to_datetime(stock_df["trade_date"]).values
    regime_aligned = regime_signal_by_date.reindex(stock_dates).ffill()
    combined = stock_signal_raw.values * regime_aligned.values
    return pd.Series(combined)


def main() -> int:
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    client = create_client(url, key)

    # Universe (10 blue chips, exclude ^AXJO itself).
    resp = client.table("stocks").select("ticker").execute()
    all_tickers = sorted({r["ticker"] for r in resp.data})
    tickers = [t for t in all_tickers if t != REGIME_TICKER]
    print(f"Universe ({len(tickers)} tickers): {tickers}")
    print(f"Regime ticker: {REGIME_TICKER} (filter: above MA-{REGIME_WINDOW})")
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

    # Prefetch all per-ticker series + XJO.
    print("Prefetching prices...")
    prices_cache: dict[str, pd.DataFrame] = {}
    for t in tickers:
        prices_cache[t] = load_price_df(client, t)
    xjo_df = load_price_df(client, REGIME_TICKER)
    n_rows_total = sum(len(d) for d in prices_cache.values()) + len(xjo_df)
    print(
        f"  Cached {n_rows_total} rows ({len(tickers)} tickers + "
        f"{REGIME_TICKER} regime series)."
    )
    print()

    # Build the regime signal ONCE over the full XJO series.
    regime_raw = regime_above_ma(
        xjo_df, window=REGIME_WINDOW, close_col="adj_close"
    )
    regime_signal_by_date = pd.Series(
        regime_raw.values,
        index=pd.to_datetime(xjo_df["trade_date"]),
    )

    # Grid sweep with regime filter.
    grid_summary: dict[tuple[int, int], dict] = {}
    per_ticker_winner_inputs: dict[tuple[int, int], dict[str, dict]] = {}

    for short, long in PARAM_GRID:
        train_results: dict[str, dict] = {}
        test_results: dict[str, dict] = {}
        per_ticker_winner_inputs[(short, long)] = {}

        for t in tickers:
            stock_df = prices_cache[t]
            combined = build_combined_signal(
                stock_df, regime_signal_by_date, short, long
            )
            mask_train = stock_df["trade_date"] <= HOLDOUT_CUTOFF

            train_df = stock_df[mask_train].reset_index(drop=True)
            test_df = stock_df[~mask_train].reset_index(drop=True)
            train_signal = combined[mask_train.values].reset_index(drop=True)
            test_signal = combined[~mask_train.values].reset_index(drop=True)

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

    # Winner: highest train Sharpe; tiebreak avg_total_return.
    def winner_key(combo: tuple[int, int]) -> tuple[float, float]:
        agg = grid_summary[combo]["train"]
        sharpe = agg["avg_sharpe"]
        if pd.isna(sharpe):
            sharpe = float("-inf")
        return (sharpe, agg["avg_total_return"])

    winner = max(PARAM_GRID, key=winner_key)
    w_short, w_long = winner

    # grid_metrics_regime.csv (10 rows: 5 combos x 2 windows).
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
                "is_winner_window": (
                    combo == winner and window_name == "train"
                ),
            })
    pd.DataFrame(grid_rows).to_csv(
        RESULTS_DIR / "grid_metrics_regime.csv", index=False
    )

    # Winner equity curves: full-window single sim with regime-filtered signal.
    print(f"Writing winner equity curves (short={w_short}, long={w_long})...")
    for t in tickers:
        stock_df = prices_cache[t]
        combined = build_combined_signal(
            stock_df, regime_signal_by_date, w_short, w_long
        )
        result = run_backtest(t, stock_df, combined)
        eq = result["equity_curve"]

        first_valid = combined.first_valid_index()
        pos_eval = combined.iloc[first_valid:].reset_index(drop=True).astype(int)

        out = pd.DataFrame({
            "trade_date": eq["trade_date"].dt.strftime("%Y-%m-%d"),
            "position": pos_eval.values,
            "equity_strategy": eq["signal_equity"].values,
            "equity_bh": eq["buy_hold_equity"].values,
        })
        csv_name = t.replace(".", "_")
        out.to_csv(
            RESULTS_DIR / f"equity_curve_{csv_name}_winner_regime.csv",
            index=False,
        )

    # Read V2 grid for side-by-side comparison.
    v2_grid = pd.read_csv(RESULTS_DIR / "grid_metrics.csv")

    print()
    print("==== V3 GRID HONESTY TABLE (regime-filtered, train + test) ====")
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

    # Side-by-side V2 vs V3 deltas.
    print()
    print("==== V2 vs V3 SIDE-BY-SIDE (per combo, train then test) ====")
    print(
        f"  {'combo':<10} {'window':<6} "
        f"{'V2 Sharpe':<11} {'V3 Sharpe':<11} {'dSharpe':<10} "
        f"{'V2 alpha':<11} {'V3 alpha':<11} {'dAlpha':<10}"
    )
    for combo in PARAM_GRID:
        for window in ("train", "test"):
            v2_row = v2_grid[
                (v2_grid["short"] == combo[0])
                & (v2_grid["long"] == combo[1])
                & (v2_grid["window"] == window)
            ].iloc[0]
            v3 = grid_summary[combo][window]
            v2_sharpe = float(v2_row["avg_sharpe"])
            v3_sharpe = v3["avg_sharpe"]
            v2_alpha = float(v2_row["avg_alpha_over_bh"])
            v3_alpha = v3["avg_alpha_over_bh"]
            print(
                f"  {str(combo):<10} {window:<6} "
                f"{_fmt_sharpe(v2_sharpe):<11} "
                f"{_fmt_sharpe(v3_sharpe):<11} "
                f"{_fmt_delta_sharpe(v3_sharpe, v2_sharpe):<10} "
                f"{_fmt_pct(v2_alpha):<11} "
                f"{_fmt_pct(v3_alpha):<11} "
                f"{_fmt_delta_pct(v3_alpha, v2_alpha):<10}"
            )

    print()
    print(f"==== V3 WINNER: short={w_short}, long={w_long} ====")
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
        f"==== PER-TICKER TRAIN/TEST SHARPE for V3 WINNER "
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
    print(f"Outputs: {RESULTS_DIR / 'grid_metrics_regime.csv'}")
    print(
        f"Outputs: {RESULTS_DIR}/equity_curve_<TICKER_AX>_winner_regime.csv "
        f"({len(tickers)} files)"
    )
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
