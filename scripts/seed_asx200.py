"""WP-DATA-UNIVERSE-ASX200 — one-shot seed for the full S&P/ASX 200 universe.

For every ticker in src.data.universe.ASX_200 that is not already in
the Supabase `stocks` table, upserts the stocks row and backfills 5y
of daily OHLCV via per-ticker yf.Ticker.history. Mirrors the per-ticker
pattern from scripts/backfill_historical.py (NaN drop + volume<=0
filter from WP-INFRA-INTRADAY-FILTER, fe9100e).

Idempotent via existing on_conflict=(ticker,trade_date) on prices and
on_conflict=(ticker) on stocks. Safe to rerun on partial failure.

Single-ticker failures (delisted, fetch error, empty response) are
logged and skipped; the run continues. Final summary reports
attempted/succeeded/failed.

ASCII-only stdout per CLAUDE.md item 8.

TODO: WP-INFRA-YFUTILS-PERTICKER-INGEST will consolidate this
per-ticker fetch+reshape+filter+upsert pattern (now inlined in
backfill_historical.py + seed_asx200.py) into src/data/yfinance_utils.py
once a 3rd consumer materialises.

Usage:
    python scripts/seed_asx200.py
"""
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from supabase import create_client, Client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data.universe import ASX_200, TICKERS
from src.data.yfinance_utils import df_to_records, upsert_prices

FETCH_PERIOD = "5y"
RETRY_DELAYS = (1, 2, 4)

NOT_NULL_PRICE_COLS = [
    "open", "high", "low", "close", "adj_close", "volume",
]


def fetch_history_with_retry(ticker: str) -> pd.DataFrame:
    """yf.Ticker(t).history with 3-attempt exponential backoff."""
    last_exc: Optional[Exception] = None
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            return yf.Ticker(ticker).history(
                period=FETCH_PERIOD, auto_adjust=False,
            )
        except Exception as exc:
            last_exc = exc
            print(
                f"    {ticker} attempt {attempt} failed: {exc}; "
                f"retrying in {delay}s"
            )
            time.sleep(delay)
    raise RuntimeError(
        f"yf.Ticker({ticker}).history failed after "
        f"{len(RETRY_DELAYS)} attempts"
    ) from last_exc


def reshape_ticker_history(ticker: str, df: pd.DataFrame) -> pd.DataFrame:
    """Tidy yf.Ticker.history output for df_to_records.

    Mirrors scripts/backfill_historical.py.reshape_ticker_history.
    """
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


def upsert_stocks_row(client: Client, ticker: str) -> None:
    """Minimal stocks row: ticker + name + is_active. Other metadata
    deferred to WP-DATA-STOCKS-METADATA-ENRICHMENT.
    """
    client.table("stocks").upsert(
        [{
            "ticker": ticker,
            "name": TICKERS.get(ticker, ticker),
            "is_active": True,
        }],
        on_conflict="ticker",
    ).execute()


def process_ticker(client: Client, ticker: str) -> dict:
    """Fetch + reshape + filter + upsert one ticker. Returns stats."""
    upsert_stocks_row(client, ticker)

    raw = fetch_history_with_retry(ticker)
    if raw is None or len(raw) == 0:
        return {"ticker": ticker, "rows": 0, "dropped_nan": 0,
                "dropped_zerovol": 0, "status": "empty"}

    tidy = reshape_ticker_history(ticker, raw)

    before = len(tidy)
    tidy = tidy.dropna(subset=NOT_NULL_PRICE_COLS)
    dropped_nan = before - len(tidy)

    # WP-INFRA-INTRADAY-FILTER: drop zero/negative-volume rows.
    zero_vol_mask = tidy["volume"].isna() | (tidy["volume"] <= 0)
    dropped_zerovol = int(zero_vol_mask.sum())
    if dropped_zerovol:
        tidy = tidy.loc[~zero_vol_mask]

    records = df_to_records(tidy)
    n = len(records)
    if n:
        upsert_prices(client, records)

    return {
        "ticker": ticker,
        "rows": n,
        "dropped_nan": dropped_nan,
        "dropped_zerovol": dropped_zerovol,
        "status": "ok",
    }


def main() -> int:
    load_dotenv()
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

    # Diff ASX_200 against existing stocks table.
    existing_rows = client.table("stocks").select("ticker").execute().data
    existing = {r["ticker"] for r in (existing_rows or [])}
    new_tickers = [t for t in ASX_200 if t not in existing]

    print(f"ASX_200 size:       {len(ASX_200)}")
    print(f"already in stocks:  {len(ASX_200) - len(new_tickers)}")
    print(f"to seed:            {len(new_tickers)}")
    print()

    successes = []
    failures = []
    t_start = time.time()

    for i, ticker in enumerate(new_tickers, start=1):
        print(f"[{i}/{len(new_tickers)}] FETCHING {ticker}...", flush=True)
        try:
            stat = process_ticker(client, ticker)
            if stat["status"] == "empty":
                failures.append((ticker, "empty response from yfinance"))
                print(f"    SKIP {ticker}: empty response")
                continue
            successes.append(stat)
            extras = []
            if stat["dropped_nan"]:
                extras.append(f"dropped_nan={stat['dropped_nan']}")
            if stat["dropped_zerovol"]:
                extras.append(f"dropped_zerovol={stat['dropped_zerovol']}")
            extras_s = f"  ({', '.join(extras)})" if extras else ""
            print(f"    OK {ticker}: rows={stat['rows']}{extras_s}")
        except Exception as e:
            failures.append((ticker, f"{type(e).__name__}: {e}"))
            print(f"    FAILED {ticker}: {type(e).__name__}: {e}")

    elapsed = time.time() - t_start
    total_rows = sum(s["rows"] for s in successes)
    print()
    print("=" * 60)
    print("seed_asx200 complete.")
    print(f"  attempted:    {len(new_tickers)}")
    print(f"  succeeded:    {len(successes)}")
    print(f"  failed:       {len(failures)}")
    print(f"  prices rows:  {total_rows}")
    print(f"  wall-clock:   {elapsed:.1f}s")
    if failures:
        print(f"  failed tickers:")
        for t, reason in failures:
            print(f"    - {t}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
