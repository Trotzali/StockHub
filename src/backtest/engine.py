"""StockHub backtest engine (extracted in WP-SIGNAL-MA-CROSSOVER-GRID-V1).

Signal-agnostic equity simulator. The caller precomputes a position
series (1 = long, 0 = flat, NaN = warm-up / undefined). The engine
slices from the first non-NaN position, runs the trade simulation
with brokerage + slippage costs, and returns metrics + trade list +
equity curve.

Locked decisions (preserved from WP-SIGNAL-MA-CROSSOVER-V1):
- Execution at signal-day close.
- Long-only V1 / GRID-V1 (position in {NaN, 0, 1}); short banked.
- Costs on transitions only.
- Open positions at window end MTM'd to final close (not counted as
  closed trades).
- B&H baseline is gross (no costs) — matches V-walk formula.
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
                 slippage_per_share: float = SLIPPAGE_PER_SHARE) -> dict:
    """Simulate a precomputed position series; return metrics + curve + trades.

    Caller responsibilities:
    - df has columns trade_date, adj_close, sorted ascending.
    - signal_series is length-aligned to df with values in {NaN, 0, 1};
      NaN marks warm-up / undefined and is sliced off before the sim.

    Returns dict with keys: ticker, metrics, bh_metrics, trades, equity_curve.
    equity_curve has columns trade_date, signal_equity, buy_hold_equity.
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
            "buy_hold_equity": bh_full.values,
        })
        return {
            "ticker": ticker,
            "metrics": compute_metrics(
                eq_df["signal_equity"], [], starting_capital, eq_df["trade_date"]
            ),
            "bh_metrics": compute_metrics(
                eq_df["buy_hold_equity"], [], starting_capital, eq_df["trade_date"]
            ),
            "trades": [],
            "equity_curve": eq_df,
        }

    df_eval = df.iloc[first_valid:].reset_index(drop=True)
    signal_eval = signal_series.iloc[first_valid:].reset_index(drop=True)

    cash = starting_capital
    shares = 0.0
    equity_curve_rows: list[dict] = []
    trades: list[dict] = []
    open_trade: dict | None = None
    prev_pos = 0

    for i in range(len(df_eval)):
        cur_pos = int(signal_eval.iloc[i])
        price = float(df_eval.iloc[i]["adj_close"])
        date = df_eval.iloc[i]["trade_date"]

        if prev_pos == 0 and cur_pos == 1:
            # ENTRY
            entry_price = price + slippage_per_share
            shares = cash / (entry_price * (1 + brokerage_pct))
            notional = shares * entry_price
            brokerage = notional * brokerage_pct
            cash = cash - notional - brokerage
            open_trade = {
                "entry_date": date,
                "entry_price": entry_price,
                "entry_shares": shares,
                "entry_brokerage": brokerage,
            }
        elif prev_pos == 1 and cur_pos == 0:
            # EXIT
            exit_price = price - slippage_per_share
            notional = shares * exit_price
            brokerage = notional * brokerage_pct
            cash = cash + notional - brokerage
            assert open_trade is not None
            entry = open_trade
            trade_pnl = (
                (exit_price - entry["entry_price"]) * entry["entry_shares"]
                - entry["entry_brokerage"] - brokerage
            )
            trade_return_pct = trade_pnl / (
                entry["entry_price"] * entry["entry_shares"]
            )
            trades.append({
                "entry_date": entry["entry_date"],
                "entry_price": entry["entry_price"],
                "exit_date": date,
                "exit_price": exit_price,
                "shares": entry["entry_shares"],
                "pnl": trade_pnl,
                "return_pct": trade_return_pct,
            })
            shares = 0.0
            open_trade = None

        # MTM equity each day: cash + open-position value at close.
        equity = cash + shares * price
        equity_curve_rows.append({"trade_date": date, "signal_equity": equity})
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
    bh_metrics = compute_metrics(
        eq_df["buy_hold_equity"], [], starting_capital, eq_df["trade_date"]
    )

    return {
        "ticker": ticker,
        "metrics": sig_metrics,
        "bh_metrics": bh_metrics,
        "trades": trades,
        "equity_curve": eq_df,
    }
