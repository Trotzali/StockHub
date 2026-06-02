"""StockHub backtest engine (extracted in WP-SIGNAL-MA-CROSSOVER-GRID-V1;
long-short extension in WP-INFRA-ENGINE-SHORTSIDE).

Signal-agnostic equity simulator. The caller precomputes a position
series (+1 = long held, -1 = short held, 0 = flat, NaN = warm-up /
undefined). The engine slices from the first non-NaN position, runs
the trade simulation with brokerage + slippage costs (and optional
borrow drag on short notional), and returns gross + net metrics,
trade list, and equity curve.

Backwards compatible: long-only inputs ({NaN, 0, 1}) with the default
borrow_rate=0.0 produce BIT-IDENTICAL output to the pre-extension
engine (regression-verified at WP-INFRA-ENGINE-SHORTSIDE).

Locked decisions (preserved from WP-SIGNAL-MA-CROSSOVER-V1 +
extended in WP-INFRA-ENGINE-SHORTSIDE):
- Execution at signal-day close.
- Position alphabet: {NaN, -1, 0, +1}. Held-position semantic:
  consecutive same-side values = continuous hold; transitions =
  exit/entry. Flips (+1<->-1) are exit-then-entry, 4 fills, both
  costed.
- Costs on transitions only; sign-aware slippage (buy pays UP,
  sell receives LESS); brokerage symmetric.
- Sizing: cash-funded with brokerage carve-out, sign-flipped for
  shorts. qty = cash / (entry_price * (1 + brokerage_pct)). Same
  formula for long and short; the regression invariant.
- Borrow: pure-drag accounting. Daily charge of
  abs(shares) * close * (borrow_rate / 252) accumulated to a
  separate cumulative series, subtracted from gross to produce
  net. Does NOT touch cash or the sizing path. Entry day inclusive,
  exit day excluded (transition zeroes shares before the borrow
  check). Compounding (cash-reducing) borrow is banked as a future
  V2 option.
- Open positions at window end MTM'd to final close (not counted as
  closed trades).
- B&H baseline is gross long buy-and-hold (no costs) — matches V1
  V-walk formula and remains the comparator regardless of strategy
  direction.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

STARTING_CAPITAL = 10_000.0
BROKERAGE_PCT = 0.001        # 0.1% per side
SLIPPAGE_PER_SHARE = 0.01    # $0.01 per share per side
TRADING_DAYS_PER_YEAR = 252


def compute_buy_and_hold(df_eval: pd.DataFrame,
                         starting_capital: float) -> pd.Series:
    """Per-day B&H equity series.

    Gross (no costs). Matches the V1 V-walk formula
    starting_capital * (current_price / first_price).
    df_eval must have an adj_close column; result is index-aligned to it.
    """
    first_price = float(df_eval.iloc[0]["adj_close"])
    return starting_capital * df_eval["adj_close"] / first_price


def compute_metrics(equity: pd.Series, trades: list[dict],
                    starting_capital: float, dates: pd.Series) -> dict:
    """Headline metrics from an equity curve + trade list.

    Robust to trade_count == 0 (win-rate / avg-win / avg-loss returned
    as None). Sharpe is NaN when equity is flat (no daily volatility).
    """
    final_eq = float(equity.iloc[-1])
    total_return_dollar = final_eq - starting_capital
    total_return_pct = total_return_dollar / starting_capital

    n_days = len(equity)
    if n_days > 1 and final_eq > 0:
        ann_return = (
            (final_eq / starting_capital) ** (TRADING_DAYS_PER_YEAR / n_days) - 1
        )
    else:
        ann_return = float("nan")

    daily_ret = equity.pct_change().dropna()
    if len(daily_ret) > 1 and float(daily_ret.std()) > 0:
        sharpe = float(daily_ret.mean()) / float(daily_ret.std()) * np.sqrt(
            TRADING_DAYS_PER_YEAR
        )
    else:
        sharpe = float("nan")

    running_max = equity.cummax()
    dd_dollar = equity - running_max
    dd_pct = dd_dollar / running_max
    max_dd_dollar = float(dd_dollar.min())
    max_dd_pct = float(dd_pct.min())

    n_trades = len(trades)
    win_rate = None
    avg_win_dollar = avg_win_pct = None
    avg_loss_dollar = avg_loss_pct = None
    if n_trades > 0:
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        win_rate = len(wins) / n_trades
        if wins:
            avg_win_dollar = float(np.mean([t["pnl"] for t in wins]))
            avg_win_pct = float(np.mean([t["return_pct"] for t in wins]))
        else:
            avg_win_dollar = 0.0
            avg_win_pct = 0.0
        if losses:
            avg_loss_dollar = float(np.mean([t["pnl"] for t in losses]))
            avg_loss_pct = float(np.mean([t["return_pct"] for t in losses]))
        else:
            avg_loss_dollar = 0.0
            avg_loss_pct = 0.0

    return {
        "final_equity": final_eq,
        "total_return_dollar": total_return_dollar,
        "total_return_pct": total_return_pct,
        "ann_return": ann_return,
        "sharpe": sharpe,
        "max_dd_dollar": max_dd_dollar,
        "max_dd_pct": max_dd_pct,
        "n_trades": n_trades,
        "win_rate": win_rate,
        "avg_win_dollar": avg_win_dollar,
        "avg_win_pct": avg_win_pct,
        "avg_loss_dollar": avg_loss_dollar,
        "avg_loss_pct": avg_loss_pct,
    }


def run_backtest(ticker: str, df: pd.DataFrame, signal_series: pd.Series,
                 *,
                 starting_capital: float = STARTING_CAPITAL,
                 brokerage_pct: float = BROKERAGE_PCT,
                 slippage_per_share: float = SLIPPAGE_PER_SHARE,
                 borrow_rate: float = 0.0) -> dict:
    """Simulate a precomputed position series; return metrics + curve + trades.

    Caller responsibilities:
    - df has columns trade_date, adj_close, sorted ascending.
    - signal_series is length-aligned to df with values in
      {NaN, -1, 0, 1}; NaN marks warm-up / undefined and is sliced off
      before the sim. Long-only inputs ({NaN, 0, 1}) are a degenerate
      case; with borrow_rate=0.0 they produce BIT-IDENTICAL output to
      the pre-extension long-only engine.
    - borrow_rate is the per-ticker annualized borrow cost (e.g. 0.04
      for 4% APR). Daily charge on absolute short notional; pure-drag
      accounting (does not touch cash or sizing). Defaults to 0.0 so
      callers that never short are unaffected.

    Returns dict with keys:
        ticker
        metrics              -- gross (pre-borrow) metrics
        metrics_net          -- net (post-borrow) metrics; equals
                                metrics exactly when borrow_drag == 0
                                across the whole window (long-only or
                                borrow_rate=0.0).
        bh_metrics           -- long buy-and-hold comparator (unchanged)
        trades               -- list of round-trip records (now include
                                signed `shares` and `side`)
        equity_curve         -- DataFrame with columns:
                                  trade_date,
                                  signal_equity,           (gross)
                                  signal_equity_net,       (gross - cum drag)
                                  borrow_drag_cumulative,
                                  buy_hold_equity
        borrow_rate          -- echo of input
        borrow_drag_total    -- total cumulative drag at window end
    """
    if len(df) != len(signal_series):
        raise ValueError(
            f"df and signal_series length mismatch: "
            f"{len(df)} vs {len(signal_series)}"
        )

    first_valid = signal_series.first_valid_index()
    if first_valid is None:
        # No valid signal: equity stays at starting_capital across the
        # full window; B&H still computed for the same window.
        bh_full = compute_buy_and_hold(df, starting_capital)
        eq_df = pd.DataFrame({
            "trade_date": df["trade_date"].values,
            "signal_equity": [starting_capital] * len(df),
            "signal_equity_net": [starting_capital] * len(df),
            "borrow_drag_cumulative": [0.0] * len(df),
            "buy_hold_equity": bh_full.values,
        })
        gross_m = compute_metrics(
            eq_df["signal_equity"], [], starting_capital, eq_df["trade_date"]
        )
        return {
            "ticker": ticker,
            "metrics": gross_m,
            "metrics_net": gross_m,
            "bh_metrics": compute_metrics(
                eq_df["buy_hold_equity"], [], starting_capital, eq_df["trade_date"]
            ),
            "trades": [],
            "equity_curve": eq_df,
            "borrow_rate": borrow_rate,
            "borrow_drag_total": 0.0,
        }

    df_eval = df.iloc[first_valid:].reset_index(drop=True)
    signal_eval = signal_series.iloc[first_valid:].reset_index(drop=True)

    cash = starting_capital
    shares = 0.0  # signed: >0 long, <0 short, 0 flat
    equity_curve_rows: list[dict] = []
    trades: list[dict] = []
    open_trade: dict | None = None
    prev_pos = 0
    cumulative_borrow_drag = 0.0

    def _entry(side: int, price: float, date) -> dict:
        """side in {+1, -1}. Mutates cash + shares; returns open_trade dict.

        Sizing formula (regression invariant):
            qty = cash / (entry_price * (1 + brokerage_pct))
        Same formula for both directions; sign applied to shares only.
        Long pays cash; short receives proceeds. Brokerage symmetric.
        """
        nonlocal cash, shares
        if side == 1:
            entry_price = price + slippage_per_share  # long: buy up
        else:
            entry_price = price - slippage_per_share  # short: sell down
        qty = cash / (entry_price * (1 + brokerage_pct))
        notional = qty * entry_price
        brokerage = notional * brokerage_pct
        if side == 1:
            cash = cash - notional - brokerage
            shares = +qty
        else:
            cash = cash + notional - brokerage
            shares = -qty
        return {
            "entry_date": date,
            "entry_price": entry_price,
            "entry_shares": side * qty,  # signed
            "entry_brokerage": brokerage,
            "side": side,
        }

    def _exit(side: int, price: float, date, entry: dict) -> dict:
        """side is the side being CLOSED (+1 closing long, -1 closing short).

        PnL formula is sign-aware:
            long:  (exit_price - entry_price) * qty - costs
            short: (entry_price - exit_price) * qty - costs
        """
        nonlocal cash, shares
        if side == 1:
            exit_price = price - slippage_per_share  # long exit: sell down
        else:
            exit_price = price + slippage_per_share  # short cover: buy up
        qty = abs(entry["entry_shares"])
        notional = qty * exit_price
        brokerage = notional * brokerage_pct
        if side == 1:
            cash = cash + notional - brokerage
            trade_pnl = (
                (exit_price - entry["entry_price"]) * qty
                - entry["entry_brokerage"] - brokerage
            )
        else:
            cash = cash - notional - brokerage
            trade_pnl = (
                (entry["entry_price"] - exit_price) * qty
                - entry["entry_brokerage"] - brokerage
            )
        trade_return_pct = trade_pnl / (entry["entry_price"] * qty)
        shares = 0.0
        return {
            "entry_date": entry["entry_date"],
            "entry_price": entry["entry_price"],
            "exit_date": date,
            "exit_price": exit_price,
            "shares": entry["entry_shares"],  # signed (matches entry)
            "pnl": trade_pnl,
            "return_pct": trade_return_pct,
            "side": side,
        }

    for i in range(len(df_eval)):
        cur_pos = int(signal_eval.iloc[i])
        price = float(df_eval.iloc[i]["adj_close"])
        date = df_eval.iloc[i]["trade_date"]

        if cur_pos == prev_pos:
            pass  # hold (flat, long, or short)
        elif prev_pos == 0 and cur_pos == 1:
            open_trade = _entry(+1, price, date)
        elif prev_pos == 0 and cur_pos == -1:
            open_trade = _entry(-1, price, date)
        elif prev_pos == 1 and cur_pos == 0:
            assert open_trade is not None
            trades.append(_exit(+1, price, date, open_trade))
            open_trade = None
        elif prev_pos == -1 and cur_pos == 0:
            assert open_trade is not None
            trades.append(_exit(-1, price, date, open_trade))
            open_trade = None
        elif prev_pos == 1 and cur_pos == -1:
            # Flip long -> short (exit-then-entry, both costed)
            assert open_trade is not None
            trades.append(_exit(+1, price, date, open_trade))
            open_trade = _entry(-1, price, date)
        elif prev_pos == -1 and cur_pos == 1:
            # Flip short -> long (exit-then-entry, both costed)
            assert open_trade is not None
            trades.append(_exit(-1, price, date, open_trade))
            open_trade = _entry(+1, price, date)

        # Daily borrow accrual on absolute short notional, charged at
        # close on every day shares < 0. Entry day INCLUSIVE; exit day
        # EXCLUDED because the transition handler set shares = 0 above
        # before this check.
        if shares < 0:
            cumulative_borrow_drag += (
                abs(shares) * price * (borrow_rate / TRADING_DAYS_PER_YEAR)
            )

        # MTM equity each day: cash + open-position value at close.
        # Signed `shares` makes this the same formula for long, short,
        # and flat states.
        gross_equity = cash + shares * price
        net_equity = gross_equity - cumulative_borrow_drag
        equity_curve_rows.append({
            "trade_date": date,
            "signal_equity": gross_equity,
            "signal_equity_net": net_equity,
            "borrow_drag_cumulative": cumulative_borrow_drag,
        })
        prev_pos = cur_pos

    sig_eq = pd.DataFrame(equity_curve_rows)
    bh_eq_series = compute_buy_and_hold(df_eval, starting_capital)
    bh_eq = pd.DataFrame({
        "trade_date": df_eval["trade_date"].values,
        "buy_hold_equity": bh_eq_series.values,
    })
    eq_df = sig_eq.merge(bh_eq, on="trade_date")

    sig_metrics = compute_metrics(
        eq_df["signal_equity"], trades, starting_capital, eq_df["trade_date"]
    )
    net_metrics = compute_metrics(
        eq_df["signal_equity_net"], trades, starting_capital, eq_df["trade_date"]
    )
    bh_metrics = compute_metrics(
        eq_df["buy_hold_equity"], [], starting_capital, eq_df["trade_date"]
    )

    return {
        "ticker": ticker,
        "metrics": sig_metrics,
        "metrics_net": net_metrics,
        "bh_metrics": bh_metrics,
        "trades": trades,
        "equity_curve": eq_df,
        "borrow_rate": borrow_rate,
        "borrow_drag_total": cumulative_borrow_drag,
    }
