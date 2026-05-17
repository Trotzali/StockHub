"""WP-DATA-YFINANCE-FETCHER: Daily ASX prices ingestion via yfinance.

Fetches the last 7 days of OHLC + Adj Close for a hardcoded universe
of 10 ASX blue chips and upserts into Supabase. Idempotent — safe to
rerun.

Per CLAUDE.md and locked decisions:
- supabase-py over HTTPS only
- daily EOD ingestion, no intraday
- service_role bypasses RLS

Usage: python scripts/fetch_yfinance.py
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
from src.data.yfinance_utils import trade_date, df_to_records, upsert_prices

# 10 ASX blue chips for MVP. Expand via WP-DATA-UNIVERSE-ASX200.
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

FETCH_PERIOD = "7d"
RETRY_DELAYS = (1, 2, 4)  # exponential backoff between attempts

NOT_NULL_PRICE_COLS = [
    "open", "high", "low", "close", "adj_close", "volume",
]


def fetch_with_retry(tickers: list[str]) -> pd.DataFrame:
    """Single yf.download call wrapped in 3-attempt exponential backoff."""
    last_exc: Optional[Exception] = None
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            return yf.download(
                tickers,
                period=FETCH_PERIOD,
                group_by="ticker",
                auto_adjust=False,
                progress=False,
            )
        except Exception as exc:
            last_exc = exc
            print(
                f"  fetch attempt {attempt} failed: {exc}; "
                f"retrying in {delay}s"
            )
            time.sleep(delay)
    raise RuntimeError(
        f"yf.download failed after {len(RETRY_DELAYS)} attempts"
    ) from last_exc


def flatten_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten the (Ticker, Field) MultiIndex DataFrame into tidy rows.

    Pandas 3.x requires future_stack=True for the new stack semantics.
    """
    flat = df.stack(level=0, future_stack=True).reset_index()
    flat = flat.rename(columns={
        "Date": "trade_date",
        "Ticker": "ticker",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    })
    return flat


def upsert_stocks(client: Client) -> int:
    """Upsert minimal stocks rows.

    Metadata (sector, industry, market_cap) deferred to
    WP-DATA-STOCKS-METADATA-ENRICHMENT.
    """
    rows = [
        {"ticker": t, "name": n, "is_active": True}
        for t, n in TICKERS.items()
    ]
    client.table("stocks").upsert(
        rows, on_conflict="ticker"
    ).execute()
    return len(rows)


def main() -> int:
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    client = create_client(url, key)

    print(f"Fetching {len(TICKERS)} tickers for last {FETCH_PERIOD}...")

    n_stocks = upsert_stocks(client)
    print(f"  stocks: upserted {n_stocks} rows")

    raw = fetch_with_retry(list(TICKERS.keys()))
    flat = flatten_prices(raw)

    before = len(flat)
    dropped_tickers = (
        flat.loc[
            flat[NOT_NULL_PRICE_COLS].isna().any(axis=1),
            "ticker"
        ].unique().tolist()
    )
    flat = flat.dropna(subset=NOT_NULL_PRICE_COLS)

    records = df_to_records(flat)
    n_prices = upsert_prices(client, records)

    print(
        f"  prices: upserted {n_prices} rows across "
        f"{flat['ticker'].nunique()} tickers"
    )
    if dropped_tickers:
        print(
            f"  dropped {before - len(flat)} rows from "
            f"{len(dropped_tickers)} tickers: {dropped_tickers}"
        )

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
