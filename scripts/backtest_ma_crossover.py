"""scripts/backtest_ma_crossover.py -- WP-SIGNAL-MA-CROSSOVER-V1 (refactored).

50-day / 200-day SMA crossover backtest on the ASX blue-chip universe.
Thin caller of extracted modules:
- src.data.yfinance_utils.fetch_prices_full (paginated read)
- src.backtest.signals.ma_crossover_signal
- src.backtest.engine.run_backtest

Locked decisions (unchanged from V1 — see WP-SIGNAL-MA-CROSSOVER-V1):
- Signal: golden cross (MA-50 > MA-200) = long; death cross = flat.
- Universe: all rows in `stocks` (currently 10 .AX tickers).
- Hold rule: until opposite signal. No stops / targets / time limits.
- Execution: trade at signal-day close.
- Costs: 0.1% brokerage + $0.01 slippage per share per side.
- Per-ticker $10,000 starting capital; 10 independent backtests.
- Warm-up: rows with NaN signal (no MA-long) excluded by the engine.
- Open positions at window end MTM'd to final adj_close.
- B&H baseline is gross.
- Output: per-ticker + aggregate metrics to stdout (ASCII only);
  results/equity_curve_<TICKER_AX>.csv per ticker.

Engine + signal + paginated-fetch helper extracted to src/backtest/
+ src/data/yfinance_utils.py in WP-SIGNAL-MA-CROSSOVER-GRID-V1
(second-consumer trigger). V1 behaviour preserved byte-identical
(regression V-walked at extraction).
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.backtest.engine import (
    BROKERAGE_PCT,
    SLIPPAGE_PER_SHARE,
    STARTING_CAPITAL,
    run_backtest,
)
from src.backtest.signals import LONG_WINDOW, SHORT_WINDOW, ma_crossover_signal
from src.data.yfinance_utils import fetch_prices_full

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"


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
        records = fetch_prices_full(client, t)
        df = pd.DataFrame(records)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df["adj_close"] = pd.to_numeric(df["adj_close"])
        df = df.sort_values("trade_date").reset_index(drop=True)
        signal = ma_crossover_signal(df)
        result = run_backtest(t, df, signal)
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
