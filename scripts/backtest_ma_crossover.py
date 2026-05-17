"""scripts/backtest_ma_crossover.py -- WP-SIGNAL-MA-CROSSOVER-V1.

50-day / 200-day SMA crossover backtest on the ASX blue-chip universe.

Locked decisions (orchestrator chat, not re-litigated here):
- Signal: golden cross (MA-50 > MA-200) = long; death cross = flat.
- Universe: all rows in `stocks` (currently 10 .AX tickers).
- Hold rule: until opposite signal. No stops / targets / time limits.
- Execution: trade at signal-day close (same-day fill).
- Costs: 0.1% brokerage per side + $0.01 slippage per share per side
  on the signal strategy. B&H baseline is gross (no costs) to match
  the V-walk verification formula.
- Per-ticker $10,000 starting capital; 10 independent backtests.
- Warm-up: first LONG_WINDOW-1 rows have no MA-long -> position
  flat -> excluded from equity curve and metrics.
- Open positions at window end MTM'd to final adj_close; NOT counted
  as closed trades.
- Output: per-ticker + aggregate metrics to stdout (ASCII only);
  results/equity_curve_<TICKER_AX>.csv per ticker.
- Engine inline as run_backtest(). Extraction to src/backtest/
  deferred to the second consumer (V2 grid-sweep or UI shell),
  mirroring the src-layout split rule from 4be60e1.

Pagination note: the supabase free-tier PostgREST caps responses at
1000 rows regardless of .range/.limit (verified Phase A). Per-ticker
history is ~1265 rows so pagination is mandatory. Helper inlined
here; extraction WP banked (WP-INFRA-YFUTILS-FETCH-PRICES-PAGINATED).
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

# ----- Constants -----

STARTING_CAPITAL = 10_000.0
BROKERAGE_PCT = 0.001        # 0.1% per side
SLIPPAGE_PER_SHARE = 0.01    # $0.01 per share per side
SHORT_WINDOW = 50
LONG_WINDOW = 200
TRADING_DAYS_PER_YEAR = 252
PAGE_SIZE = 1000

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"


# ----- Data loading (local helper; do not extract this WP) -----

def fetch_full_series(client: Client, ticker: str) -> pd.DataFrame:
    """Paginated fetch of (trade_date, adj_close) for one ticker.

    PostgREST free-tier caps at 1000 rows per request regardless of
    .range / .limit. Phase A confirmed pagination is mandatory.
    """
    rows: list[dict] = []
    offset = 0
    while True:
        r = (
            client.table("prices")
            .select("trade_date,adj_close")
            .eq("ticker", ticker)
            .order("trade_date")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        rows.extend(r.data)
        if len(r.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    df = pd.DataFrame(rows)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["adj_close"] = pd.to_numeric(df["adj_close"])
    return df


# ----- Signal -----

def ma_crossover_signal(df: pd.DataFrame, short: int = SHORT_WINDOW,
                        long: int = LONG_WINDOW) -> pd.Series:
    """Long (1) when MA-short > MA-long, flat (0) otherwise.

    Warm-up rows (MA-long NaN) coerced to 0.
    """
    ma_s = df["adj_close"].rolling(short).mean()
    ma_l = df["adj_close"].rolling(long).mean()
    pos = (ma_s > ma_l).astype(int)
    return pos.where(ma_l.notna(), 0)


# ----- Backtest engine (inline; extract to src/backtest/ at v2) -----

def run_backtest(ticker: str, df: pd.DataFrame, signal_fn,
                 *,
                 starting_capital: float = STARTING_CAPITAL,
                 brokerage_pct: float = BROKERAGE_PCT,
                 slippage_per_share: float = SLIPPAGE_PER_SHARE) -> dict:
    """Simulate signal_fn against df; return metrics + equity curve + trades."""
    pos = signal_fn(df)
    df = df.assign(pos=pos)

    # Slice to evaluation window: first LONG_WINDOW-1 rows have no MA-long.
    df_eval = df.iloc[LONG_WINDOW - 1:].reset_index(drop=True)

    cash = starting_capital
    shares = 0.0
    equity_curve_rows: list[dict] = []
    trades: list[dict] = []
    open_trade: dict | None = None
    prev_pos = 0

    for _, row in df_eval.iterrows():
        cur_pos = int(row["pos"])
        price = float(row["adj_close"])
        date = row["trade_date"]

        if prev_pos == 0 and cur_pos == 1:
            # ENTRY: buy at close + slippage; brokerage on notional.
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
            # EXIT: sell at close - slippage; brokerage on notional.
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

    # B&H baseline: gross, no costs (matches V-walk formula).
    first_price = float(df_eval.iloc[0]["adj_close"])
    bh_eq_series = starting_capital * df_eval["adj_close"] / first_price
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


# ----- Metrics -----

def compute_metrics(equity: pd.Series, trades: list[dict],
                    starting_capital: float, dates: pd.Series) -> dict:
    """Headline metrics from an equity curve + trade list.

    Robust to trade_count == 0: win-rate / avg-win / avg-loss returned
    as None. Sharpe is NaN if equity is flat (no daily volatility).
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


# ----- Output (ASCII only) -----

def _fmt_dollar(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"${v:,.2f}"


def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v * 100:+.2f}%"


def _fmt_sharpe(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:.3f}"


