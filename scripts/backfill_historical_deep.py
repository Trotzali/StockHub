"""WP-DIAG-FACTOR-REGIME-CONFOUND Phase B (S13): deep-history backfill.

Extends the daily-price store back to yfinance's earliest available bar
(period="max") for the 185 ASX-200 survivors + ^AXJO benchmark. Same
schema, same on_conflict=(ticker,trade_date) upsert -- idempotent
re-runs, no dupes possible.

Rationale: Phase A's regime-confound diagnostic found only N=6 DOWN
forward-12m windows in 2021-2025 (partial support, under-powered).
Multi-cycle history (GFC 2008-09, 2011 EU crisis, 2015-16 commodities,
COVID 2020, 2022 pullback) materially populates the DOWN bucket for
the low-vol re-screen. Gating commit: 488d247.

Survivorship caveat (mandatory to state at every consumer): deep history
on TODAY's 185 survivors deletes blown-up names, systematically skewing
against high-vol survival. This BIASES a low-vol re-screen TOWARD
high-vol outperformance, i.e. AGAINST the low-vol hypothesis. A positive
low-vol result on this data is therefore conservative/robust; a negative
result remains ambiguous because we cannot separate "no anomaly" from
"survivorship-eaten-anomaly". Deep-history screens on this cohort are
directional multi-regime colour, not clean tests.

Usage:
    python scripts/backfill_historical_deep.py --dry-run
    python scripts/backfill_historical_deep.py --tickers CBA.AX
    python scripts/backfill_historical_deep.py

ASCII-only stdout per CLAUDE.md item 8.
"""
import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from supabase import create_client, Client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data.yfinance_utils import df_to_records, upsert_prices
from src.data.universe import ASX_200

BENCHMARK_TICKER = "^AXJO"
FETCH_PERIOD = "max"
RETRY_DELAYS = (1, 2, 4)
WARN_MIN_ROWS = 2000  # ~8 years of trading days
HOLDOUT_CUTOFF = pd.Timestamp("2024-07-01")
MIN_HISTORY_PRE_CUTOFF = 504

NOT_NULL_PRICE_COLS = [
    "open", "high", "low", "close", "adj_close", "volume",
]


def survivor_filter(client, candidates):
    """Return survivors: tickers with >= MIN_HISTORY_PRE_CUTOFF rows in
    the current prices table where trade_date <= HOLDOUT_CUTOFF.
    Deterministic across sessions (mirrors prior WPs)."""
    cutoff_iso = HOLDOUT_CUTOFF.date().isoformat()
    survivors = []
    for t in candidates:
        r = (client.table("prices")
             .select("ticker", count="exact")
             .eq("ticker", t)
             .lte("trade_date", cutoff_iso)
             .limit(0).execute())
        if r.count >= MIN_HISTORY_PRE_CUTOFF:
            survivors.append(t)
    return sorted(survivors)


def fetch_history_with_retry(ticker):
    """yf.Ticker(t).history with 3-attempt exponential backoff."""
    last_exc = None
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            return yf.Ticker(ticker).history(
                period=FETCH_PERIOD, auto_adjust=False,
            )
        except Exception as exc:
            last_exc = exc
            print(f"  {ticker} attempt {attempt} failed: {exc}; "
                  f"retrying in {delay}s")
            time.sleep(delay)
    raise RuntimeError(
        f"yf.Ticker({ticker}).history failed after "
        f"{len(RETRY_DELAYS)} attempts"
    ) from last_exc


def reshape_ticker_history(ticker, df):
    """Tidy yf.Ticker.history output for df_to_records (schema-matching)."""
    df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    })
    df = df.reset_index().rename(columns={"Date": "trade_date"})
    df["ticker"] = ticker
    return df


