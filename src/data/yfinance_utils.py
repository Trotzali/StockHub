"""StockHub shared data-layer helpers (extracted in WP-INFRA-SRC-LAYOUT).

Helpers reusable across yfinance consumers:
- scripts/fetch_yfinance.py (daily 7-day window)
- scripts/backfill_historical.py (5-year per-ticker — WP-DATA-HISTORICAL-BACKFILL)
- future signal / schema scripts

Per CLAUDE.md ENVIRONMENT NOTES:
- pandas 3.x .stack() requires future_stack=True (handled in caller-side flatten)
- yfinance Ticker.history is tz-aware Australia/Sydney; yf.download is tz-naive.
  trade_date() handles both shapes.
"""
from datetime import date
from typing import Iterator

import pandas as pd
from supabase import Client


UPSERT_BATCH_SIZE = 500


def trade_date(ts: pd.Timestamp) -> date:
    """Convert a yfinance timestamp to an ASX trade date.

    yf.Ticker.history returns tz-aware Australia/Sydney;
    yf.download returns tz-naive (already exchange-local).
    Never call .tz_convert('UTC').date() — for AEDT/AEST
    evening UTC bars that lands you on the previous day.
    """
    if ts.tzinfo is not None:
        ts = ts.tz_convert("Australia/Sydney")
    return ts.date()


def chunked(seq: list, size: int) -> Iterator[list]:
    """Yield consecutive chunks of `size` from `seq`."""
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to upsert-ready records (NaN -> None, ISO dates).

    Treats any column named 'trade_date' as a timestamp to coerce via
    trade_date(). All other NaN cells become None.
    """
    records = []
    for raw in df.to_dict(orient="records"):
        r = {}
        for k, v in raw.items():
            if pd.isna(v):
                r[k] = None
            elif k == "trade_date":
                r[k] = trade_date(pd.Timestamp(v)).isoformat()
            else:
                r[k] = v
        records.append(r)
    return records


def upsert_prices(client: Client, records: list[dict]) -> int:
    """Idempotent upsert into the prices table.

    Chunked by UPSERT_BATCH_SIZE; conflict resolution on
    (ticker, trade_date) composite PK.
    """
    total = 0
    for chunk in chunked(records, UPSERT_BATCH_SIZE):
        client.table("prices").upsert(
            chunk, on_conflict="ticker,trade_date"
        ).execute()
        total += len(chunk)
    return total
