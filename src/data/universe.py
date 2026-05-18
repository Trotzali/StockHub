"""StockHub universe (consolidated in WP-INFRA-UNIVERSE-CENTRALIZE).

Single source of truth for the tradeable / benchmark universe. Pulled
out of scripts/fetch_yfinance.py and scripts/backfill_historical.py
where the same TICKERS dict was duplicated (sessions 2-5).

Shape preserved: TICKERS is a flat dict[str, str] mapping the
yfinance ticker symbol to a human-readable name. Consumers iterate
.items() / .keys() / len() -- no access-pattern change vs the
inline dicts they replace.

Two list views provided for callers that need separated slices of
the universe:
- BLUE_CHIPS_ASX: the 10 ASX blue chips (tradeable equities),
  alphabetical for stable diffs as the universe expands.
- BENCHMARKS: index reference series (^AXJO; used as regime filter
  input, not traded).

WP-DATA-UNIVERSE-ASX200 (T2, concurrent at the time of this WP)
will extend by adding an ASX_200 list + ~190 more TICKERS entries.
Additions land purely additively in this file.
"""
from __future__ import annotations


BLUE_CHIPS_ASX: list[str] = [
    "ANZ.AX",
    "BHP.AX",
    "CBA.AX",
    "CSL.AX",
    "NAB.AX",
    "RIO.AX",
    "TLS.AX",
    "WBC.AX",
    "WES.AX",
    "WOW.AX",
]

BENCHMARKS: list[str] = [
    "^AXJO",
]

# Flat ticker -> name mapping. Order preserved from the original
# inline dicts (CBA first per fetch_yfinance.py ordering) so any
# implicit-order-dependent consumer behaviour is unchanged.
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
    "^AXJO":  "S&P/ASX 200 Index",
}
