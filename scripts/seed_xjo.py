"""WP-SIGNAL-MA-CROSSOVER-REGIME-FILTER-V1 -- one-off ^AXJO seed.

Idempotent: UPSERT semantics on both `stocks` and `prices` make this
safe to re-run. Seeds 1 stocks row + ~1264 prices rows so the V3
regime-filter signal (XJO MA-200) has data to read.

Filters applied to the yfinance fetch:
- volume > 0: drops intraday-during-market-hours snapshots (volume
  starts at 0 and accumulates through the session) + any historical
  zero-volume anomalies.
- trade_date <= max blue-chip trade_date: keeps XJO's date set
  identical to the universe so the date-aligned signal multiplication
  in V3 doesn't introduce surprise NaNs at the trailing edge.

After this seeds: the daily fetcher + historical backfill scripts
both carry ^AXJO in their TICKERS dict, so future runs keep XJO
extended in lockstep with the blue chips.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data.yfinance_utils import df_to_records, trade_date, upsert_prices


TICKER = "^AXJO"
STOCK_NAME = "S&P/ASX 200 Index"
FETCH_PERIOD = "5y"


def main() -> int:
    load_dotenv()
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

    # Determine blue-chip ceiling via CBA.AX (universe is uniform per
    # Phase A WP-SIGNAL-MA-CROSSOVER-V1; CBA is representative).
    r = (
        client.table("prices")
        .select("trade_date")
        .eq("ticker", "CBA.AX")
        .order("trade_date", desc=True)
        .limit(1)
        .execute()
    )
    if not r.data:
        print("FAIL: no CBA.AX rows in prices; cannot determine ceiling.")
        return 1
    max_blue_chip_date = pd.to_datetime(r.data[0]["trade_date"]).date()
    print(f"Max blue-chip trade_date (CBA.AX): {max_blue_chip_date}")

    print(f"Fetching {TICKER} via yfinance (period={FETCH_PERIOD})...")
    raw = yf.Ticker(TICKER).history(period=FETCH_PERIOD, auto_adjust=False)
    print(
        f"  yfinance returned {len(raw)} rows, "
        f"range {raw.index.min().date()}..{raw.index.max().date()}"
    )

    # Reshape to schema convention (matches backfill_historical.py:87).
    df = raw.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    })
    df = df.reset_index().rename(columns={"Date": "trade_date"})
    df["ticker"] = TICKER

    rows_in = len(df)
    df = df[df["volume"] > 0]
    rows_after_vol = len(df)
    dropped_vol = rows_in - rows_after_vol
    print(f"  Dropped {dropped_vol} rows (volume == 0)")

    # Cap at blue-chip ceiling using the trade_date() helper so the
    # tz-aware Sydney timestamps from Ticker.history convert correctly.
    df["__d"] = df["trade_date"].apply(trade_date)
    df = df[df["__d"] <= max_blue_chip_date].drop(columns="__d")
    rows_after_date = len(df)
    dropped_date = rows_after_vol - rows_after_date
    print(f"  Dropped {dropped_date} rows (trade_date > {max_blue_chip_date})")
    print(f"  Rows to seed: {len(df)}")

    if df.empty:
        print("FAIL: zero rows after filtering; nothing to seed.")
        return 1

    # Upsert stocks row first (FK target for prices).
    stocks_row = [{
        "ticker": TICKER,
        "name": STOCK_NAME,
        "is_active": True,
    }]
    client.table("stocks").upsert(
        stocks_row, on_conflict="ticker"
    ).execute()
    print(f"  stocks: upserted 1 row ({TICKER}: {STOCK_NAME})")

    records = df_to_records(df)
    upsert_prices(client, records)
    first_dt = records[0]["trade_date"]
    last_dt = records[-1]["trade_date"]
    print(
        f"  prices: upserted {len(records)} rows for {TICKER}, "
        f"range {first_dt}..{last_dt}"
    )
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
