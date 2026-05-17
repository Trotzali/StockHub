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
