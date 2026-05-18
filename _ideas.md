# _ideas.md

Banked future directions. Things we've considered but deliberately
deferred. Promoted to _project_state.md open WPs when scope allows.

═══════════════════════════════════════════════════════
BANKED (PHASE 2+ AFTER ASX EQUITIES VALIDATED)
═══════════════════════════════════════════════════════

WP-CRYPTO-SOCIAL-SIGNAL-ENGINE
  Second section in the same app for low-cap crypto / "shitcoins".
  Different signal logic: social-sentiment driven (Twitter API, Reddit
  API, Discord bot monitoring) rather than technicals. Same app shell,
  separate signal engine and data feeds. Defer until ASX engine has
  demonstrated edge — mixing both during validation violates "one
  hypothesis at a time".

WP-EXPAND-US-MARKETS
  Add US equities universe once ASX engine is validated. Different data
  source mix (likely Alpaca or Polygon free tier), same signal core.

WP-OPTIONS-STRATEGIES
  Covered calls and cash-secured puts on validated long positions. Only
  after equities engine is producing genuine edge. Year 2+.

WP-EXEC-BROKER-API-INTEGRATION
  Automated execution via Stake / IBKR / Alpaca API. Manual execution
  until live validation is solid. Year 2+.

WP-FRONTEND-NEXTJS-MIGRATION
  Move off Streamlit to Next.js on Vercel if/when the app outgrows
  Streamlit's UX ceiling. Only if needed.

WP-DB-MIGRATIONS-CLI
  Adopt Supabase CLI for proper migration management once schema
  starts churning. For MVP we run DDL via Supabase SQL Editor and
  track migration files manually in /migrations. Promote when the
  manual track-by-git workflow starts feeling fragile.

WP-DB-RLS-POLICIES
  Design and apply Row Level Security policies on stocks/prices/signals
  (and any future tables) for the day we expose data via anon or
  authenticated keys. Currently RLS is ENABLED on all three tables with
  NO policies defined — meaning anon/authenticated access returns zero
  rows by default. Service_role bypasses RLS so backend scripts and
  Streamlit app (using service_role) work normally. Bank status: blocked
  until we have a public-facing surface requiring non-service-role access.

WP-UI-FRONTEND-STACK-ARM64-RESOLUTION
  When entering the UI WP arc, first resolve win_arm64 wheel
  availability for streamlit 1.x's transitive deps (primarily
  pyarrow). Resolution paths (rough preference order):
    1. Pin pyarrow to a version with win_arm64 wheels (if one exists)
    2. Switch UI framework (Gradio, Dash, FastAPI + HTMX) whose deps
       clear win_arm64 cleanly
    3. Install x64 Python alongside, run UI process under emulation
    4. Build pyarrow from source (last resort)
  DO NOT accept streamlit==0.8 silent-downgrade as a workaround.
  Gates: WP-UI-STREAMLIT-SHELL (or whatever UI WP we land on).

WP-DB-DIRECT-SQL-ESCAPE-HATCH
  If a future workload genuinely needs ad-hoc SQL (no current use
  case demands it — all EOD signal work fits PostgREST + pandas).
  Resolution options:
    - Install x64 Python in parallel venv just for batch SQL jobs
    - Use Supabase Database Functions (RPC) for custom SQL via REST
    - Wait for a PG driver to ship win_arm64 wheels
  Banked because we may eventually want server-side aggregation or
  window functions for heavy backtests.

WP-DATA-UNIVERSE-ASX200
  Expand the hardcoded 10-ticker blue-chip list in
  scripts/fetch_yfinance.py to the full ASX 200. Source TBD —
  candidates: scrape ASX index composition page, use a maintained
  list from a finance package (yfinance lacks index-membership
  API), or pull from Alpha Vantage / Finnhub free tier. Decide
  refresh cadence (quarterly index reconstitution).

WP-DATA-STOCKS-METADATA-ENRICHMENT
  Populate the currently-NULL stocks columns (sector, industry,
  market_cap) via yfinance Ticker.info per ticker. Weekly refresh
  job — info changes slowly. Separate from the daily price fetch
  (different rate-limit profile, different failure tolerance).
  Banked because v1 fetcher ships minimal stocks rows; enrichment
  is a layer on top.

WP-INFRA-SCHEDULER
  Automated daily run of scripts/fetch_yfinance.py post-ASX close.
  Recommend Windows Task Scheduler for v1 (no extra deps, native
  to the box). Trigger ~17:30 AEST (after 16:00 ASX close, before
  late corrections). Capture stdout/stderr to a rotated log file
  in scripts/logs/. Consider an exit-code-aware retry wrapper if
  silent failures bite.

