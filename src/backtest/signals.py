"""StockHub signal functions (extracted in WP-SIGNAL-MA-CROSSOVER-GRID-V1).

Each signal function takes a price DataFrame (with `adj_close`) and
returns a position series aligned to the input -- values in {NaN, 0, 1}
for long-only, {NaN, -1, 0, +1} for long-short. NaN marks warm-up /
undefined; the backtest engine slices from the first non-NaN row.

Cross-sectional functions (WP-SIGNAL-MOMENTUM-CROSS-SECTIONAL-V1) take
a panel (dict[str, DataFrame]) and return per-ticker series + rebalance
metadata. They use the same {NaN, -1, 0, +1} alphabet per series.
"""
from __future__ import annotations

import numpy as np
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


def momentum_cross_sectional_longshort_signal(
    panel: dict[str, pd.DataFrame],
    J: int,
    skip: int = 21,
    rebalance: str = "ME",
    k: int = 18,
    close_col: str = "adj_close",
) -> tuple[
    dict[str, pd.Series],
    list[pd.Timestamp],
    dict[pd.Timestamp, tuple[frozenset[str], frozenset[str]]],
]:
    """Cross-sectional momentum long-short signal (WP-SIGNAL-MOMENTUM-
    CROSS-SECTIONAL-V1; Option B architecture).

    Panel-in (dict[ticker -> DataFrame with trade_date, adj_close]),
    per-ticker series-out, {NaN, -1, 0, +1}. Position changes ONLY at
    rebalance bars; held constant between rebalances regardless of
    intra-month rank shifts.

    Rebalance bars: monthly month-ends mapped to the LAST actual
    trading day <= each month-end in the UNION calendar across all
    tickers in the panel. Duplicates collapsed.

    Per-ticker formation return at rebalance rb (uses the ticker's own
    calendar):
        ix     = ticker_dates.get_loc(rb)
        p_skip = closes[ix - skip]
        p_then = closes[ix - skip - J]
        lookback_return = (p_skip / p_then) - 1.0
    Ticker is INELIGIBLE at rb if any of: rb not in its calendar,
    ix < skip + J, p_then non-finite or <= 0.

    Breadth: fixed top-k / bottom-k per rebalance (k=18 locked for V1).
    Top-k by descending formation return -> +1. Bottom-k -> -1. Middle
    and ineligible tickers -> 0. Deterministic tiebreak by ticker name
    (ascending). If fewer than 2*k tickers are eligible at a rebalance,
    that rebalance has EMPTY legs (no positions emitted that period).

    Per-ticker signal series (length == len(panel[t])):
        - NaN before the first rebalance that exists in t's calendar
          (engine slices from first valid index).
        - Each subsequent bar's position = leg-membership at the last
          rebalance bar <= that bar's date.
        - Ticker present in top set -> +1; in bottom set -> -1; else 0.
    No carry-forward beyond a ticker's last available bar (the series
    simply ends with df, per engine contract).

    Args:
        panel: dict[ticker -> DataFrame], each df sorted ascending by
            trade_date with columns (trade_date, close_col). Caller
            owns coercion + sort.
        J: formation lookback in trading days (e.g. 63 / 126 / 252).
        skip: skip-month gap in trading days (default 21 = 1 month,
            Jegadeesh-Titman convention).
        rebalance: pandas offset alias for the rebalance schedule.
            "ME" = month-end (locked for V1; pandas 3.x renamed "M"
            to "ME").
        k: per-leg breadth (default 18 = decile of ~180 survivors).
        close_col: which column to use for closes (default "adj_close").

    Returns:
        (signals, rebalance_dates, leg_by_rb)
        signals: dict[ticker -> pd.Series] (float dtype, len = len(df_t)).
        rebalance_dates: list[Timestamp] sorted ascending.
        leg_by_rb: dict[rb_date -> (frozenset top tickers, frozenset
            bottom tickers)].
    """
    all_dates = sorted({pd.Timestamp(d) for df in panel.values()
                        for d in df["trade_date"]})
    if not all_dates:
        return ({t: pd.Series([], dtype=float) for t in panel}, [], {})
    union_idx = pd.DatetimeIndex(all_dates)

    month_ends = pd.date_range(union_idx.min(), union_idx.max(), freq=rebalance)
    rebalance_dates: list[pd.Timestamp] = []
    seen: set[pd.Timestamp] = set()
    for m in month_ends:
        candidates = union_idx[union_idx <= m]
        if len(candidates) == 0:
            continue
        rb = pd.Timestamp(candidates[-1])
        if rb in seen:
            continue
        seen.add(rb)
        rebalance_dates.append(rb)

    ticker_dates: dict[str, pd.DatetimeIndex] = {}
    ticker_closes: dict[str, np.ndarray] = {}
    for t, df in panel.items():
        ticker_dates[t] = pd.DatetimeIndex(df["trade_date"])
        ticker_closes[t] = df[close_col].values.astype(float)

    leg_by_rb: dict[pd.Timestamp, tuple[frozenset[str], frozenset[str]]] = {}
    for rb in rebalance_dates:
        formations: dict[str, float] = {}
        for t in panel:
            dates_t = ticker_dates[t]
            if rb not in dates_t:
                continue
            ix = int(dates_t.get_loc(rb))
            if ix < skip + J:
                continue
            p_skip = ticker_closes[t][ix - skip]
            p_then = ticker_closes[t][ix - skip - J]
            if not np.isfinite(p_skip) or not np.isfinite(p_then) or p_then <= 0:
                continue
            formations[t] = (p_skip / p_then) - 1.0
        if len(formations) < 2 * k:
            leg_by_rb[rb] = (frozenset(), frozenset())
            continue
        items = sorted(formations.items(), key=lambda kv: (-kv[1], kv[0]))
        top = frozenset(t for t, _ in items[:k])
        bot = frozenset(t for t, _ in items[-k:])
        leg_by_rb[rb] = (top, bot)

    rebal_arr = np.array(rebalance_dates, dtype="datetime64[ns]")
    signals: dict[str, pd.Series] = {}
    for t in panel:
        dates_t = ticker_dates[t]
        sig = np.full(len(dates_t), np.nan, dtype=float)
        cur_rb_ix = -1
        dates_arr = dates_t.values
        for i in range(len(dates_t)):
            d = dates_arr[i]
            while (cur_rb_ix + 1 < len(rebal_arr)
                   and rebal_arr[cur_rb_ix + 1] <= d):
                cur_rb_ix += 1
            if cur_rb_ix < 0:
                continue
            rb = pd.Timestamp(rebal_arr[cur_rb_ix])
            top, bot = leg_by_rb[rb]
            if t in top:
                sig[i] = 1.0
            elif t in bot:
                sig[i] = -1.0
            else:
                sig[i] = 0.0
        signals[t] = pd.Series(sig, dtype=float)

    return signals, list(rebalance_dates), leg_by_rb
