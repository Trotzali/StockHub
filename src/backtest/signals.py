"""StockHub signal functions (extracted in WP-SIGNAL-MA-CROSSOVER-GRID-V1).

Each signal function takes a price DataFrame (with `adj_close`) and
returns a position series aligned to the input — values in {NaN, 0, 1}.
NaN marks warm-up / undefined; the backtest engine slices from the
first non-NaN row.
"""
from __future__ import annotations

import pandas as pd

SHORT_WINDOW = 50
LONG_WINDOW = 200


def ma_crossover_signal(df: pd.DataFrame,
                        short: int = SHORT_WINDOW,
                        long: int = LONG_WINDOW) -> pd.Series:
    """Long (1) when MA-short > MA-long, flat (0) otherwise.

    Warm-up rows (where MA-long is undefined — first long-1 rows)
    return NaN. The engine treats first non-NaN as the start of the
    evaluation window. This replaces V1's fillna(0)-then-iterate
    pattern with a cleaner "warm-up is genuinely undefined" contract,
    which makes grid sweeps over varying `long` windows correct.
    """
    ma_s = df["adj_close"].rolling(short).mean()
    ma_l = df["adj_close"].rolling(long).mean()
    pos = (ma_s > ma_l).astype(float)
    return pos.where(ma_l.notna(), float("nan"))