WP-INFRA-SCHEMA-DRIFT-SCRIPT
  Formalize the V-walk done in session 2 (T2 read-only,
  NO_DRIFT_DETECTED on 25/25 columns) into a committed script —
  scripts/verify_schema.py — for repeatable audits. Pulls the
  expected schema from migrations/001_initial_schema.sql,
  introspects deployed schema via PostgREST OpenAPI (/rest/v1/
  with Accept: application/openapi+json), diffs by column name +
  PostgREST type. Exit 0 = NO_DRIFT_DETECTED, exit non-zero +
  diff report on drift.

WP-INFRA-YFUTILS-EXTEND-RETRY-WRAPPER
  Generalize the 3-attempt exponential backoff (1s/2s/4s
  delays) currently duplicated as fetch_with_retry() in
  scripts/fetch_yfinance.py and fetch_history_with_retry()
  in scripts/backfill_historical.py into a shared helper
  in src/data/yfinance_utils.py. Proposed signature:
    fetch_with_retry(call: Callable[[], pd.DataFrame],
                     delays: Sequence[float] = (1, 2, 4),
                     on_attempt: Callable[[int, Exception], None] | None = None,
                     ) -> pd.DataFrame
  Surfaced as a TODO in def6718. Low-priority refactor —
  bank until a third consumer (WP-DATA-STOCKS-METADATA-
  ENRICHMENT is the likely trigger) makes the duplication
  actively painful.

WP-INFRA-INTRADAY-FILTER
  scripts/fetch_yfinance.py and scripts/backfill_historical.py
  currently have no volume>0 / "is this bar finalised?" filter.
  Today's intraday bars get picked up by daily runs during market
  hours (volume starts at 0 and accumulates through the session).
  scripts/seed_xjo.py at bfaa817 applies the right pattern inline
  (df = df[df['volume'] > 0]) and dropped 5 historical zero-volume
  ^AXJO bars + would have dropped today's intraday bar if yfinance
  had served one. Apply the same filter inline in both fetcher
  scripts, OR extract a shared helper in src/data/yfinance_utils.py
  (intraday_filter or finalised_bars_only). Trigger: next time the
  daily fetcher runs during market hours or a stock's intraday bar
  surfaces as a row in production prices.

WP-INFRA-UNIVERSE-CENTRALIZE
  TICKERS dict is duplicated across scripts/fetch_yfinance.py and
  scripts/backfill_historical.py (now 11 entries each after ^AXJO
  added in bfaa817). Two consumers managed manually so far; drift
  is a real risk on next ticker addition. Consolidate into
  src/data/universe.py with BLUE_CHIPS_ASX (10) + BENCHMARKS
  (1: ^AXJO) lists, both consumed via import. Trigger: 3rd
  consumer adds the same dict, OR WP-DATA-UNIVERSE-ASX200 fires
  (which would inflate the duplication from 11 to 200+ entries).

WP-DB-BENCHMARKS-TABLE
  ^AXJO sits in the stocks table as of bfaa817. The stocks table
  semantically holds tradeable equities; an index is a different
  thing. Functionally fine (FK from prices works, queries work,
  is_active flag works), cosmetically a mismatch. Refactor: add
  a benchmarks table with the same shape as stocks but semantically
  for indexes / reference series, migrate ^AXJO over, update FK
  from prices (via polymorphic pattern OR split into prices +
  benchmark_prices). Trigger: 3+ benchmark series (e.g. ^AXJO +
  ^GSPC + ^IXIC for US comparison) OR cosmetic mismatch starts
  causing actual confusion. Defer until then; the current state
  is honest and works.

═══════════════════════════════════════════════════════
NOTES / CALIBRATION
═══════════════════════════════════════════════════════

Lessons carried from WedgeBet:
- Beating efficient markets is brutally hard. Humble expectations.
- Backtest discipline is non-negotiable.
- Build infra to enable fast signal iteration, not the other way around.
- Don't fall in love with the system; fall in love with the validation
  process.

Process learnings (SESSION 2):
- Reconcile-commit self-reference improvement: use
  `git log -1 --oneline` wording in _timeline.md instead of
  [close-sha] placeholders. Eliminates the next-session-open
  hygiene patch entirely.
- TERMINAL MAP relocation — _project_state.md currently houses
  a TERMINAL MAP block which is inherently session-state
  (terminal status is mid-session, not project-state). Consider
  relocating to _timeline.md session entries where it lives
  naturally. Defer the refactor until it actively causes
  confusion.

