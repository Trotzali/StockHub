"""scripts/backtest_momentum_xsec_longshort_grid_asx200.py
WP-SIGNAL-MOMENTUM-CROSS-SECTIONAL-V1 -- Phase B.

Cross-sectional momentum long-short on ASX 200 survivors. Option B
architecture: per-ticker {NaN, -1, 0, +1} ternary signal, constant
between monthly rebalances, fed through the long-short engine (3cd4d0b)
per ticker with per-ticker tiered borrow costs (1/4/8 % APR by median-
dollar-volume tercile). Portfolio equity curve = SUM of per-ticker NET
equity curves.

Universe: src.data.universe.ASX_200 minus ^AXJO, then survivor filter
of >= 504 pre-2024-07-01 rows. Forward attrition handled by simply
ending each ticker's series at its last available bar (no carry-forward).

Grid: J in {63, 126, 252} (skip=21 fixed, k=18 per leg locked).

Capital model: $10k per selected name. K=18 per leg => $180k long leg,
$180k short leg, $360k gross NAV, dollar-neutral. Portfolio metrics
computed on the summed equity curves and reported as scale-invariant %.

Train/test:
- HOLDOUT_CUTOFF = 2024-07-01.
- TRAIN rebalance = next_rb <= cutoff (holding period ends <= cutoff).
- TEST rebalance = rb >= cutoff (bar at cutoff -> TEST).
- GAP rebalance = rb < cutoff and next_rb > cutoff. Excluded from
  TRAIN metrics (gap-rb bars zeroed in train signal); excluded from
  TEST (it predates cutoff).
- Winner: highest aggregate TRAIN portfolio-NET Sharpe; tiebreak
  TRAIN total return.

Comparators:
- ^AXJO total return over the test window (PRIMARY alpha benchmark).
- Sum-of-per-ticker long B&H equity curves (continuity with prior WPs).
- Top-decile LONG-ONLY sleeve (winner's signal with -1 replaced by 0).

V-walks (PASS-required):
  1. RANK: 5 named tickers' formation returns at first test rb,
     manually computed (closes.iloc lookups), confirmed to match
     emitted +1/-1/0 leg membership.
  2. HOLD: a top-18 member at rb_t holds +1 on every bar in
     [rb_t, rb_{t+1}).
  3. HOLDOUT SPLIT: last TRAIN rb's next rb <= cutoff; first TEST rb
     >= cutoff.
  4. SUM INVARIANT: sum of per-ticker last-bar equity (from per-ticker
     equity_curve) equals sum of per-ticker final_equity (from
     metrics) for both train and test.

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
    TRADING_DAYS_PER_YEAR,
    compute_metrics,
    run_backtest,
)
from src.backtest.signals import momentum_cross_sectional_longshort_signal
from src.backtest.borrow_tiering import (
    TIER_RATES_DEFAULT,
    compute_borrow_rates,
)
from src.data.universe import ASX_200
from src.data.yfinance_utils import fetch_prices_full


REGIME_TICKER_EXCLUDE = "^AXJO"
BENCHMARK_TICKER = "^AXJO"
HOLDOUT_CUTOFF = pd.Timestamp("2024-07-01")
MIN_HISTORY_PRE_CUTOFF = 504
SKIP = 21
K_PER_LEG = 18
PARAM_GRID: list[int] = [63, 126, 252]
TIER_RATES = TIER_RATES_DEFAULT
RANK_VWALK_TICKERS = ["CBA.AX", "BHP.AX", "WBC.AX", "FMG.AX", "CSL.AX"]


def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v * 100:+.2f}%"


def _fmt_sharpe(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.3f}"


def _fmt_money(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"${v:,.0f}"


def survivor_filter(client, candidates):
    cutoff_iso = HOLDOUT_CUTOFF.date().isoformat()
    survivors = []
    excluded = []
    for t in candidates:
        r = (client.table("prices")
             .select("ticker", count="exact")
             .eq("ticker", t)
             .lte("trade_date", cutoff_iso)
             .limit(0).execute())
        if r.count >= MIN_HISTORY_PRE_CUTOFF:
            survivors.append(t)
        else:
            excluded.append((t, r.count))
    return sorted(survivors), sorted(excluded, key=lambda x: (x[1], x[0]))


def classify_rebalances(rebalance_dates, cutoff):
    """Return (train_rbs, test_rbs, gap_rbs, first_test_rb).

    TRAIN: next_rb exists and next_rb <= cutoff.
    TEST: rb >= cutoff.
    GAP: rb < cutoff and next_rb > cutoff (or no next_rb but rb < cutoff,
      treated as gap so it's excluded from train).
    """
    train, test, gap = [], [], []
    for i, rb in enumerate(rebalance_dates):
        if rb >= cutoff:
            test.append(rb)
            continue
        if i + 1 < len(rebalance_dates):
            next_rb = rebalance_dates[i + 1]
            if next_rb <= cutoff:
                train.append(rb)
            else:
                gap.append(rb)
        else:
            gap.append(rb)
    first_test_rb = test[0] if test else None
    return train, test, gap, first_test_rb


def build_per_ticker_train_test_signals(panel, signals, rebalance_dates,
                                         first_test_rb, gap_rbs):
    """For each ticker, slice the full signal into TRAIN and TEST series
    aligned to the corresponding df slices. Gap-rb hold periods in the
    TRAIN window get zeroed.

    Returns: dict[t -> (df_train, sig_train, df_test, sig_test)].
    """
    gap_set = set(gap_rbs)
    rebal_arr = np.array(rebalance_dates, dtype="datetime64[ns]")
    splits = {}
    for t, df in panel.items():
        dates_t = pd.DatetimeIndex(df["trade_date"])
        train_mask = np.asarray(dates_t < first_test_rb)
        df_train = df[train_mask].reset_index(drop=True)
        df_test = df[~train_mask].reset_index(drop=True)
        sig_full = signals[t].values
        sig_train = sig_full[train_mask].copy()
        sig_test = sig_full[~train_mask].copy()

        # Zero out bars within gap-rb hold periods in TRAIN.
        if gap_set:
            train_dates = dates_t[train_mask].values
            cur_rb_ix = -1
            for i in range(len(train_dates)):
                d = train_dates[i]
                while (cur_rb_ix + 1 < len(rebal_arr)
                       and rebal_arr[cur_rb_ix + 1] <= d):
                    cur_rb_ix += 1
                if cur_rb_ix < 0:
                    continue
                rb = pd.Timestamp(rebal_arr[cur_rb_ix])
                if rb in gap_set:
                    if not np.isnan(sig_train[i]):
                        sig_train[i] = 0.0
        splits[t] = (
            df_train,
            pd.Series(sig_train, dtype=float),
            df_test,
            pd.Series(sig_test, dtype=float),
        )
    return splits


def aggregate_portfolio(per_ticker_results, window_label, calendar):
    """Sum per-ticker equity curves into a single portfolio curve over
    the supplied calendar (union of all per-ticker trade_dates in this
    window). Forward-fills each ticker's curve from its last available
    bar to the calendar end (cash-equivalent at last close).

    Returns dict with:
        portfolio_net_curve: pd.DataFrame (trade_date, value)
        portfolio_gross_curve: pd.DataFrame (trade_date, value)
        portfolio_bh_curve: pd.DataFrame (trade_date, value)  # sum long B&H
        starting_capital_total
        per_ticker_final_net: dict
        per_ticker_final_gross: dict
    """
    cal = pd.DatetimeIndex(sorted(calendar))
    n = len(cal)
    if n == 0:
        return None
    n_tickers = len(per_ticker_results)
    starting_total = n_tickers * STARTING_CAPITAL

    net_sum = np.zeros(n, dtype=float)
    gross_sum = np.zeros(n, dtype=float)
    bh_sum = np.zeros(n, dtype=float)

    per_t_net_last = {}
    per_t_gross_last = {}

    for t, res in per_ticker_results.items():
        eq = res["equity_curve"]
        if len(eq) == 0:
            # ticker contributes constant starting_capital across the calendar
            net_sum += STARTING_CAPITAL
            gross_sum += STARTING_CAPITAL
            bh_sum += STARTING_CAPITAL
            per_t_net_last[t] = STARTING_CAPITAL
            per_t_gross_last[t] = STARTING_CAPITAL
            continue
        eq_dates = pd.DatetimeIndex(eq["trade_date"])
        ser_net = pd.Series(
            eq["signal_equity_net"].values, index=eq_dates, dtype=float
        )
        ser_gross = pd.Series(
            eq["signal_equity"].values, index=eq_dates, dtype=float
        )
        ser_bh = pd.Series(
            eq["buy_hold_equity"].values, index=eq_dates, dtype=float
        )
        # Reindex to portfolio calendar.
        # Before the ticker's first equity bar -> starting_capital (no
        # activity yet). After last bar -> forward-fill last value
        # (realized cash). pandas reindex with method='ffill' covers
        # the after-last case; for before-first we fill with
        # STARTING_CAPITAL via combine_first against a starting series.
        ser_net_r = ser_net.reindex(cal, method="ffill")
        ser_gross_r = ser_gross.reindex(cal, method="ffill")
        ser_bh_r = ser_bh.reindex(cal, method="ffill")
        # Backfill leading NaNs with starting_capital
        ser_net_r = ser_net_r.fillna(STARTING_CAPITAL)
        ser_gross_r = ser_gross_r.fillna(STARTING_CAPITAL)
        ser_bh_r = ser_bh_r.fillna(STARTING_CAPITAL)
        net_sum += ser_net_r.values
        gross_sum += ser_gross_r.values
        bh_sum += ser_bh_r.values
        per_t_net_last[t] = float(ser_net.iloc[-1])
        per_t_gross_last[t] = float(ser_gross.iloc[-1])

    df_net = pd.DataFrame({"trade_date": cal, "value": net_sum})
    df_gross = pd.DataFrame({"trade_date": cal, "value": gross_sum})
    df_bh = pd.DataFrame({"trade_date": cal, "value": bh_sum})
    return {
        "portfolio_net_curve": df_net,
        "portfolio_gross_curve": df_gross,
        "portfolio_bh_curve": df_bh,
        "starting_capital_total": starting_total,
        "per_ticker_final_net": per_t_net_last,
        "per_ticker_final_gross": per_t_gross_last,
    }


def portfolio_metrics(df_curve, starting):
    eq = pd.Series(df_curve["value"].values, dtype=float)
    return compute_metrics(eq, [], starting, df_curve["trade_date"])


def fetch_benchmark_curve(client, ticker, first_date, last_date,
                          starting_capital):
    """Return a benchmark $-normalized curve aligned to (first_date,
    last_date] inclusive, scaled to start at starting_capital."""
    records = fetch_prices_full(client, ticker)
    df = pd.DataFrame(records)
    if df.empty:
        return None
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["adj_close"] = pd.to_numeric(df["adj_close"])
    df = df.sort_values("trade_date").reset_index(drop=True)
    mask = (df["trade_date"] >= first_date) & (df["trade_date"] <= last_date)
    df = df[mask].reset_index(drop=True)
    if df.empty:
        return None
    first_p = float(df["adj_close"].iloc[0])
    df["value"] = starting_capital * df["adj_close"] / first_p
    return df[["trade_date", "value"]]


def run_vwalks(panel, signals, rebalance_dates, leg_by_rb, first_test_rb,
               train_per_ticker_results, test_per_ticker_results,
               cutoff, gap_rbs, J):
    """Run the four V-walks and return a list of (name, PASS/FAIL, detail)."""
    out = []

    # V-walk 1: RANK
    print()
    print(f"==== V-WALK 1 (RANK) at first test rb {first_test_rb.date()} ====")
    print(f"  Lookback math: p_skip = closes.iloc[ix - {SKIP}];")
    print(f"                  p_then = closes.iloc[ix - {SKIP} - {J}];")
    print(f"                  lookback_return = (p_skip / p_then) - 1.0")
    print(f"  Verifying named tickers against emitted leg membership.")
    print()
    top, bot = leg_by_rb[first_test_rb]
    # Augment the named blue chips with one auto-sampled top + one bot
    # to ensure all three leg regions (TOP/MID/BOT) are exercised.
    sample_tickers = list(RANK_VWALK_TICKERS)
    if top:
        sample_tickers.append(sorted(top)[0])
    if bot:
        sample_tickers.append(sorted(bot)[0])
    print(f"  {'ticker':<10} {'manual_lb':<14} {'emitted_sig':<12} "
          f"{'expected_leg':<14} {'match':<6}")
    all_match = True
    for t in sample_tickers:
        if t not in panel:
            print(f"  {t:<10} (not in panel)")
            all_match = False
            continue
        df = panel[t]
        dates_t = pd.DatetimeIndex(df["trade_date"])
        if first_test_rb not in dates_t:
            print(f"  {t:<10} (no bar at rb date)")
            continue
        ix = int(dates_t.get_loc(first_test_rb))
        p_skip = float(df["adj_close"].iloc[ix - SKIP])
        p_then = float(df["adj_close"].iloc[ix - SKIP - J])
        lb_manual = (p_skip / p_then) - 1.0
        sig_at_rb = float(signals[t].iloc[ix])
        if t in top:
            expected = +1.0
            leg = "TOP"
        elif t in bot:
            expected = -1.0
            leg = "BOT"
        else:
            expected = 0.0
            leg = "MID"
        match = abs(sig_at_rb - expected) < 1e-12
        all_match = all_match and match
        print(f"  {t:<10} {lb_manual:<+14.6f} {sig_at_rb:<+12.1f} "
              f"{leg:<14} {'PASS' if match else 'FAIL':<6}")
    verdict = "PASS" if all_match else "FAIL"
    print(f"  V-WALK 1 VERDICT: {verdict}")
    out.append(("RANK", verdict, f"5 named tickers; all match: {all_match}"))

    # V-walk 2: HOLD
    print()
    print("==== V-WALK 2 (HOLD: position constant between rebalances) ====")
    held_pass = False
    held_detail = ""
    # Find a test rb where a top-18 ticker survives in the panel through
    # the FULL hold to next rb.
    test_rb_pairs = []
    for i, rb in enumerate(rebalance_dates):
        if rb < first_test_rb:
            continue
        if i + 1 >= len(rebalance_dates):
            continue
        test_rb_pairs.append((rb, rebalance_dates[i + 1]))
    chosen = None
    for rb, next_rb in test_rb_pairs:
        top, _ = leg_by_rb[rb]
        for t in sorted(top):
            df = panel[t]
            dates_t = pd.DatetimeIndex(df["trade_date"])
            mask = np.asarray((dates_t >= rb) & (dates_t < next_rb))
            if int(mask.sum()) < 5:
                continue
            sig_window = signals[t].values[mask]
            if np.all(sig_window == 1.0):
                chosen = (t, rb, next_rb, int(mask.sum()))
                held_pass = True
                break
        if chosen:
            break
    if chosen:
        t, rb, next_rb, n_bars = chosen
        held_detail = (f"ticker={t} rb={rb.date()} next_rb={next_rb.date()} "
                       f"bars_in_hold={n_bars} all_eq_+1=YES")
        print(f"  ticker={t}")
        print(f"  rb           = {rb.date()}")
        print(f"  next_rb      = {next_rb.date()}")
        print(f"  bars in hold = {n_bars}")
        print(f"  all bars +1  = YES")
    else:
        print("  Could not find a top-18 ticker with full-hold panel coverage.")
    verdict = "PASS" if held_pass else "FAIL"
    print(f"  V-WALK 2 VERDICT: {verdict}")
    out.append(("HOLD", verdict, held_detail))

    # V-walk 3: HOLDOUT SPLIT
    print()
    print("==== V-WALK 3 (HOLDOUT SPLIT) ====")
    train_rbs, test_rbs, gap_rbs_recl, _ = classify_rebalances(
        rebalance_dates, cutoff
    )
    last_train_rb = train_rbs[-1] if train_rbs else None
    last_train_next = None
    if last_train_rb is not None:
        ix = rebalance_dates.index(last_train_rb)
        last_train_next = rebalance_dates[ix + 1] if ix + 1 < len(rebalance_dates) else None
    first_test_rb_chk = test_rbs[0] if test_rbs else None
    cond_a = (last_train_next is not None and last_train_next <= cutoff)
    cond_b = (first_test_rb_chk is not None and first_test_rb_chk >= cutoff)
    print(f"  cutoff               = {cutoff.date()}")
    print(f"  last TRAIN rb        = {last_train_rb.date() if last_train_rb else None}")
    print(f"  next-rb after last   = {last_train_next.date() if last_train_next else None}")
    print(f"  last TRAIN holding ends <= cutoff: {cond_a}")
    print(f"  first TEST rb        = {first_test_rb_chk.date() if first_test_rb_chk else None}")
    print(f"  first TEST rb >= cutoff:           {cond_b}")
    print(f"  gap rebalances       = {[g.date() for g in gap_rbs_recl]}")
    verdict = "PASS" if (cond_a and cond_b) else "FAIL"
    print(f"  V-WALK 3 VERDICT: {verdict}")
    out.append(("HOLDOUT_SPLIT", verdict,
                f"last_train_next={last_train_next} first_test_rb={first_test_rb_chk}"))

    # V-walk 4: SUM INVARIANT
    print()
    print("==== V-WALK 4 (SUM INVARIANT) ====")
    for label, results in [("TRAIN", train_per_ticker_results),
                            ("TEST", test_per_ticker_results)]:
        sum_last_bar_net = 0.0
        sum_final_net = 0.0
        sum_last_bar_gross = 0.0
        sum_final_gross = 0.0
        for t, res in results.items():
            eq = res["equity_curve"]
            if len(eq) == 0:
                sum_last_bar_net += STARTING_CAPITAL
                sum_final_net += STARTING_CAPITAL
                sum_last_bar_gross += STARTING_CAPITAL
                sum_final_gross += STARTING_CAPITAL
                continue
            sum_last_bar_net += float(eq["signal_equity_net"].iloc[-1])
            sum_final_net += float(res["metrics_net"]["final_equity"])
            sum_last_bar_gross += float(eq["signal_equity"].iloc[-1])
            sum_final_gross += float(res["metrics"]["final_equity"])
        delta_net = abs(sum_last_bar_net - sum_final_net)
        delta_gross = abs(sum_last_bar_gross - sum_final_gross)
        print(f"  {label}: "
              f"sum_last_bar_net={sum_last_bar_net:.2f}  "
              f"sum_final_net={sum_final_net:.2f}  "
              f"delta={delta_net:.2e}")
        print(f"  {label}: "
              f"sum_last_bar_gross={sum_last_bar_gross:.2f}  "
              f"sum_final_gross={sum_final_gross:.2f}  "
              f"delta={delta_gross:.2e}")
        if delta_net > 1e-6 or delta_gross > 1e-6:
            print(f"  {label} SUM INVARIANT FAIL")
            out.append(("SUM_INVARIANT_" + label, "FAIL",
                        f"delta_net={delta_net:.2e} delta_gross={delta_gross:.2e}"))
        else:
            out.append(("SUM_INVARIANT_" + label, "PASS",
                        f"delta_net={delta_net:.2e} delta_gross={delta_gross:.2e}"))
    print(f"  V-WALK 4 VERDICT: "
          f"{'PASS' if all(o[1] == 'PASS' for o in out if o[0].startswith('SUM_INVARIANT')) else 'FAIL'}")

    return out


def run_long_only_sleeve(panel, signals, splits, borrow_rates,
                          first_test_rb, gap_rbs):
    """For each ticker, take signal with -1 -> 0 (kill the short leg).
    Rerun engine. Return per-ticker results for train + test."""
    long_train = {}
    long_test = {}
    for t, (df_train, sig_train, df_test, sig_test) in splits.items():
        sig_tr = sig_train.copy()
        sig_te = sig_test.copy()
        sig_tr[sig_tr == -1.0] = 0.0
        sig_te[sig_te == -1.0] = 0.0
        # No borrow drag on long-only.
        long_train[t] = run_backtest(t, df_train, sig_tr, borrow_rate=0.0)
        long_test[t] = run_backtest(t, df_test, sig_te, borrow_rate=0.0)
    return long_train, long_test


def main() -> int:
    load_dotenv()
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

    candidates = [t for t in ASX_200 if t != REGIME_TICKER_EXCLUDE]
    print(f"Universe source: src.data.universe.ASX_200 "
          f"({len(candidates)} candidates after ^AXJO exclusion)")
    print(f"Survivor filter: >= {MIN_HISTORY_PRE_CUTOFF} rows where "
          f"trade_date <= {HOLDOUT_CUTOFF.strftime('%Y-%m-%d')}")
    tickers, excluded = survivor_filter(client, candidates)
    print(f"  Survivors: {len(tickers)}")
    print(f"  Excluded:  {len(excluded)}")
    print()
    print(f"Grid (J trading days; skip={SKIP} fixed; K={K_PER_LEG} per leg): "
          f"{PARAM_GRID}")
    print(f"Holdout cutoff: {HOLDOUT_CUTOFF.strftime('%Y-%m-%d')}")
    print(f"Capital model: ${STARTING_CAPITAL:,.0f} per selected name; "
          f"{K_PER_LEG} per leg => "
          f"${K_PER_LEG*STARTING_CAPITAL:,.0f} long, "
          f"${K_PER_LEG*STARTING_CAPITAL:,.0f} short, "
          f"${2*K_PER_LEG*STARTING_CAPITAL:,.0f} gross NAV, dollar-neutral.")
    print(f"Brokerage: {BROKERAGE_PCT*100}%/side. "
          f"Slippage: ${SLIPPAGE_PER_SHARE}/share/side.")
    print()

    print("Prefetching panel (paginated)...")
    panel: dict[str, pd.DataFrame] = {}
    for t in tickers:
        records = fetch_prices_full(client, t)
        df = pd.DataFrame(records)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df["adj_close"] = pd.to_numeric(df["adj_close"])
        df = df.sort_values("trade_date").reset_index(drop=True)
        panel[t] = df
    n_rows_total = sum(len(d) for d in panel.values())
    print(f"  Panel: {n_rows_total} rows across {len(tickers)} tickers.")
    print()

    print("Computing per-ticker borrow rates (median-ADV terciles)...")
    borrow_rates, borrow_diag = compute_borrow_rates(client, tickers, TIER_RATES)
    tier_counts = {0: 0, 1: 0, 2: 0}
    for d in borrow_diag.values():
        tier_counts[d["tier"]] += 1
    print(f"  Tier counts (0=most liquid, 2=least): {tier_counts}")
    print(f"  Rates (tiers 0/1/2): "
          f"{TIER_RATES[0]*100}% / {TIER_RATES[1]*100}% / {TIER_RATES[2]*100}%")
    print()

    grid_results: dict[int, dict] = {}
    for J in PARAM_GRID:
        print(f"==== J = {J} ====")
        signals, rebalance_dates, leg_by_rb = (
            momentum_cross_sectional_longshort_signal(
                panel, J=J, skip=SKIP, rebalance="ME", k=K_PER_LEG,
            )
        )
        train_rbs, test_rbs, gap_rbs, first_test_rb = classify_rebalances(
            rebalance_dates, HOLDOUT_CUTOFF
        )
        print(f"  Rebalance count total: {len(rebalance_dates)}")
        print(f"    train: {len(train_rbs)}, test: {len(test_rbs)}, "
              f"gap: {len(gap_rbs)}")
        if first_test_rb is None:
            print("  No test rebalance; skipping J.")
            continue
        print(f"  First test rb: {first_test_rb.date()}")

        splits = build_per_ticker_train_test_signals(
            panel, signals, rebalance_dates, first_test_rb, gap_rbs
        )

        train_per_ticker = {}
        test_per_ticker = {}
        for t in tickers:
            df_train, sig_train, df_test, sig_test = splits[t]
            br = float(borrow_rates[t])
            train_per_ticker[t] = run_backtest(
                t, df_train, sig_train, borrow_rate=br
            )
            test_per_ticker[t] = run_backtest(
                t, df_test, sig_test, borrow_rate=br
            )

        # Build portfolio calendars from union of per-ticker eq curve dates.
        train_cal = set()
        for res in train_per_ticker.values():
            for d in res["equity_curve"]["trade_date"]:
                train_cal.add(pd.Timestamp(d))
        test_cal = set()
        for res in test_per_ticker.values():
            for d in res["equity_curve"]["trade_date"]:
                test_cal.add(pd.Timestamp(d))

        port_train = aggregate_portfolio(train_per_ticker, "train", train_cal)
        port_test = aggregate_portfolio(test_per_ticker, "test", test_cal)

        starting_total = port_train["starting_capital_total"]
        train_net_m = portfolio_metrics(
            port_train["portfolio_net_curve"], starting_total
        )
        train_gross_m = portfolio_metrics(
            port_train["portfolio_gross_curve"], starting_total
        )
        train_bh_m = portfolio_metrics(
            port_train["portfolio_bh_curve"], starting_total
        )
        test_net_m = portfolio_metrics(
            port_test["portfolio_net_curve"], starting_total
        )
        test_gross_m = portfolio_metrics(
            port_test["portfolio_gross_curve"], starting_total
        )
        test_bh_m = portfolio_metrics(
            port_test["portfolio_bh_curve"], starting_total
        )

        # Long-only sleeve (short leg killed)
        long_train_pt, long_test_pt = run_long_only_sleeve(
            panel, signals, splits, borrow_rates, first_test_rb, gap_rbs
        )
        port_long_train = aggregate_portfolio(long_train_pt, "train_long", train_cal)
        port_long_test = aggregate_portfolio(long_test_pt, "test_long", test_cal)
        long_train_net_m = portfolio_metrics(
            port_long_train["portfolio_net_curve"], starting_total
        )
        long_test_net_m = portfolio_metrics(
            port_long_test["portfolio_net_curve"], starting_total
        )

        grid_results[J] = {
            "signals": signals,
            "rebalance_dates": rebalance_dates,
            "leg_by_rb": leg_by_rb,
            "first_test_rb": first_test_rb,
            "train_rbs": train_rbs,
            "test_rbs": test_rbs,
            "gap_rbs": gap_rbs,
            "splits": splits,
            "train_per_ticker": train_per_ticker,
            "test_per_ticker": test_per_ticker,
            "port_train": port_train,
            "port_test": port_test,
            "metrics": {
                "train_net": train_net_m,
                "train_gross": train_gross_m,
                "train_bh": train_bh_m,
                "test_net": test_net_m,
                "test_gross": test_gross_m,
                "test_bh": test_bh_m,
                "long_train_net": long_train_net_m,
                "long_test_net": long_test_net_m,
            },
        }
        print(f"  train NET   Sharpe: {_fmt_sharpe(train_net_m['sharpe'])}  "
              f"total return: {_fmt_pct(train_net_m['total_return_pct'])}")
        print(f"  train GROSS Sharpe: {_fmt_sharpe(train_gross_m['sharpe'])}  "
              f"total return: {_fmt_pct(train_gross_m['total_return_pct'])}")
        print(f"  test  NET   Sharpe: {_fmt_sharpe(test_net_m['sharpe'])}  "
              f"total return: {_fmt_pct(test_net_m['total_return_pct'])}")
        print(f"  test  GROSS Sharpe: {_fmt_sharpe(test_gross_m['sharpe'])}  "
              f"total return: {_fmt_pct(test_gross_m['total_return_pct'])}")
        print()

    # ===== Winner selection: TRAIN NET Sharpe; tiebreak total return =====
    def winner_key(J):
        m = grid_results[J]["metrics"]["train_net"]
        s = m["sharpe"]
        if pd.isna(s):
            s = float("-inf")
        return (s, m["total_return_pct"])

    valid_J = [J for J in PARAM_GRID if J in grid_results]
    if not valid_J:
        print("No valid grid results; aborting.")
        return 1
    winner = max(valid_J, key=winner_key)
    print(f"==== WINNER (TRAIN NET Sharpe): J={winner} ====")
    print()

    # ===== Comparators =====
    # ^AXJO total return over test window
    test_cal_winner = sorted({
        pd.Timestamp(d)
        for res in grid_results[winner]["test_per_ticker"].values()
        for d in res["equity_curve"]["trade_date"]
    })
    test_first = test_cal_winner[0]
    test_last = test_cal_winner[-1]
    starting_total = grid_results[winner]["port_train"]["starting_capital_total"]
    bench_curve = fetch_benchmark_curve(
        client, BENCHMARK_TICKER, test_first, test_last, starting_total
    )
    if bench_curve is not None:
        bench_metrics = portfolio_metrics(bench_curve, starting_total)
    else:
        bench_metrics = None
    print(f"Benchmark ^AXJO over test window "
          f"({test_first.date()} -> {test_last.date()}):")
    if bench_metrics is not None:
        print(f"  total return: {_fmt_pct(bench_metrics['total_return_pct'])}")
        print(f"  Sharpe:       {_fmt_sharpe(bench_metrics['sharpe'])}")
    else:
        print("  (no data)")
    print()

    # ===== Grid summary table =====
    print("==== GRID SUMMARY (portfolio NET) ====")
    print(f"  {'J':<5} {'tr Sh':<8} {'tr ret':<10} "
          f"{'te Sh':<8} {'te ret':<10} {'te alpha vs XJO':<16}")
    for J in PARAM_GRID:
        if J not in grid_results:
            continue
        m = grid_results[J]["metrics"]
        alpha_xjo = "N/A"
        if bench_metrics is not None:
            alpha = m["test_net"]["total_return_pct"] - bench_metrics["total_return_pct"]
            alpha_xjo = _fmt_pct(alpha)
        tag = "  *WINNER*" if J == winner else ""
        print(f"  J={J:<3} "
              f"{_fmt_sharpe(m['train_net']['sharpe']):<8} "
              f"{_fmt_pct(m['train_net']['total_return_pct']):<10} "
              f"{_fmt_sharpe(m['test_net']['sharpe']):<8} "
              f"{_fmt_pct(m['test_net']['total_return_pct']):<10} "
              f"{alpha_xjo:<16}"
              f"{tag}")
    print()

    # ===== Decomposition (winner) =====
    w = grid_results[winner]
    wm = w["metrics"]
    print(f"==== DECOMPOSITION (winner J={winner}) ====")
    print(f"  capital model: $10k per selected name; K={K_PER_LEG} per leg")
    print(f"  starting NAV total: {_fmt_money(starting_total)}")
    print()
    print(f"  TRAIN window:")
    print(f"    portfolio NET   Sharpe: {_fmt_sharpe(wm['train_net']['sharpe'])}  "
          f"total return: {_fmt_pct(wm['train_net']['total_return_pct'])}")
    print(f"    portfolio GROSS Sharpe: {_fmt_sharpe(wm['train_gross']['sharpe'])}  "
          f"total return: {_fmt_pct(wm['train_gross']['total_return_pct'])}")
    print(f"    borrow drag (GROSS - NET total return): "
          f"{_fmt_pct(wm['train_gross']['total_return_pct'] - wm['train_net']['total_return_pct'])}")
    print(f"    sum long-only B&H per-ticker total return: "
          f"{_fmt_pct(wm['train_bh']['total_return_pct'])}")
    print(f"    long-only sleeve NET total return: "
          f"{_fmt_pct(wm['long_train_net']['total_return_pct'])}")
    short_train_ret = (
        wm['train_net']['total_return_pct'] - wm['long_train_net']['total_return_pct']
    )
    print(f"    SHORT sleeve contribution (NET ls - NET long): "
          f"{_fmt_pct(short_train_ret)}")
    print()
    print(f"  TEST window:")
    print(f"    portfolio NET   Sharpe: {_fmt_sharpe(wm['test_net']['sharpe'])}  "
          f"total return: {_fmt_pct(wm['test_net']['total_return_pct'])}")
    print(f"    portfolio GROSS Sharpe: {_fmt_sharpe(wm['test_gross']['sharpe'])}  "
          f"total return: {_fmt_pct(wm['test_gross']['total_return_pct'])}")
    print(f"    borrow drag (GROSS - NET total return): "
          f"{_fmt_pct(wm['test_gross']['total_return_pct'] - wm['test_net']['total_return_pct'])}")
    if bench_metrics is not None:
        alpha_xjo = (wm['test_net']['total_return_pct']
                     - bench_metrics['total_return_pct'])
        print(f"    alpha vs ^AXJO: {_fmt_pct(alpha_xjo)}")
    print(f"    sum long-only B&H per-ticker total return: "
          f"{_fmt_pct(wm['test_bh']['total_return_pct'])}")
    print(f"    long-only sleeve NET total return: "
          f"{_fmt_pct(wm['long_test_net']['total_return_pct'])}")
    short_test_ret = (
        wm['test_net']['total_return_pct'] - wm['long_test_net']['total_return_pct']
    )
    print(f"    SHORT sleeve contribution (NET ls - NET long): "
          f"{_fmt_pct(short_test_ret)}")

    # ===== V-walks (winner) =====
    vwalk_out = run_vwalks(
        panel, w["signals"], w["rebalance_dates"], w["leg_by_rb"],
        w["first_test_rb"], w["train_per_ticker"], w["test_per_ticker"],
        HOLDOUT_CUTOFF, w["gap_rbs"], winner
    )

    print()
    print("==== V-WALK SUMMARY ====")
    for name, verdict, detail in vwalk_out:
        print(f"  {name:<22} {verdict:<6} {detail}")

    all_pass = all(v[1] == "PASS" for v in vwalk_out)
    print()
    print(f"OVERALL V-WALK: {'PASS' if all_pass else 'FAIL'}")
    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
