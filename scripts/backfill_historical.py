"""WP-DATA-HISTORICAL-BACKFILL: 5y EOD backfill for 10 ASX blue chips.

One-shot per-ticker historical load. yf.download batch caps at ~60d,
so per-ticker yf.Ticker(t).history(period='5y') is the only viable
path for 5y windows.

Idempotent via existing on_conflict=(ticker,trade_date) on prices.

Usage:
    python scripts/backfill_historical.py --dry-run
    python scripts/backfill_historical.py
"""
import argparse
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
from src.data.yfinance_utils import df_to_records, upsert_prices

# Same 10 ASX blue chips as scripts/fetch_yfinance.py.
# TODO: WP-DATA-UNIVERSE-ASX200 will consolidate to a shared config.
TICKERS: dict[str, str] = {
    "CBA.AX": "Commonwealth Bank of Australia",
    "BHP.AX": "BHP Group Limited",
    "RIO.AX": "Rio Tinto Limited",
    "WBC.AX": "Westpac Banking Corporation",
    "NAB.AX": "National Australia Bank",
    "ANZ.AX": "ANZ Group Holdings",
    "WES.AX": "Wesfarmers Limited",
    "WOW.AX": "Woolworths Group",
    "TLS.AX": "Telstra Group",
    "CSL.AX": "CSL Limited",
}

FETCH_PERIOD = "5y"
RETRY_DELAYS = (1, 2, 4)
WARN_MIN_ROWS = 1000  # approx 4 years of trading days

NOT_NULL_PRICE_COLS = [
    "open", "high", "low", "close", "adj_close", "volume",
]


# TODO: WP-INFRA-YFUTILS-EXTEND-RETRY-WRAPPER — generalize the
# 3-attempt exponential backoff into a shared helper consumed by
# both the daily fetcher (batch yf.download) and this per-ticker
# backfill (yf.Ticker.history). Currently duplicated.
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
                f"  {ticker} attempt {attempt} failed: {exc}; "
                f"retrying in {delay}s"
            )
            time.sleep(delay)
    raise RuntimeError(
        f"yf.Ticker({ticker}).history failed after "
        f"{len(RETRY_DELAYS)} attempts"
    ) from last_exc


def reshape_ticker_history(ticker: str, df: pd.DataFrame) -> pd.DataFrame:
    """Tidy yf.Ticker.history output for df_to_records.

    Input: index=Date (tz-aware Australia/Sydney), columns include
    Open/High/Low/Close/Adj Close/Volume plus Dividends/Stock Splits.

    Output: tidy DataFrame with schema-matching column names plus a
    `ticker` column. Date is materialised as `trade_date`; trade_date()
    will normalise it inside df_to_records.
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


def process_ticker(client: Client, ticker: str, dry_run: bool) -> dict:
    raw = fetch_history_with_retry(ticker)
    tidy = reshape_ticker_history(ticker, raw)

    before = len(tidy)
    tidy = tidy.dropna(subset=NOT_NULL_PRICE_COLS)
    dropped = before - len(tidy)

    records = df_to_records(tidy)
    n = len(records)

    if not dry_run and n:
        upsert_prices(client, records)

    date_min = tidy["trade_date"].min() if n else None
    date_max = tidy["trade_date"].max() if n else None
    warn = n < WARN_MIN_ROWS
    flag = "WARN" if warn else "OK  "
    print(
        f"  {flag} {ticker:<8} rows={n:>5}  "
        f"range={date_min}..{date_max}  dropped={dropped}"
    )
    return {"ticker": ticker, "rows": n, "warn": warn, "dropped": dropped}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch and reshape only; skip DB upsert.",
    )
    args = parser.parse_args()

    load_dotenv()
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    print(
        f"Backfilling {len(TICKERS)} tickers @ period={FETCH_PERIOD} "
        f"({mode})"
    )

    results = []
    for ticker in TICKERS:
        results.append(process_ticker(client, ticker, args.dry_run))

    total = sum(r["rows"] for r in results)
    warned = [r["ticker"] for r in results if r["warn"]]
    print()
    print(f"Total rows fetched: {total}")
    print(f"Tickers processed:  {len(results)}")
    if warned:
        print(f"WARN (< {WARN_MIN_ROWS} rows): {warned}")
    else:
        print("WARN: none")
    if args.dry_run:
        print("DRY-RUN — no DB writes performed.")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
