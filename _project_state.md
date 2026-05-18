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
(between WPs — SESSION 6 opens with design conversation on next
signal family: momentum / mean-reversion / volatility breakout /
universe expansion. MA crossover family closed across 3 refutations
this session — see _build_log.md and _timeline.md.)

Closed in SESSION 1:
  WP-BOOTSTRAP-REPO-INIT              — 73b2c8d
  WP-RECONCILE-POST-BOOTSTRAP         — d57dbcd
  WP-DB-SCHEMA-INIT                   — a1d825d  (with RLS amendment)
  WP-RECONCILE-MILESTONE              — 16ebfcb  (named "SESSION 1 CLOSE"
                                                  prematurely; treat as
                                                  mid-session milestone)
  WP-DEV-ENV-SETUP                    — 1ed6d8b  (after four-round
                                                  ARM64 wheel-gap odyssey)
  WP-RECONCILE-SESSION-1-CLOSE        — 401c938  (actual close)

Closed in SESSION 2:
  WP-HYGIENE-TIMELINE-SHA-BACKFILL    — 70e7193
  WP-INFRA-CLAUDE-MD                  — 9600a81
  WP-DATA-YFINANCE-FETCHER            — 7bacd7f
  WP-RECONCILE-SESSION-2-CLOSE        — 5799004

