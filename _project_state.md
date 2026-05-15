# _project_state.md

Current state of StockHub. Source of truth for scope, locked decisions,
and open work packages between sessions.

═══════════════════════════════════════════════════════
PROJECT
═══════════════════════════════════════════════════════
Name:       StockHub
Repo:       https://github.com/Trotzali/StockHub
Prod branch: master
Working dir: C:\Users\admin\Projects\StockHub
Owner:      Troy (admin@tjkcivil.com.au)
Cadence:    5-10 hrs/week, evenings
Horizon:    12 months to validate signals before scaling capital

═══════════════════════════════════════════════════════
GOAL
═══════════════════════════════════════════════════════
Beat the ASX retail crowd by 5-10% annually through a disciplined,
systematic, rules-based screening and trading system. Daily EOD signals
only — no intraday.

═══════════════════════════════════════════════════════
LOCKED DECISIONS
═══════════════════════════════════════════════════════
- ASX 200 universe initially (crypto/shitcoins banked for Phase 2+)
- Daily end-of-day signals only — no intraday reactive trading
- Python 3.12, Streamlit MVP, Supabase free tier, Plotly charts
- Data sources: yfinance (primary), Finnhub free, Alpha Vantage free
- Build for me, not as a product — optimise for fast iteration
- One signal hypothesis at a time
- Backtest before believing; paper-trade before live capital
- 12-month validation window before scaling beyond $1k-5k risk capital
- Branch: master (not main)

═══════════════════════════════════════════════════════
CURRENT WP
═══════════════════════════════════════════════════════
WP-BOOTSTRAP-REPO-INIT — in progress (this commit)

═══════════════════════════════════════════════════════
OPEN WPs (BANKED, NOT STARTED)
═══════════════════════════════════════════════════════
Foundation (Phase 1, months 1-2):
  WP-DB-SCHEMA-INIT             — Supabase project + stocks/prices/signals schema
  WP-DATA-YFINANCE-FETCHER      — Python script: ASX 200 daily OHLC -> Supabase
  WP-DATA-HISTORICAL-BACKFILL   — 5yr historical load
  WP-UI-STREAMLIT-SHELL         — Streamlit app, ticker dropdown, Plotly candlestick
  WP-UI-MA-OVERLAY              — 20/50/200-day MA overlay

Gate order: WP-DB-SCHEMA-INIT gates everything else.

Signal design (Phase 2, months 2-4):
  WP-SIGNAL-HYPOTHESIS-V1       — one clear hypothesis (leaning earnings surprise + RSI<40 + above 200MA)
  WP-INDICATORS-TA-CORE         — RSI, MACD, Bollinger Bands
  WP-FUNDAMENTALS-FILTERS       — P/E, earnings dates, sector
  WP-NEWS-SENTIMENT-OPTIONAL    — Finnhub/Alpha Vantage sentiment scoring

Backtest (Phase 3, months 4-6):
  WP-BACKTEST-ENGINE-CORE       — slippage, brokerage, realistic fills
  WP-BACKTEST-REGIMES           — 2020/2021/2022/2023-2025 cuts
  WP-BACKTEST-EQUITY-DRAWDOWN   — equity curve, drawdown, win/loss dist

Paper / live (Phases 4-5, months 6-12):
  WP-PAPER-TRADE-3MO            — live signals, fake money, 3 months min
  WP-LIVE-RISK-CAPITAL-START    — $1k-5k real money with hard risk limits

═══════════════════════════════════════════════════════
TERMINAL MAP (current session)
═══════════════════════════════════════════════════════
T1 — bootstrap (WP-BOOTSTRAP-REPO-INIT)
T2 — idle
T3 — idle
T4 — idle
T5 — held / spare

═══════════════════════════════════════════════════════
OPEN QUESTIONS
═══════════════════════════════════════════════════════
- Broker for eventual execution: Stake / IBKR / CommSec (defer until Phase 5)
- First signal hypothesis: leaning earnings surprise + technical confirm
- ASX 200 vs ASX 300 universe (locked to ASX 200 initially)

═══════════════════════════════════════════════════════
STATE FILES
═══════════════════════════════════════════════════════
- C:\Users\admin\Projects\StockHub\_project_state.md (this file)
- C:\Users\admin\Projects\StockHub\_build_log.md
- C:\Users\admin\Projects\StockHub\_ideas.md
- C:\Users\admin\Projects\StockHub\_timeline.md
