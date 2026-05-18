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


def regime_above_ma(df: pd.DataFrame,
                    window: int = 200,
                    close_col: str = "adj_close") -> pd.Series:
    """Regime filter: 1.0 when close > rolling-mean(window), 0.0 otherwise.

    Same NaN-warm-up + 0/1 contract as ma_crossover_signal. Designed for
    use as a regime filter on a primary signal via date-aligned element-
    wise multiplication at the call site (see
    scripts/backtest_ma_crossover_regime_grid.py).

    Returns:
        Series of length len(df). First window-1 rows are NaN (MA-window
        undefined). Subsequent rows are 1.0 (regime "on") or 0.0
        (regime "off"). Caller supplies the alignment / multiplication.
    """
    ma = df[close_col].rolling(window).mean()
    pos = (df[close_col] > ma).astype(float)
    return pos.where(ma.notna(), float("nan"))


def mean_reversion_zscore_signal(df: pd.DataFrame,
                                 window: int,
                                 threshold: float,
                                 close_col: str = "adj_close") -> pd.Series:
    """Mean-reversion z-score signal (stateful, mean-touch exit).

    Enter long when the close price is below the rolling mean by more
    than `threshold` rolling standard deviations (z < -threshold).
    Exit when the close reverts to or above the rolling mean (z >= 0).

    Stateful: between an entry and the subsequent mean-touch exit, the
    position is HELD at 1 regardless of intermediate z values. This is
    the classic bounded-band trader semantic — once you're long, you
    wait for the mean target, not for another entry signal. Differs
    from the stateless ma_crossover_signal where each day's position
    is a pure function of today's MAs.

    Standard deviation uses ddof=0 (POPULATION stdev). This keeps the
    z-score scale identical across grid sweeps over varying `window`
    sizes; ddof=1 (sample stdev) would slightly inflate stdev on
    smaller windows and shift threshold crossings. The choice is
    locked at population to give the grid a consistent scale.

    Warm-up rows (where the rolling mean / stdev are undefined — first
    window-1 rows) return NaN. The engine treats first non-NaN as the
    start of the evaluation window.

    Returns:
        Series of length len(df), float dtype. First window-1 rows are
        NaN. Subsequent rows are 0.0 / 1.0 representing held-position
        state per the engine's signal_series protocol.
    """
    closes = df[close_col]
    sma = closes.rolling(window).mean()
    stdev = closes.rolling(window).std(ddof=0)
    z = (closes - sma) / stdev

    position = pd.Series([float("nan")] * len(df), index=df.index, dtype=float)
    prev_pos = 0
    for t in range(window - 1, len(df)):
        z_t = z.iloc[t]
        if pd.notna(z_t) and z_t < -threshold:
            position.iloc[t] = 1.0
            prev_pos = 1
        elif pd.notna(z_t) and z_t >= 0 and prev_pos == 1:
            position.iloc[t] = 0.0
            prev_pos = 0
        else:
            position.iloc[t] = float(prev_pos)
    return position