Closed in SESSION 3:
  WP-INFRA-SRC-LAYOUT                 — 4be60e1  (T1, shipped broken —
                                                  `data/` pattern in
                                                  .gitignore hid src/data/*
                                                  from staging)
  WP-INFRA-GITIGNORE-RESCOPE          — fd8ba2e  (T1, recovery: anchored
                                                  data/ → /data/, ships
                                                  missed files)
  WP-DATA-HISTORICAL-BACKFILL         — def6718  (T2, 5y EOD × 10 blues —
                                                  12,650 rows in prices)
  WP-RECONCILE-SESSION-3-CLOSE        — 56ddc53  (opportunistic backfill
                                                  at session-4 close)

Closed in SESSION 4:
  WP-SIGNAL-MA-CROSSOVER-V1           — 00e2141  (T1, engine-first single-
                                                  signal backtest — engine
                                                  proven, signal refuted at
                                                  avg -30% alpha over B&H)
  WP-RECONCILE-SESSION-4-CLOSE        — 45d8220  (opportunistic backfill
                                                  at session-5 close)

Closed in SESSION 5:
  WP-SIGNAL-MA-CROSSOVER-GRID-V1      — 8782a6a  (T1, engine extraction +
                                                  V2 5-combo grid — every
                                                  combo loses to B&H on
                                                  train AND test alpha)
  WP-SIGNAL-MA-CROSSOVER-REGIME-FILTER-V1
                                      — bfaa817  (T1, XJO MA-200 regime
                                                  filter — refuted; filter
                                                  churns more than it blocks)
  WP-RECONCILE-SESSION-5-CLOSE        — (see `git log -1 --oneline`)

See _build_log.md for commit details.

═══════════════════════════════════════════════════════
OPEN WPs (BANKED, NOT STARTED)
═══════════════════════════════════════════════════════
Foundation (Phase 1, months 1-2):
  WP-INFRA-YFUTILS-EXTEND-RETRY-WRAPPER
                                 — Generalize the 3-attempt exponential
                                   backoff currently duplicated as
                                   fetch_with_retry() in
                                   scripts/fetch_yfinance.py and
                                   fetch_history_with_retry() in
                                   scripts/backfill_historical.py into a
                                   shared helper in src/data/yfinance_utils.py.
                                   Surfaced as a TODO in def6718.
                                   Low priority — bank until a third consumer
                                   makes the duplication actively painful.
  WP-UI-STREAMLIT-SHELL          — Streamlit app, ticker dropdown, Plotly candlestick
                                   GATED ON: WP-UI-FRONTEND-STACK-ARM64-RESOLUTION
  WP-UI-MA-OVERLAY               — 20/50/200-day MA overlay

Foundation arc complete. MA crossover signal family fully
characterised across three refutations (00e2141 V1 single, 8782a6a
V2 grid, bfaa817 V3 regime-filtered). Engine + signal + paginated-
fetch helpers live in src/backtest/ + src/data/yfinance_utils.py.

Production state at session-5 close: 11 stocks (added ^AXJO regime
ticker), 13,910 prices (12,650 blue-chip + 1,260 XJO), 0 signals.

Next gate is the signal arc: SESSION 6 opens with design
conversation on the next signal family — momentum / mean-reversion
/ volatility breakout / universe expansion. Speculative regime-
filter variants retired with the MA family. UI shell remains
gated on WP-UI-FRONTEND-STACK-ARM64-RESOLUTION.

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
T1 — idle (closed WP-SIGNAL-MA-CROSSOVER-GRID-V1,
            WP-SIGNAL-MA-CROSSOVER-REGIME-FILTER-V1, + this reconcile)
T2 — idle / spare (not activated this session)
T3 — idle / spare (not activated this session)
T4 — held / spare
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

═══════════════════════════════════════════════════════
ENVIRONMENT NOTES (Windows 11 + PS 5.1)
═══════════════════════════════════════════════════════

Permanent gotchas — bake into every CC prompt on this box.

1. git commit messages
   Multi -m chains with backtick (`) continuation and empty -m ""
   separators get mangled by PS 5.1 quoting. Use either:
     - Single -m with embedded \n via $msg = @"...`n...`n..."@ ; git commit -m $msg
     - git commit -F <tempfile>, removing the tempfile before any push verification

2. File creation with UTF-8
   `Set-Content -Encoding utf8` writes UTF-8 WITH BOM on PS 5.1.
   Prefer the Write tool, or use:
     [System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))

3. Benign noise to ignore
   - LF→CRLF warnings on `git add` (Windows core.autocrlf default)
   - NativeCommandError text on `git push` when stderr is redirected
     — exit code is authoritative

4. Python
   Use `python` (3.12, has pip bound). Do NOT use `python3` (3.14, pip not bound).

5. Shell
   PowerShell 5.1, not Git Bash. Use New-Item / Set-Location / Get-Location
   for filesystem ops; avoid bash idioms like `mkdir -p` heredocs piped to commands.

6. Architecture (CRITICAL — surfaced WP-DEV-ENV-SETUP)
   Windows 11 on ARM64 (Snapdragon). Python 3.12.10 is the ARM64
   build; all venvs inherit this. Many PyPI packages with native
   C extensions have wheel-supply gaps for win_arm64 — confirmed
   gaps include psycopg2-binary, psycopg-binary (all versions),
   and pyarrow at modern versions. Pure-Python packages are fine.
   Always include "what arch is this box" in any new-project
   Phase A bootstrap inventory.

7. Pip install policy
   Always use `--only-binary :all:` for installs. Failure modes:
     (a) Silent sdist fallback — pip downloads .tar.gz and tries
         to compile, fails on Windows without build toolchain.
     (b) Silent resolver back-walk — pip exits 0 but resolves to a
         stale major (saw streamlit==0.8 from 2018 instead of 1.40+).
         Pip's exit 0 is necessary but NOT sufficient. Always
         sanity-check installed versions against current-stable
         expectations before pinning to requirements.txt.

8. DB driver policy
   supabase-py (REST/HTTPS) only. No native PG drivers — psycopg2-binary
   and psycopg-binary lack win_arm64 wheels at all versions. Our
   workload fits PostgREST cleanly: bulk inserts via .insert([...])
   chunked, range queries via .select().gte().lte(), analytics
   client-side in pandas. WP-DB-DIRECT-SQL-ESCAPE-HATCH banked for
   the day a workload genuinely needs ad-hoc SQL.

9. UI stack ARM64 risk
   streamlit 1.x hard-requires pyarrow, which has incomplete
   win_arm64 wheel coverage. WP-UI-FRONTEND-STACK-ARM64-RESOLUTION
   is gating work for the UI arc. Resolution paths (rough preference):
     - Pin pyarrow to a version with win_arm64 wheels (if one exists)
     - Switch UI framework (Gradio, Dash, FastAPI + HTMX)
     - Install x64 Python alongside, run UI under emulation
     - Build pyarrow from source (last resort)
   DO NOT pin streamlit==0.8 as a "workaround" — that's
   semantic poison.

10. Pandas 3.x .stack() semantics (surfaced WP-DATA-YFINANCE-FETCHER)
    The venv runs pandas==3.0.3. The new .stack() semantics require
    future_stack=True explicitly. Legacy stack(level=0) without that
    kwarg was a breaking change in pandas 3. Use:
      df.stack(level=0, future_stack=True)
    in any code that flattens a (Ticker, Field) MultiIndex DataFrame.

11. yfinance timezone divergence (surfaced WP-DATA-YFINANCE-FETCHER)
    yfinance Ticker.history returns tz-aware Australia/Sydney;
    yf.download returns tz-naive (already exchange-local). Never
    call .tz_convert('UTC').date() on ASX bars — evening UTC times
    land on the previous trade day. Use the trade_date() helper
    pattern from scripts/fetch_yfinance.py: if tzinfo, convert to
    Australia/Sydney first, then .date().

12. yfinance auto_adjust default (surfaced WP-DATA-YFINANCE-FETCHER)
    yfinance auto_adjust defaults to True (folds corporate-action
    adjustments into Close and DROPS Adj Close from the output).
    Always pass auto_adjust=False to preserve both raw Close and
    Adj Close — the schema has both columns NOT NULL.

13. Parallel-terminal sequencing (surfaced twice in SESSION 2)
    When a queued WP's Phase A captures a HEAD that advances by
    Phase B time (because another terminal shipped a commit in
    between), `git pull --ff-only origin master` in Phase B
    integrates safely as a fast-forward. Demonstrated twice in
    SESSION 2: T2's WP-INFRA-CLAUDE-MD over T1's hygiene push,
    and T2's V-walk over T1's fetcher push. Fast-forward only —
    if the pull would require a merge, STOP and report instead.
