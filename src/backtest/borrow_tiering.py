"""Borrow-rate tiering helper.

Per-ticker annualized borrow rate derived from a structural liquidity
proxy: median daily dollar volume (raw close * volume) over the full
available history. Tickers are tercile-classified across the input
universe; each tier maps to one of three rates.

Default tier rates (annualized):
    tier 0 -- top tercile (most liquid)    -> 1% APR
    tier 1 -- middle tercile               -> 4% APR
    tier 2 -- bottom tercile (least liquid)-> 8% APR

Median (not mean) for robustness to the known volume=0 outliers
(WP-INFRA-PRICES-ZEROVOL-CLEANUP banking; 7 rows on 4 blue chips
under the live data; intraday filter prevents new ones).

Full-sample (not train-window) is the rule: liquidity is a structural
cost assumption, not a return predictor, and is highly persistent.
Train-only would needlessly shorten the median sample without removing
any leakage.

The helper self-fetches (close, volume) from Supabase rather than
relying on fetch_prices_full (which selects only adj_close). The fetch
MUST paginate: PostgREST's row cap is 1000, and most tickers exceed
1000 rows over 5y of daily history. An unpaginated select silently
truncates to the OLDEST 1000 rows by .order(...), biasing every
ticker's median ADV toward early-window liquidity. Pagination per
WP-INFRA-ENGINE-SHORTSIDE Phase A4 verification.

ASCII-only stdout per CLAUDE.md item 8.

Spec source: WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1.
"""
from __future__ import annotations

import pandas as pd

TIER_RATES_DEFAULT: tuple[float, float, float] = (0.01, 0.04, 0.08)
PAGE_SIZE = 1000


def fetch_close_volume_full(client, ticker: str,
                             page_size: int = PAGE_SIZE) -> pd.DataFrame:
    """Paginated read of (trade_date, close, volume) for one ticker.

    Mirrors src.data.yfinance_utils.fetch_prices_full's pagination
    pattern. Returns a DataFrame sorted ascending by trade_date.
    """
    rows: list[dict] = []
    offset = 0
    while True:
        r = (
            client.table("prices")
            .select("trade_date,close,volume")
            .eq("ticker", ticker)
            .order("trade_date")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows.extend(r.data)
        if len(r.data) < page_size:
            break
        offset += page_size
    df = pd.DataFrame(rows)
    if not df.empty:
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df["close"] = pd.to_numeric(df["close"])
        df["volume"] = pd.to_numeric(df["volume"])
        df = df.sort_values("trade_date").reset_index(drop=True)
    return df


def compute_borrow_rates(
    client,
    tickers: list[str],
    rates: tuple[float, float, float] = TIER_RATES_DEFAULT,
) -> tuple[dict[str, float], dict[str, dict]]:
    """For each ticker, fetch (close, volume) over full available
    history (paginated), compute median daily dollar volume
    (close * volume), tercile-classify across the universe, map to
    annualized borrow rates.

    Args:
        client: Supabase client.
        tickers: universe of tickers (the same set passed to
            run_backtest downstream).
        rates: (top, mid, bottom) tier rate triplet. Defaults to
            (1%, 4%, 8%) annualized.

    Returns:
        rates_per_ticker:  {ticker: annualized_rate}
        diagnostics:       {ticker: {"median_adv": float,
                                     "tier":       int (0/1/2),
                                     "rate":       float,
                                     "row_count":  int}}
    """
    medians: dict[str, float] = {}
    row_counts: dict[str, int] = {}
    for t in tickers:
        df = fetch_close_volume_full(client, t)
        row_counts[t] = len(df)
        if df.empty:
            medians[t] = 0.0
            continue
        dollar_volume = (df["close"] * df["volume"]).astype(float)
        medians[t] = float(dollar_volume.median())

    s = pd.Series(medians)
    # qcut with 3 quantiles. labels=[0,1,2] => 0 = lowest ADV bucket,
    # 2 = highest. We want the inverse: 0 = highest ADV (most liquid).
    # So label inversion is applied below.
    tiers_raw = pd.qcut(s, q=3, labels=[0, 1, 2])
    tiers = tiers_raw.map({0: 2, 1: 1, 2: 0}).astype(int)  # invert

    rates_per_ticker: dict[str, float] = {}
    diagnostics: dict[str, dict] = {}
    for t in tickers:
        tier = int(tiers.loc[t])
        rate = float(rates[tier])
        rates_per_ticker[t] = rate
        diagnostics[t] = {
            "median_adv": medians[t],
            "tier": tier,
            "rate": rate,
            "row_count": row_counts[t],
        }
    return rates_per_ticker, diagnostics