Process learnings (SESSION 3):
- Gitignore pattern hygiene — anchored vs unanchored.
  `pattern/` in .gitignore matches any directory of that
  name anywhere in the tree; `/pattern/` matches only at
  repo root. 4be60e1 → fd8ba2e arc: `data/` (unanchored)
  silently excluded src/data/yfinance_utils.py and
  src/data/__init__.py from staging; recovered by
  anchoring to `/data/`. For project-specific top-level
  directories (data/, logs/, build/), always anchor with
  the leading slash. Future .gitignore edits: review
  unanchored patterns whose names could conflict with a
  nested directory.
- First "shipped broken, recovered same session" arc.
  4be60e1 V-walked locally as PASS because the working
  tree had the files on disk — the broken state only
  manifests on a fresh clone of origin/master. V-walks
  against the working tree don't catch staging-set gaps;
  only `git check-ignore -v <new-paths>` does, before
  push. Banked into CLAUDE.md commit-discipline chain at
  session-3 close.

Process learnings (SESSION 4):
- V1 backtest result as data point: 50/200 SMA long-only on 10 ASX
  blue chips, 2022-02-25 → 2026-05-15, avg alpha over B&H is -30
  percentage points. Engine proven correct (CBA.AX V-walked end-to-
  end, B&H math reconciled to the cent). Signal family has real
  defensive properties (CSL.AX +47.6% alpha during a 60% B&H
  drawdown — the strategy sat in cash). Misapplied as a standalone
  long-only signal on a bull-trending universe. Useful as a regime
  filter or defensive sleeve, NOT a primary alpha generator.
  Relevant input for any future signal that incorporates MA
  crossovers in any form.
- Per-ticker parameter tuning is curve-fitting on this universe.
  Tuning (short, long) per ticker on 10 tickers × 4y multiplies the
  parameter search space by 10x with no statistical justification.
  Do NOT include in WP-SIGNAL-MA-CROSSOVER-GRID-V1. Aggregate
  optimisation only. Bank as red-flag anti-pattern for any future
  per-ticker tuning impulse.
- ASCII-only stdout in PowerShell promoted from session-3
  calibration to CLAUDE.md environment notes (item 8 — see
  CLAUDE.md). Validated session 4: clean Phase B stdout run with
  ASCII-only discipline after a Phase A probe-exit crash on `→`.

Process learnings (SESSION 5):
- Engine protocol: signal_fn -> signal_series. The V2 extraction
  (8782a6a) changed run_backtest's signature: caller precomputes
  the position series, engine slices from first non-NaN. Required
  for V3's holdout-with-full-series-precompute pattern (compute
  signal once over full series, slice into train/test, two engine
  calls). signal_fn-as-argument couples signal-computation timing
  to engine internals; signal_series-as-argument cleanly separates
  the two. Pattern validated, applies to any future signal family.
- ffill pattern for multi-signal composition (V3 deviation): when
  joining a primary signal with an auxiliary indicator that may
  have data gaps (XJO's 5 historical zero-volume days), .ffill()
  the auxiliary onto the primary's date index BEFORE element-wise
  multiplication. Plain NaN propagation makes the engine see
  1 -> NaN -> 1 as exit + re-entry; ffill carries the previous
  day's auxiliary state through the gap, matching the realistic
  "no data today, carry yesterday forward" semantics a live trader
  would use.
- Empirical anti-overfit inversion (V2): test Sharpe HIGHER than
  train Sharpe across all 5 (short, long) combos. Standard overfit
  pattern is the opposite (train > test). The bull market in the
  test slice (2024-07 -> 2026-05) flattered the signals more than
  the train slice (2022-02 -> 2024-07); holdout-period regime
  matters as much as signal logic. Lesson: holdout Sharpe alone is
  not a free pass; check alpha-over-B&H in BOTH windows.
- Empirical churn-vs-block (V3): regime filter on a bull-trending
  universe with mostly-long stock signals introduces ~3.5x more
  entries than it blocks (universe-wide on V3 winner (30, 100):
  80 V2 entries -> 160 V3 entries; 31 blocked, 111 added). Each
  added entry is a regime cycle inside a held position = exit +
  re-entry round-trip cost. The blocking benefit must overcome the
  churn cost; on this universe / window it doesn't. Future regime-
  filter designs should consider entry-only gating (regime gates
  new entries but never forces exits).
- Data quality (yfinance ^AXJO): 5 historical zero-volume bars in
  the 2021-2026 window (likely index reconstitution / data-gap
  days). volume>0 filter at seed time was sufficient to drop them;
  worth knowing for future benchmark-series seeds.
- Best-parameters context-dependence: V2 winner (50, 200) became
  V3's worst-degrading combo; V3 winner shifted to (30, 100). The
  "best" (short, long) combo isn't intrinsic — it depends on the
  filter / regime / portfolio context applied on top. Lesson:
  re-optimise per signal architecture; don't carry V2-winner
  parameters as defaults into V3-style WPs.
