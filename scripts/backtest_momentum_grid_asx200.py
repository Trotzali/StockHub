"""scripts/backtest_momentum_grid_asx200.py -- WP-SIGNAL-MOMENTUM-V1.

3-combo absolute lookback momentum sweep on ASX 200 survivors
(>= MIN_HISTORY_PRE_CUTOFF rows pre-2024-07-01).

Signal: momentum_absolute_lookback_signal(df, N, skip=21).
  p_then = close[t - skip - N]
  p_skip = close[t - skip]
  lookback_return = (p_skip / p_then) - 1
  signal = 1 if lookback_return > 0 (strict) else 0
  warm-up (skip + N) days = NaN

Grid: N in {63, 126, 252} = {3, 6, 12 months}. skip=21 fixed.

Locked decisions carried verbatim from MR V2 (c823e20):
- Universe: src.data.universe.ASX_200 -> >= MIN_HISTORY_PRE_CUTOFF
  rows where trade_date <= 2024-07-01.
- Holdout 60/40 at 2024-07-01 (train inclusive of cutoff).
- Winner selection: aggregate TRAIN Sharpe; tiebreak aggregate
  train total return. Test metrics REPORTED as held-out validation,
  never optimised over.
- Engine: src.backtest.engine.run_backtest, defaults
  ($10k/ticker, 0.1% brokerage, $0.01/share slippage, long-only).
- Stdout ASCII-only per CLAUDE.md item 8.

Embedded V-walk: CBA.AX winner combo, first 3 0->1 transitions in
the train window, script-computed lookback_return (pandas .shift)
vs independently-computed manual reference (explicit .iloc lookups
into closes). PASS criterion: max delta < 1e-8.
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
from src.backtest.signals import momentum_absolute_lookback_signal
from src.data.universe import ASX_200
from src.data.yfinance_utils import fetch_prices_full


REGIME_TICKER_EXCLUDE = "^AXJO"
HOLDOUT_CUTOFF = pd.Timestamp("2024-07-01")
MIN_HISTORY_PRE_CUTOFF = 504
SKIP = 21
PARAM_GRID: list[int] = [63, 126, 252]

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ----- Output helpers (ASCII only) -----

def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v * 100:+.2f}%"


def _fmt_sharpe(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.3f}"


# ----- Aggregation (verbatim from MR V2) -----

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


# ----- Survivor filter (verbatim from MR V2) -----

def survivor_filter(client, candidates: list[str]) -> tuple[list[str], list[tuple[str, int]]]:
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


# ----- Embedded V-walk -----

def vwalk_cba_ax(prices_cache: dict[str, pd.DataFrame], winner_N: int) -> float:
    """Recompute lookback_return manually for first 3 train-window 0->1
    transitions on CBA.AX (winner combo), compare against script's
    pandas-shift path. Returns max abs delta.

    Independent path: explicit closes.iloc[t - skip - N] / closes.iloc[t - skip]
    lookups. Script path: closes.shift(skip + N) / closes.shift(skip).
    These reach the same values via different code; delta < 1e-8 = PASS.
    """
    df = prices_cache["CBA.AX"]
    closes = df["adj_close"]
    signal = momentum_absolute_lookback_signal(df, N=winner_N, skip=SKIP)

    # Script path: from inside the signal function, recompute
    # lookback_return via .shift (mirrors the signal fn body).
    p_then_script = closes.shift(SKIP + winner_N)
    p_skip_script = closes.shift(SKIP)
    lb_script = (p_skip_script / p_then_script) - 1.0

    mask_train = df["trade_date"] <= HOLDOUT_CUTOFF
    train_sig = signal[mask_train].reset_index(drop=True)
    train_df = df[mask_train].reset_index(drop=True)

    # Find first 3 0->1 transitions in train
    entry_train_ixs: list[int] = []
    prev = 0
    for ix in range(len(train_sig)):
        if pd.notna(train_sig.iloc[ix]):
            cur = int(train_sig.iloc[ix])
            if prev == 0 and cur == 1:
                entry_train_ixs.append(ix)
                if len(entry_train_ixs) >= 3:
                    break
            prev = cur

    print()
    print(
        f"==== EMBEDDED V-WALK: CBA.AX winner combo N={winner_N}, "
        f"skip={SKIP} ===="
    )
    print(
        f"  {'date':<12} {'src_ix':<6} {'p_then':<10} "
        f"{'p_skip':<10} {'lb_script':<14} {'lb_manual':<14} {'delta':<12}"
    )
    max_delta = 0.0
    for tr_ix in entry_train_ixs:
        # Map train-row index back to source df index by date match
        d_t = train_df.iloc[tr_ix]["trade_date"]
        src_ix = int(df.index[df["trade_date"] == d_t][0])
        # Manual independent computation: explicit .iloc lookups
        p_then_manual = float(closes.iloc[src_ix - SKIP - winner_N])
        p_skip_manual = float(closes.iloc[src_ix - SKIP])
        lb_manual = (p_skip_manual / p_then_manual) - 1.0
        lb_s = float(lb_script.iloc[src_ix])
        delta = abs(lb_manual - lb_s)
        max_delta = max(max_delta, delta)
        print(
            f"  {str(d_t.date()):<12} {src_ix:<6} "
            f"{p_then_manual:<10.4f} {p_skip_manual:<10.4f} "
            f"{lb_s:<+14.10f} {lb_manual:<+14.10f} {delta:<12.2e}"
        )
    print(f"  MAX DELTA: {max_delta:.2e}  (PASS criterion < 1e-8)")
    print(f"  VERDICT: {'PASS' if max_delta < 1e-8 else 'FAIL'}")
    return max_delta


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
    print(f"Param grid (N values, skip={SKIP} fixed): {PARAM_GRID}")
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
    grid_summary: dict[int, dict] = {}
    per_ticker_winner_inputs: dict[int, dict[str, dict]] = {}

    for N in PARAM_GRID:
        train_results: dict[str, dict] = {}
        test_results: dict[str, dict] = {}
        per_ticker_winner_inputs[N] = {}

        for t in tickers:
            df = prices_cache[t]
            signal = momentum_absolute_lookback_signal(df, N=N, skip=SKIP)
            mask_train = df["trade_date"] <= HOLDOUT_CUTOFF

            train_df = df[mask_train].reset_index(drop=True)
            test_df = df[~mask_train].reset_index(drop=True)
            train_signal = signal[mask_train].reset_index(drop=True)
            test_signal = signal[~mask_train].reset_index(drop=True)

            tr = run_backtest(t, train_df, train_signal)
            te = run_backtest(t, test_df, test_signal)
            train_results[t] = tr
            test_results[t] = te
            per_ticker_winner_inputs[N][t] = {
                "train_sharpe": tr["metrics"]["sharpe"],
                "test_sharpe": te["metrics"]["sharpe"],
            }

        grid_summary[N] = {
            "train": aggregate_window(train_results),
            "test": aggregate_window(test_results),
        }

    # Winner: highest aggregate TRAIN Sharpe; tiebreak avg train total return.
    # Test metrics REPORTED but NOT used for selection (test-set leakage guardrail).
    def winner_key(N: int):
        agg = grid_summary[N]["train"]
        sharpe = agg["avg_sharpe"]
        if pd.isna(sharpe):
            sharpe = float("-inf")
        return (sharpe, agg["avg_total_return"])

    winner = max(PARAM_GRID, key=winner_key)

    print("==== GRID HONESTY TABLE (aggregate train + test per N) ====")
    print(
        f"  {'N':<6} "
        f"{'tr Sh':<8} {'te Sh':<8} "
        f"{'tr alpha':<10} {'te alpha':<10} "
        f"{'tr ent':<7} {'te ent':<7} "
        f"{'bh tr Sh':<10} {'bh te Sh':<10}"
    )
    for N in PARAM_GRID:
        s = grid_summary[N]
        tag = "  *WINNER*" if N == winner else ""
        print(
            f"  N={N:<4} "
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
        f"N={winner}, skip={SKIP} ===="
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
        f"==== PER-TICKER TRAIN/TEST SHARPE for WINNER N={winner} ===="
    )
    print(f"  {'ticker':<10} {'train Sharpe':<14} {'test Sharpe':<14}")
    for t in tickers:
        s = per_ticker_winner_inputs[winner][t]
        print(
            f"  {t:<10} "
            f"{_fmt_sharpe(s['train_sharpe']):<14} "
            f"{_fmt_sharpe(s['test_sharpe']):<14}"
        )

    # Embedded V-walk on CBA.AX winner combo
    vwalk_cba_ax(prices_cache, winner)

    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