def print_ticker_block(ticker: str, result: dict) -> None:
    m = result["metrics"]
    bh = result["bh_metrics"]
    alpha = m["total_return_pct"] - bh["total_return_pct"]
    print(f"---- {ticker} ----")
    print(f"  Signal final equity:   {_fmt_dollar(m['final_equity'])}")
    print(f"  Signal total return:   {_fmt_dollar(m['total_return_dollar'])} "
          f"({_fmt_pct(m['total_return_pct'])})")
    print(f"  Signal ann. return:    {_fmt_pct(m['ann_return'])}")
    print(f"  Signal Sharpe:         {_fmt_sharpe(m['sharpe'])}")
    print(f"  Signal max DD:         {_fmt_dollar(m['max_dd_dollar'])} "
          f"({_fmt_pct(m['max_dd_pct'])})")
    print(f"  Trade count:           {m['n_trades']}")
    if m["n_trades"] > 0:
        print(f"  Win rate:              {_fmt_pct(m['win_rate'])}")
        print(f"  Avg win:               {_fmt_dollar(m['avg_win_dollar'])} "
              f"({_fmt_pct(m['avg_win_pct'])})")
        print(f"  Avg loss:              {_fmt_dollar(m['avg_loss_dollar'])} "
              f"({_fmt_pct(m['avg_loss_pct'])})")
        first_entry = result["trades"][0]["entry_date"].strftime("%Y-%m-%d")
        print(f"  First entry date:      {first_entry}")
    else:
        print(f"  Win rate / avg win / avg loss: N/A (no closed trades)")
    print(f"  B&H total return:      {_fmt_dollar(bh['total_return_dollar'])} "
          f"({_fmt_pct(bh['total_return_pct'])})")
    print(f"  B&H ann. return:       {_fmt_pct(bh['ann_return'])}")
    print(f"  B&H Sharpe:            {_fmt_sharpe(bh['sharpe'])}")
    print(f"  B&H max DD:            {_fmt_dollar(bh['max_dd_dollar'])} "
          f"({_fmt_pct(bh['max_dd_pct'])})")
    print(f"  ALPHA over B&H:        {_fmt_pct(alpha)}")
    print()


def print_aggregate(results: list[dict]) -> None:
    n = len(results)
    sig_total_d = sum(r["metrics"]["total_return_dollar"] for r in results)
    bh_total_d = sum(r["bh_metrics"]["total_return_dollar"] for r in results)
    sig_avg_pct = sum(r["metrics"]["total_return_pct"] for r in results) / n
    bh_avg_pct = sum(r["bh_metrics"]["total_return_pct"] for r in results) / n
    avg_alpha = sig_avg_pct - bh_avg_pct
    total_trades = sum(r["metrics"]["n_trades"] for r in results)
    sig_sharpes = [r["metrics"]["sharpe"] for r in results
                   if not pd.isna(r["metrics"]["sharpe"])]
    bh_sharpes = [r["bh_metrics"]["sharpe"] for r in results
                  if not pd.isna(r["bh_metrics"]["sharpe"])]
    avg_sharpe_sig = float(np.mean(sig_sharpes)) if sig_sharpes else float("nan")
    avg_sharpe_bh = float(np.mean(bh_sharpes)) if bh_sharpes else float("nan")
    avg_max_dd = float(np.mean([r["metrics"]["max_dd_pct"] for r in results]))
    n_winners = sum(
        1 for r in results
        if (r["metrics"]["total_return_pct"] - r["bh_metrics"]["total_return_pct"]) > 0
    )

    print("==== AGGREGATE (across all tickers) ====")
    print(f"  Total signal $ return (sum):   {_fmt_dollar(sig_total_d)}")
    print(f"  Total B&H $ return    (sum):   {_fmt_dollar(bh_total_d)}")
    print(f"  Avg signal % return:           {_fmt_pct(sig_avg_pct)}")
    print(f"  Avg B&H % return:              {_fmt_pct(bh_avg_pct)}")
    print(f"  AVG ALPHA over B&H:            {_fmt_pct(avg_alpha)}")
    print(f"  Signal beats B&H on:           {n_winners} / {n} tickers")
    print(f"  Total trades across universe:  {total_trades}")
    print(f"  Avg signal Sharpe:             {_fmt_sharpe(avg_sharpe_sig)}")
    print(f"  Avg B&H Sharpe:                {_fmt_sharpe(avg_sharpe_bh)}")
    print(f"  Avg signal max DD:             {_fmt_pct(avg_max_dd)}")


# ----- Main -----

def main() -> int:
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    client = create_client(url, key)

    resp = client.table("stocks").select("ticker").order("ticker").execute()
    tickers = sorted({r["ticker"] for r in resp.data})
    print(f"Backtest universe ({len(tickers)} tickers): {tickers}")
    print(
        f"Engine: {SHORT_WINDOW}/{LONG_WINDOW} SMA crossover on adj_close. "
        f"Long-only. Hold until opposite signal."
    )
    print(
        f"Capital: ${STARTING_CAPITAL:,.0f} per ticker. "
        f"Brokerage: {BROKERAGE_PCT * 100}%/side. "
        f"Slippage: ${SLIPPAGE_PER_SHARE}/share/side."
    )
    print(
        f"B&H baseline: gross (no costs); matches V-walk verification formula."
    )
    print()

    RESULTS_DIR.mkdir(exist_ok=True)

    results = []
    for t in tickers:
        df = fetch_full_series(client, t)
        result = run_backtest(t, df, ma_crossover_signal)
        results.append(result)
        print_ticker_block(t, result)

        csv_name = t.replace(".", "_")
        out_path = RESULTS_DIR / f"equity_curve_{csv_name}.csv"
        eq_csv = result["equity_curve"].copy()
        eq_csv["trade_date"] = eq_csv["trade_date"].dt.strftime("%Y-%m-%d")
        eq_csv.to_csv(out_path, index=False)

    print_aggregate(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
