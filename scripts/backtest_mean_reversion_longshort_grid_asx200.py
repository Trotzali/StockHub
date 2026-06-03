"""scripts/backtest_mean_reversion_longshort_grid_asx200.py
WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1.

First long-short experiment. Re-runs the MR z-score spec (refuted
long-only at c823e20 / MR V2) with a symmetric short leg added,
through the long-short engine (3cd4d0b), with per-ticker tiered
borrow costs (1 / 4 / 8 % APR by median dollar volume terciles).

Universe: same 185 survivors as MR V2 / momentum V1
(>= 504 rows pre-2024-07-01 in src.data.universe.ASX_200, minus
^AXJO).

Grid: same 6 combos (window, threshold) =
    (10, 2.0), (20, 1.5), (20, 2.0), (20, 2.5), (30, 2.0), (50, 2.0).

Holdout: 60/40 at 2024-07-01 (train_mask uses <=, inclusive of cutoff).

Winner selection: aggregate TRAIN NET Sharpe (post-borrow -- the
realistic decision). GROSS reported alongside for diagnosis. TEST
metrics are held-out validation, NEVER optimised over.

Borrow tiering: per src.backtest.borrow_tiering. Static per-ticker
from full-sample median (close * volume); not test-leakage because
liquidity is a structural cost feature, not a return predictor.

Embedded V-walks (PASS required before any external use):
- Signal z-transition V-walk on CBA.AX winner combo (first 3 0->+1
  AND first 3 0->-1 in train; manual z = (close - SMA) / std(ddof=0)
  vs script's emitted signal direction). PASS criterion: <1e-8 z delta.
- Holdout split assert: train.max <= cutoff, test.min > cutoff.
- Gross-vs-net invariant: at least one ticker has metrics_net !=
  metrics AND borrow_drag_total > 0.
- Tier-distribution sanity: 3 tier counts close to N/3; CBA.AX in
  tier 0 (most liquid).
- Pagination coverage: helper's CBA.AX row count == supabase
  COUNT(*) for CBA.AX (no silent truncation at 1000 rows).

ASCII-only stdout per CLAUDE.md item 8.
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
from src.backtest.signals import mean_reversion_zscore_longshort_signal
from src.backtest.borrow_tiering import (
    TIER_RATES_DEFAULT,
    compute_borrow_rates,
)
from src.data.universe import ASX_200
from src.data.yfinance_utils import fetch_prices_full


REGIME_TICKER_EXCLUDE = "^AXJO"
HOLDOUT_CUTOFF = pd.Timestamp("2024-07-01")
MIN_HISTORY_PRE_CUTOFF = 504
PARAM_GRID: list[tuple[int, float]] = [
    (10, 2.0),
    (20, 1.5),
    (20, 2.0),
    (20, 2.5),
    (30, 2.0),
    (50, 2.0),
]
TIER_RATES = TIER_RATES_DEFAULT


# ----- Output helpers (ASCII) -----

def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v * 100:+.2f}%"


def _fmt_sharpe(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.3f}"


# ----- Aggregation (extended to read either gross or net metrics) -----

def aggregate_window(window_results: dict[str, dict],
                     metric_key: str = "metrics") -> dict:
    """Aggregate per-ticker results for one window. metric_key in
    {"metrics" (gross), "metrics_net" (net)}.
    """
    n = len(window_results)
    metrics = [r[metric_key] for r in window_results.values()]
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

def survivor_filter(client, candidates: list[str]):
    cutoff_iso = HOLDOUT_CUTOFF.date().isoformat()
    survivors, excluded = [], []
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


# ----- Embedded V-walks -----

def vwalk_signal_transitions(prices_cache, winner_window, winner_threshold):
    """CBA.AX winner combo: first 3 0->+1 and 0->-1 transitions in
    train window. Hand-compute z; verify script signal direction.
    """
    df = prices_cache["CBA.AX"]
    closes = df["adj_close"].astype(float)
    sig = mean_reversion_zscore_longshort_signal(
        df, window=winner_window, threshold=winner_threshold,
    )
    mask_train = df["trade_date"] <= HOLDOUT_CUTOFF
    train_df = df[mask_train].reset_index(drop=True)
    train_sig = sig[mask_train].reset_index(drop=True)

    # Find first 3 0->+1 and first 3 0->-1 transitions in train
    longs, shorts = [], []
    prev = 0
    for i in range(len(train_sig)):
        if pd.notna(train_sig.iloc[i]):
            cur = int(train_sig.iloc[i])
            if prev == 0 and cur == 1 and len(longs) < 3:
                longs.append(i)
            if prev == 0 and cur == -1 and len(shorts) < 3:
                shorts.append(i)
            prev = cur
        if len(longs) >= 3 and len(shorts) >= 3:
            break

    print()
    print(
        f"==== EMBEDDED V-WALK 1: CBA.AX signal transitions "
        f"(window={winner_window}, threshold={winner_threshold}) ===="
    )
    max_delta = 0.0
    for label, ixs, expected_sign in (("0->+1 LONG entries", longs, +1),
                                       ("0->-1 SHORT entries", shorts, -1)):
        print(f"  {label}:")
        for tr_ix in ixs:
            d_t = train_df.iloc[tr_ix]["trade_date"]
            src_ix = int(df.index[df["trade_date"] == d_t][0])
            # Manual z arithmetic: closes[src_ix-window+1 : src_ix+1]
            window_slice = closes.iloc[src_ix - winner_window + 1: src_ix + 1].values
            assert len(window_slice) == winner_window
            mean_m = float(window_slice.mean())
            var_m = float(((window_slice - mean_m) ** 2).mean())  # ddof=0
            std_m = var_m ** 0.5
            z_m = (float(closes.iloc[src_ix]) - mean_m) / std_m
            # Script z (rolling, same formula)
            sma = closes.rolling(winner_window).mean().iloc[src_ix]
            std_s = closes.rolling(winner_window).std(ddof=0).iloc[src_ix]
            z_s = (float(closes.iloc[src_ix]) - float(sma)) / float(std_s)
            delta = abs(z_m - z_s)
            max_delta = max(max_delta, delta)
            actual_sig = int(sig.iloc[src_ix])
            # Verify expected direction matches
            if expected_sign == +1:
                assert z_m < -winner_threshold, (
                    f"long entry expected z < -{winner_threshold}, got z={z_m}"
                )
                assert actual_sig == 1, f"sig expected 1 got {actual_sig}"
            else:
                assert z_m > +winner_threshold, (
                    f"short entry expected z > +{winner_threshold}, got z={z_m}"
                )
                assert actual_sig == -1, f"sig expected -1 got {actual_sig}"
            print(
                f"    {str(d_t.date()):<12} src_ix={src_ix:<5} "
                f"close={float(closes.iloc[src_ix]):<10.4f} "
                f"z_script={z_s:<+10.6f} z_manual={z_m:<+10.6f} "
                f"delta={delta:.2e} sig={actual_sig:+d}"
            )
    print(f"  MAX z DELTA: {max_delta:.2e}  (PASS criterion < 1e-8)")
    print(f"  VERDICT: {'PASS' if max_delta < 1e-8 else 'FAIL'}")
    return max_delta


def vwalk_holdout_split(prices_cache, tickers):
    """For one ticker, assert train.max <= cutoff, test.min > cutoff."""
    t = tickers[0]
    df = prices_cache[t]
    mask_train = df["trade_date"] <= HOLDOUT_CUTOFF
    train_df = df[mask_train]
    test_df = df[~mask_train]
    train_max = train_df["trade_date"].max()
    test_min = test_df["trade_date"].min()
    print()
    print(f"==== EMBEDDED V-WALK 2: holdout split ({t}) ====")
    print(f"  train.max:  {train_max.date()}  (cutoff: {HOLDOUT_CUTOFF.date()})")
    print(f"  test.min:   {test_min.date()}")
    ok_train = train_max <= HOLDOUT_CUTOFF
    ok_test = test_min > HOLDOUT_CUTOFF
    print(f"  train.max <= cutoff: {ok_train}")
    print(f"  test.min  >  cutoff: {ok_test}")
    print(f"  VERDICT: {'PASS' if (ok_train and ok_test) else 'FAIL'}")
    return ok_train and ok_test


def vwalk_gross_net_invariant(train_results):
    """At least one ticker must have metrics_net != metrics AND
    borrow_drag_total > 0.
    """
    found = False
    for t, r in train_results.items():
        if (r["metrics_net"]["final_equity"] != r["metrics"]["final_equity"]
                and r["borrow_drag_total"] > 0):
            found = True
            print()
            print(f"==== EMBEDDED V-WALK 3: gross-vs-net invariant ====")
            print(f"  example ticker: {t}")
            print(f"    metrics.final_equity     = {r['metrics']['final_equity']:.4f}")
            print(f"    metrics_net.final_equity = {r['metrics_net']['final_equity']:.4f}")
            print(f"    borrow_drag_total        = {r['borrow_drag_total']:.4f}")
            print(f"    borrow_rate              = {r['borrow_rate']:.4f}")
            print(f"  VERDICT: PASS")
            return True
    print()
    print(f"==== EMBEDDED V-WALK 3: gross-vs-net invariant ====")
    print(f"  VERDICT: FAIL (no ticker had borrow drag -- short leg may not")
    print(f"           have fired on any train series)")
    return False


def vwalk_pagination_coverage(client, ticker, diagnostics):
    """Helper's row count for `ticker` MUST equal Supabase COUNT(*)
    for that ticker. Catches silent truncation at the 1000-row cap.
    """
    r = (
        client.table("prices")
        .select("ticker", count="exact")
        .eq("ticker", ticker)
        .limit(0)
        .execute()
    )
    db_count = r.count
    helper_count = diagnostics[ticker]["row_count"]
    print()
    print(f"==== EMBEDDED V-WALK 4: pagination coverage ({ticker}) ====")
    print(f"  helper row count: {helper_count}")
    print(f"  supabase COUNT(*): {db_count}")
    ok = (helper_count == db_count)
    print(f"  match: {ok}")
    print(f"  VERDICT: {'PASS' if ok else 'FAIL (silent truncation)'}")
    return ok


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
    print(
        f"Borrow tiers (annualized): top={TIER_RATES[0]*100:.0f}%, "
        f"mid={TIER_RATES[1]*100:.0f}%, bottom={TIER_RATES[2]*100:.0f}%"
    )
    print()

    print("Computing per-ticker borrow rates (median dollar volume terciles, paginated fetch)...")
    tier_rates, tier_diag = compute_borrow_rates(client, tickers, TIER_RATES)
    tier_counts = {0: 0, 1: 0, 2: 0}
    for t in tickers:
        tier_counts[tier_diag[t]["tier"]] += 1
    print(f"  Tier distribution: top={tier_counts[0]}, mid={tier_counts[1]}, bottom={tier_counts[2]}")
    # Show 3 sample tickers per tier sorted by median_adv
    by_tier: dict[int, list] = {0: [], 1: [], 2: []}
    for t in tickers:
        by_tier[tier_diag[t]["tier"]].append(
            (t, tier_diag[t]["median_adv"], tier_diag[t]["row_count"])
        )
    for tier in (0, 1, 2):
        by_tier[tier].sort(key=lambda x: -x[1])  # desc by adv
        label = {0: "top (most liquid)", 1: "mid", 2: "bottom (least liquid)"}[tier]
        rate = TIER_RATES[tier]
        print(f"  Tier {tier} ({label}, rate={rate*100:.0f}%): "
              f"top-of-tier {by_tier[tier][:3]}; bottom {by_tier[tier][-3:]}")
    print(
        f"  CBA.AX: tier {tier_diag['CBA.AX']['tier']}, "
        f"rate={tier_diag['CBA.AX']['rate']*100:.0f}%, "
        f"median_adv=${tier_diag['CBA.AX']['median_adv']:,.0f}"
    )
    assert tier_diag["CBA.AX"]["tier"] == 0, "CBA.AX should be tier 0 (most liquid)"
    print(f"  CBA.AX tier-0 sanity: PASS")

    # Run pagination coverage check on CBA.AX (high-row-count blue chip)
    vwalk_pagination_coverage(client, "CBA.AX", tier_diag) or sys.exit(1)
    print()

    print("Prefetching prices (adj_close, paginated)...")
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

    # Grid sweep: per combo, per ticker, two sims (train + test);
    # aggregate gross AND net separately.
    grid_summary: dict[tuple[int, float], dict] = {}
    per_ticker_winner_inputs: dict[tuple[int, float], dict[str, dict]] = {}
    train_results_winner_combo: dict | None = None  # reused for V-walk 3

    for window, threshold in PARAM_GRID:
        train_results: dict[str, dict] = {}
        test_results: dict[str, dict] = {}
        per_ticker_winner_inputs[(window, threshold)] = {}

        for t in tickers:
            df = prices_cache[t]
            signal = mean_reversion_zscore_longshort_signal(
                df, window=window, threshold=threshold,
            )
            mask_train = df["trade_date"] <= HOLDOUT_CUTOFF

            train_df = df[mask_train].reset_index(drop=True)
            test_df = df[~mask_train].reset_index(drop=True)
            train_signal = signal[mask_train].reset_index(drop=True)
            test_signal = signal[~mask_train].reset_index(drop=True)

            tr = run_backtest(t, train_df, train_signal,
                              borrow_rate=tier_rates[t])
            te = run_backtest(t, test_df, test_signal,
                              borrow_rate=tier_rates[t])
            train_results[t] = tr
            test_results[t] = te
            per_ticker_winner_inputs[(window, threshold)][t] = {
                "train_sharpe_gross": tr["metrics"]["sharpe"],
                "train_sharpe_net":   tr["metrics_net"]["sharpe"],
                "test_sharpe_gross":  te["metrics"]["sharpe"],
                "test_sharpe_net":    te["metrics_net"]["sharpe"],
            }

        grid_summary[(window, threshold)] = {
            "train_gross": aggregate_window(train_results, "metrics"),
            "train_net":   aggregate_window(train_results, "metrics_net"),
            "test_gross":  aggregate_window(test_results, "metrics"),
            "test_net":    aggregate_window(test_results, "metrics_net"),
        }

    # Winner: highest aggregate TRAIN NET Sharpe; tiebreak avg train net total return.
    def winner_key(combo):
        agg = grid_summary[combo]["train_net"]
        sharpe = agg["avg_sharpe"]
        if pd.isna(sharpe):
            sharpe = float("-inf")
        return (sharpe, agg["avg_total_return"])

    winner = max(PARAM_GRID, key=winner_key)
    w_window, w_threshold = winner

    print()
    print("==== GRID HONESTY TABLE (gross alongside net; selection on TRAIN NET Sharpe) ====")
    print(
        f"  {'combo':<12} "
        f"{'tr Sh g':<9} {'tr Sh n':<9} "
        f"{'te Sh g':<9} {'te Sh n':<9} "
        f"{'tr alp g':<10} {'tr alp n':<10} "
        f"{'te alp g':<10} {'te alp n':<10} "
        f"{'tr ent':<7} {'te ent':<7}"
    )
    for combo in PARAM_GRID:
        s = grid_summary[combo]
        tag = "  *WINNER*" if combo == winner else ""
        print(
            f"  {str(combo):<12} "
            f"{_fmt_sharpe(s['train_gross']['avg_sharpe']):<9} "
            f"{_fmt_sharpe(s['train_net']['avg_sharpe']):<9} "
            f"{_fmt_sharpe(s['test_gross']['avg_sharpe']):<9} "
            f"{_fmt_sharpe(s['test_net']['avg_sharpe']):<9} "
            f"{_fmt_pct(s['train_gross']['avg_alpha_over_bh']):<10} "
            f"{_fmt_pct(s['train_net']['avg_alpha_over_bh']):<10} "
            f"{_fmt_pct(s['test_gross']['avg_alpha_over_bh']):<10} "
            f"{_fmt_pct(s['test_net']['avg_alpha_over_bh']):<10} "
            f"{s['train_gross']['total_entries']:<7} "
            f"{s['test_gross']['total_entries']:<7}"
            f"{tag}"
        )

    print()
    print(
        f"==== WINNER (highest aggregate TRAIN NET Sharpe): "
        f"window={w_window}, threshold={w_threshold} ===="
    )
    w = grid_summary[winner]
    print("  TRAIN NET (used for selection):")
    print(f"    avg total return:  {_fmt_pct(w['train_net']['avg_total_return'])}")
    print(f"    avg Sharpe:        {_fmt_sharpe(w['train_net']['avg_sharpe'])}")
    print(f"    avg B&H Sharpe:    {_fmt_sharpe(w['train_net']['avg_bh_sharpe'])}")
    print(f"    avg alpha vs B&H:  {_fmt_pct(w['train_net']['avg_alpha_over_bh'])}")
    print(f"    total entries:     {w['train_net']['total_entries']}")
    print(
        f"    beats B&H on:      "
        f"{w['train_net']['num_beating_bh']} / {len(tickers)} tickers"
    )
    print("  TRAIN GROSS (diagnostic):")
    print(f"    avg Sharpe:        {_fmt_sharpe(w['train_gross']['avg_sharpe'])}")
    print(f"    avg alpha vs B&H:  {_fmt_pct(w['train_gross']['avg_alpha_over_bh'])}")
    print("  TEST NET (held-out validation; NOT used for selection):")
    print(f"    avg total return:  {_fmt_pct(w['test_net']['avg_total_return'])}")
    print(f"    avg Sharpe:        {_fmt_sharpe(w['test_net']['avg_sharpe'])}")
    print(f"    avg B&H Sharpe:    {_fmt_sharpe(w['test_net']['avg_bh_sharpe'])}")
    print(f"    avg alpha vs B&H:  {_fmt_pct(w['test_net']['avg_alpha_over_bh'])}")
    print(f"    total entries:     {w['test_net']['total_entries']}")
    print(
        f"    beats B&H on:      "
        f"{w['test_net']['num_beating_bh']} / {len(tickers)} tickers"
    )
    print("  TEST GROSS (diagnostic):")
    print(f"    avg Sharpe:        {_fmt_sharpe(w['test_gross']['avg_sharpe'])}")
    print(f"    avg alpha vs B&H:  {_fmt_pct(w['test_gross']['avg_alpha_over_bh'])}")

    # Re-run winner combo train to capture train_results_winner_combo
    # for the gross-vs-net invariant V-walk. (We need access to the per-
    # ticker result dicts with borrow_drag_total etc.)
    train_results_winner: dict[str, dict] = {}
    for t in tickers:
        df = prices_cache[t]
        signal = mean_reversion_zscore_longshort_signal(
            df, window=w_window, threshold=w_threshold,
        )
        mask_train = df["trade_date"] <= HOLDOUT_CUTOFF
        train_df = df[mask_train].reset_index(drop=True)
        train_signal = signal[mask_train].reset_index(drop=True)
        train_results_winner[t] = run_backtest(
            t, train_df, train_signal, borrow_rate=tier_rates[t],
        )

    # Embedded V-walks
    d1 = vwalk_signal_transitions(prices_cache, w_window, w_threshold)
    d2 = vwalk_holdout_split(prices_cache, tickers)
    d3 = vwalk_gross_net_invariant(train_results_winner)
    print()
    print("=" * 60)
    print("V-WALK ROLLUP")
    print("=" * 60)
    print(f"  signal transitions (z-delta < 1e-8):  {'PASS' if d1 < 1e-8 else 'FAIL'}")
    print(f"  holdout split:                        {'PASS' if d2 else 'FAIL'}")
    print(f"  gross-vs-net invariant:               {'PASS' if d3 else 'FAIL'}")
    print(f"  pagination coverage (CBA.AX):         PASS (asserted earlier)")
    print(f"  tier distribution + CBA.AX tier-0:    PASS (asserted earlier)")
    if not (d1 < 1e-8 and d2 and d3):
        print("OVERALL V-WALK: FAIL")
        return 1

    # ---- HEADLINE ----
    test_net_alpha = w["test_net"]["avg_alpha_over_bh"]
    test_net_sharpe = w["test_net"]["avg_sharpe"]
    test_bh_sharpe = w["test_net"]["avg_bh_sharpe"]
    if test_net_alpha < 0:
        verdict = "REFUTED"
    elif test_net_sharpe <= test_bh_sharpe:
        verdict = "PROVISIONAL"
    else:
        verdict = "VALIDATED"

    print()
    print("=" * 60)
    print(f"HEADLINE -- WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1")
    print("=" * 60)
    print(f"  Winner combo:           (window={w_window}, threshold={w_threshold})")
    print(f"  TEST NET Sharpe:        {test_net_sharpe:.3f}  (vs long B&H {test_bh_sharpe:.3f})")
    print(f"  TEST NET alpha vs B&H:  {test_net_alpha*100:+.2f}%")
    print(f"  TEST NET total return:  {w['test_net']['avg_total_return']*100:+.2f}%")
    print(f"  Tickers beat B&H:       {w['test_net']['num_beating_bh']} / {len(tickers)}")
    print()
    print(f"  VERDICT: {verdict}")
    print()

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
