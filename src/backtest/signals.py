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


def momentum_absolute_lookback_signal(df: pd.DataFrame,
                                      N: int,
                                      skip: int = 21,
                                      close_col: str = "adj_close") -> pd.Series:
    """Absolute lookback momentum signal (Jegadeesh-Titman skip-1-month).

    Per-ticker binary signal. At each trade_date t:
        p_then = close[t - skip - N]
        p_skip = close[t - skip]
        lookback_return = (p_skip / p_then) - 1
        signal[t] = 1  if lookback_return >  0  (strict)
        signal[t] = 0  if lookback_return <= 0
        signal[t] = NaN for the first (skip + N) trade days (warm-up)
                    or if either p_then or p_skip is NaN.

    The (strict >) is locked; zero or negative lookback yields 0, not 1.

    The skip-21 (one month) is the classic Jegadeesh-Titman convention
    designed to avoid the well-documented short-term mean-reversion
    overlap into momentum measurement. Default-bound so the signal is
    a single-grid-axis function of N.

    Stateless: each day's signal is a pure function of two prices
    (skip and skip+N trade days ago). Consecutive 1s mean the
    momentum condition continues to hold; the engine's held-position
    protocol treats them as a single continuous position.

    Returns:
        Series of length len(df), float dtype. First (skip + N) rows
        are NaN. Subsequent rows are 0.0 / 1.0 per the engine's
        signal_series protocol.

    Spec source: WP-SIGNAL-MOMENTUM-V1.
    """
    closes = df[close_col]
    p_then = closes.shift(skip + N)
    p_skip = closes.shift(skip)
    lookback_return = (p_skip / p_then) - 1.0
    signal = (lookback_return > 0).astype(float)
    return signal.where(lookback_return.notna(), float("nan"))


def mean_reversion_zscore_longshort_signal(df: pd.DataFrame,
                                           window: int,
                                           threshold: float,
                                           close_col: str = "adj_close") -> pd.Series:
    """Symmetric long-short mean-reversion z-score signal.

    Mirror of mean_reversion_zscore_signal (the long-only version) with
    the constraint flipped from long-only ({NaN, 0, +1}) to symmetric
    long-short ({NaN, -1, 0, +1}). Same z-score formula, same window
    and threshold parameters, same warm-up convention, same
    population stdev (ddof=0). Spec source:
    WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1.

    Z-score:
        z = (close - SMA(window)) / stdev(window, ddof=0)

    Transition logic (priority order, evaluated per bar from
    window-1 onward):
        1. z < -threshold              -> signal = +1 (LONG ENTRY,
                                          overrides any prior state;
                                          re-affirms if already long)
        2. z > +threshold              -> signal = -1 (SHORT ENTRY,
                                          overrides any prior state;
                                          re-affirms if already short;
                                          FLIPs from +1 trigger the
                                          engine's exit-then-entry path)
        3. prev_pos == +1 and z >= 0   -> signal = 0  (LONG mean-touch
                                          exit; identical to long-only
                                          spec)
        4. prev_pos == -1 and z <= 0   -> signal = 0  (SHORT mean-touch
                                          exit; mirror of long exit)
        5. otherwise                   -> signal = prev_pos (HOLD)

    Mean-touch at z = 0 from both sides: from below for long-side
    (z >= 0); from above for short-side (z <= 0). At z = 0 exactly,
    only the side currently held triggers (prev_pos discriminates).

    Stateful held-position semantic: between an entry-threshold cross
    and the subsequent mean-touch, position is HELD regardless of
    intermediate z values. Re-entries at the same side are no-ops
    (signal stays the same).

    Flips (direct +1 -> -1 or -1 -> +1) happen only if z jumps across
    both thresholds in a single bar; the entry condition (priority 1
    or 2) overrides the held state. The engine (run_backtest at
    3cd4d0b) models flips as exit-then-entry within a single loop
    iteration, both legs costed.

    Warm-up: first window-1 rows return NaN (rolling stats undefined).
    Loop runs from t = window-1 onward, matching the long-only
    function's structure exactly.

    Returns:
        Series of length len(df), float dtype. First window-1 rows are
        NaN. Subsequent rows are -1.0 / 0.0 / +1.0 per the engine's
        signal_series protocol.
    """
    closes = df[close_col]
    sma = closes.rolling(window).mean()
    stdev = closes.rolling(window).std(ddof=0)
    z = (closes - sma) / stdev

    position = pd.Series([float("nan")] * len(df), index=df.index, dtype=float)
    prev_pos = 0
    for t in range(window - 1, len(df)):
        z_t = z.iloc[t]
        if pd.notna(z_t):
            if z_t < -threshold:
                new_pos = 1
            elif z_t > threshold:
                new_pos = -1
            elif prev_pos == 1 and z_t >= 0:
                new_pos = 0
            elif prev_pos == -1 and z_t <= 0:
                new_pos = 0
            else:
                new_pos = prev_pos
        else:
            new_pos = prev_pos
        position.iloc[t] = float(new_pos)
        prev_pos = new_pos
    return position