def process_ticker(client, ticker, dry_run):
    raw = fetch_history_with_retry(ticker)
    if not isinstance(raw, pd.DataFrame) or raw.empty:
        print(f"  SKIP {ticker:<10} yfinance returned empty frame")
        return {"ticker": ticker, "rows": 0, "warn": True, "dropped": 0,
                "date_min": None, "date_max": None}
    tidy = reshape_ticker_history(ticker, raw)

    before = len(tidy)
    tidy = tidy.dropna(subset=NOT_NULL_PRICE_COLS)
    dropped_nan = before - len(tidy)

    # Drop zero/negative-volume rows (defensive intraday-filter parity).
    # Index rows (^AXJO) legitimately have volume=0 in yfinance -- do not
    # drop those; adjust filter to exclude non-index tickers only.
    if ticker != BENCHMARK_TICKER:
        zero_vol_mask = tidy["volume"].isna() | (tidy["volume"] <= 0)
        zero_vol_n = int(zero_vol_mask.sum())
        if zero_vol_n:
            print(f"  FILTERED {ticker}: dropped {zero_vol_n} "
                  f"zero-or-negative-volume rows")
            tidy = tidy.loc[~zero_vol_mask]

    records = df_to_records(tidy)
    n = len(records)

    if not dry_run and n:
        upsert_prices(client, records)  # chunked, on_conflict=(ticker,trade_date)

    date_min = tidy["trade_date"].min() if n else None
    date_max = tidy["trade_date"].max() if n else None
    warn = n < WARN_MIN_ROWS
    flag = "WARN" if warn else "OK  "
    print(
        f"  {flag} {ticker:<10} rows={n:>6}  "
        f"range={date_min}..{date_max}  dropped_nan={dropped_nan}"
    )
    return {"ticker": ticker, "rows": n, "warn": warn,
            "dropped": dropped_nan,
            "date_min": str(date_min.date()) if date_min else None,
            "date_max": str(date_max.date()) if date_max else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch and reshape only; skip DB upsert.",
    )
    parser.add_argument(
        "--tickers", type=str, default=None,
        help="Comma-separated ticker override (e.g. 'CBA.AX,BHP.AX'). "
             "Default: all 185 survivors + ^AXJO.",
    )
    args = parser.parse_args()

    load_dotenv()
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

    if args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
        print(f"Explicit ticker list ({len(tickers)}): {tickers}")
    else:
        candidates = [t for t in ASX_200 if t != BENCHMARK_TICKER]
        survivors = survivor_filter(client, candidates)
        tickers = survivors + [BENCHMARK_TICKER]
        print(f"Survivor set: {len(survivors)}; "
              f"benchmark added -> total {len(tickers)}")

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    print(f"Deep backfill (period={FETCH_PERIOD}) mode={mode}")
    print(f"On-conflict: (ticker,trade_date) upsert; idempotent re-runs.")
    print()

    results = []
    for i, t in enumerate(tickers):
        try:
            results.append(process_ticker(client, t, args.dry_run))
        except Exception as e:
            print(f"  FAIL {t:<10} {str(e)[:80]}")
            results.append({"ticker": t, "rows": 0, "warn": True,
                            "dropped": 0, "date_min": None, "date_max": None,
                            "error": str(e)[:80]})
        if (i + 1) % 20 == 0:
            print(f"  ... {i+1}/{len(tickers)} processed")

    total = sum(r["rows"] for r in results)
    warned = [r["ticker"] for r in results if r["warn"]]
    print()
    print("==== COVERAGE TABLE ====")
    print(f"  {'ticker':<10} {'rows':>7} {'first':<12} {'last':<12} {'flag':<6}")
    for r in results:
        flag = "WARN" if r["warn"] else "OK"
        print(f"  {r['ticker']:<10} {r['rows']:>7} "
              f"{str(r.get('date_min')):<12} "
              f"{str(r.get('date_max')):<12} {flag:<6}")
    print()
    print(f"Total rows: {total}")
    print(f"Tickers processed: {len(results)}")
    if warned:
        print(f"WARN (< {WARN_MIN_ROWS} rows): {warned}")
    else:
        print("WARN: none")
    if args.dry_run:
        print("DRY-RUN -- no DB writes performed.")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
