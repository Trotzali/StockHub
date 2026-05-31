# _build_log.md

Shipped commits in chronological order. Each entry: SHA, WP, one-line
summary, date. Closed WPs migrate here from _project_state.md with their
commit SHA.

═══════════════════════════════════════════════════════
COMMITS
═══════════════════════════════════════════════════════

73b2c8d — 2026-05-15 — WP-BOOTSTRAP-REPO-INIT
  bootstrap: init StockHub repo with state files and gitignore
  Root commit on master. Established working dir
  C:\Users\admin\Projects\StockHub, initialised git, added remote
  origin → github.com/Trotzali/StockHub, seeded four canonical
  state files (_project_state.md, _build_log.md, _ideas.md,
  _timeline.md), .gitignore, README.md stub. First push set
  master as default branch.

d57dbcd — 2026-05-15 — WP-RECONCILE-POST-BOOTSTRAP
  reconcile: backfill bootstrap SHA, bank PS 5.1 environment notes
  - _build_log.md: bootstrap (73b2c8d) entry filled in
  - _timeline.md: SESSION 1 SHA backfilled, CALIBRATION NOTES appended
  - _project_state.md: WP-BOOTSTRAP-REPO-INIT closed, CURRENT WP
    advanced to WP-DB-SCHEMA-INIT, ENVIRONMENT NOTES section added
    (PS 5.1 gotchas — permanent for this box)
  - _ideas.md: banked WP-DB-MIGRATIONS-CLI
  Gates: 73b2c8d.

a1d825d — 2026-05-16 — WP-DB-SCHEMA-INIT
  WP-DB-SCHEMA-INIT: initial schema + .env template + RLS amendment
  - migrations/001_initial_schema.sql: stocks/prices/signals tables
    with indexes, comments, FK constraints, updated_at trigger,
    wrapped in BEGIN/COMMIT for atomic apply.
  - .env.example: committed credentials template; .env gitignored.
  - AMENDMENT: RLS enabled at Supabase SQL Editor apply-time via
    "Run and enable RLS". Migration file amended with ALTER TABLE
    ENABLE ROW LEVEL SECURITY for all three tables to keep file = DB
    state. No policies defined; access via service_role only (which
    bypasses RLS).
  - _ideas.md: banked WP-DB-RLS-POLICIES for future public surface.
  Gates: d57dbcd.

1ed6d8b — 2026-05-16 — WP-DEV-ENV-SETUP
  WP-DEV-ENV-SETUP: Python venv + pinned requirements + DB smoke test
  - .venv/ with Python 3.12 ARM64 (gitignored)
  - requirements.txt: 4 top-level pins (python-dotenv 1.2.2, supabase
    2.25.1, pandas 3.0.3, yfinance 1.3.0) + 50 transitives. All ==
    pinned, all win_arm64 wheels or pure-Python.
  - scripts/smoke_test_db.py: end-to-end validator via supabase-py
    with service_role (RLS bypass). PASSed pre- and post-commit:
    prices, signals, stocks all reachable.

  Closed after four-round wheel-gap odyssey that surfaced the
  underlying ARM64 platform:
    R1: psycopg2-binary==2.9.12 → silent sdist, no pg_config
    R2: psycopg2-binary==2.9.10 → same sdist fallback
    R3: psycopg[binary] + --only-binary :all: → ResolutionImpossible.
        Surfaced root cause: win_arm64 has no PG-driver wheels at any
        version. Pivot to supabase-py.
    R4: install exit 0 but streamlit silently resolved to 0.8 (2018
        release). T1 caught semantic-failure-as-success. Dropped
        streamlit+plotly from WP, banked to UI WP. Recreated venv.

  Banked WPs: WP-UI-FRONTEND-STACK-ARM64-RESOLUTION,
              WP-DB-DIRECT-SQL-ESCAPE-HATCH.
  Gates: 16ebfcb.

70e7193 — 2026-05-16 — WP-HYGIENE-TIMELINE-SHA-BACKFILL
  Patched two [actual-close-sha] placeholders in
  _timeline.md to 401c938; rewrote the line 196-198
  meta-note paragraph to past tense. Phase A discovered a
  third occurrence of the literal string (the meta-note
  itself, not a placeholder) — naive replacement would
  have corrupted the file. Same pattern as the 16ebfcb
  patch from session 1.
  Gates: 401c938.

9600a81 — 2026-05-16 — WP-INFRA-CLAUDE-MD
  Authored CLAUDE.md at repo root so Claude Code auto-
  loads the standing working-model rules on terminal
  start. Per-prompt scaffolding now drops env notes,
  commit discipline, identity-stamp convention, state-file
  naming, and report format. Gate anomaly resolved cleanly
  via `git pull --ff-only` in Phase B — T1's hygiene
  commit landed between T2's Phase A read and Phase B
  execution.
  Gates: 70e7193.

7bacd7f — 2026-05-16 — WP-DATA-YFINANCE-FETCHER
  scripts/fetch_yfinance.py at 192 lines. Daily ASX EOD
  ingestion of 10 hardcoded blue chips (CBA, BHP, RIO,
  WBC, NAB, ANZ, WES, WOW, TLS, CSL) into Supabase via
  yfinance. Single yf.download batch with
  auto_adjust=False, flattened via stack(level=0,
  future_stack=True), idempotent upsert on (ticker,
  trade_date). 7-day fetch window per run (gap-resilient).
  3-attempt exponential backoff (1s/2s/4s). NaN-guard
  hardened across all 6 NOT NULL price columns. Stocks
  rows minimal (ticker, name, is_active=true). Dry-run
  validated against production: 10 stocks + 70 prices
  across all 10 expected tickers, zero dropped.
  Gates: 9600a81.

4be60e1 — 2026-05-17 — WP-INFRA-SRC-LAYOUT
  Pure refactor. Extracted trade_date(), df_to_records(),
  chunked() (now private), upsert_prices(), and
  UPSERT_BATCH_SIZE from scripts/fetch_yfinance.py into a
  new shared module src/data/yfinance_utils.py. Daily
  fetcher imports via a 4-line sys.path prelude.
  Import mechanism (Phase A4 decision): sys.path
  manipulation in each consumer, not pyproject.toml
  editable install. Lighter — no packaging surface area
  for an MVP single-repo screener.
  Behaviour unchanged: V-walked 10 stocks + 70 prices,
  zero dropped, idempotent same-day rerun matches the
  7bacd7f baseline.
  Shipped broken: `data/` pattern in .gitignore (line 21)
  silently excluded src/data/yfinance_utils.py and
  src/data/__init__.py from staging. origin/master ended
  up with a fetcher importing a non-tracked module.
  Recovered in fd8ba2e.
  Gates: 5799004.

fd8ba2e — 2026-05-17 — WP-INFRA-GITIGNORE-RESCOPE
  Recovery of 4be60e1. .gitignore line 21 `data/`
  matched any directory named data/ anywhere in the tree,
  including src/data/. Anchored to `/data/` (repo root
  only); top-level data/ remains ignored, reserved for
  future raw-data dumps. Ships the two src/data/ files
  that were missed in 4be60e1.
  V-walked post-fix: 10 stocks + 70 prices, zero dropped,
  idempotent same-day rerun matches baseline.
  Methodology lesson banked: `git status -s` shorthand
  `?? src/` hides which files inside got .gitignore'd;
  `git check-ignore -v <new-paths>` is the pre-stage trip
  wire. Follow-ups banked for session-close reconcile:
  CLAUDE.md amendment + _ideas.md calibration entry on
  anchored gitignore patterns.
  Gates: 4be60e1.

def6718 — 2026-05-17 — WP-DATA-HISTORICAL-BACKFILL
  One-shot scripts/backfill_historical.py. Sequential
  per-ticker yf.Ticker(t).history(period="5y",
  auto_adjust=False) over the 10 ASX blue chips from
  the daily fetcher's hardcoded universe. yf.download
  batch caps at ~60d (T3 session-2 recon), so per-ticker
  is the only viable path for a 5y window. Consumes
  existing helpers from src/data/yfinance_utils.py
  (df_to_records, upsert_prices, transitively trade_date,
  chunked, UPSERT_BATCH_SIZE); module unchanged this WP.
  Per-ticker upsert cadence; idempotent via existing
  on_conflict=(ticker, trade_date). IPO/delisting
  tolerance: WARN if a ticker returns <1000 rows, do not
  fail the run. 3-attempt exponential backoff matching
  the daily fetcher.
  V-walked: dry-run 12,650 total rows (10 × 1265), no
  WARNs, zero NaN drops; full run pre-count 70 (T1 daily
  overlap) → post-count 12,650 = 12,580 new rows, zero
  dropped; idempotency rerun net new rows 0; post-run
  SELECT confirms 12,650 prices across 10 tickers, per-
  ticker earliest 2021-05-17 uniform, latest 2026-05-15,
  count 1265 each.
  Pre-stage trip wire (post-fd8ba2e methodology):
  `git check-ignore -v scripts/backfill_historical.py`
  returned empty (exit 1, not ignored).
  Banked follow-up: WP-INFRA-YFUTILS-EXTEND-RETRY-WRAPPER
  (generalize the 3-attempt backoff duplicated as
  fetch_history_with_retry into a shared helper).
  Gates: fd8ba2e.

00e2141 — 2026-05-18 — WP-SIGNAL-MA-CROSSOVER-V1
  Engine-first single-signal backtest. 50/200 SMA crossover on
  adj_close, long-only, hold-until-opposite-signal, signal-day-
  close execution, 0.1% brokerage + $0.01 slippage per side. Per-
  ticker $10k starting capital across 10 ASX blue chips. Inline
  thin generic run_backtest(signal_fn, ticker, df, ...) engine in
  scripts/backtest_ma_crossover.py; ma_crossover_signal,
  compute_metrics defined alongside. Inline paginated
  fetch_full_series helper (PostgREST free-tier 1000-row cap
  workaround — Phase A finding).

  Outputs: summary metrics per ticker + aggregate to stdout
  (ASCII-only per session-3 calibration); per-ticker equity curve
  to results/equity_curve_<TICKER_AX>.csv (filename substitution
  `.` -> `_`). results/ added to .gitignore as /results/
  (anchored per session-3 lesson).

  V-walked: CBA.AX first golden cross 2022-04-06 verified by hand
  (MA-50 below MA-200 day-before, above on signal day). B&H math
  reconciled to the cent. Equity curve start matches MA-200 warm-
  up cutoff 2022-02-25 across all 10 tickers (uniform per Phase A).

  Headline result: signal underperforms B&H by avg -30 percentage
  points across the universe over 2022-02-25 -> 2026-05-15. 2/10
  tickers beat B&H — CSL.AX +47.6% alpha (defensive: signal sat in
  cash through 60% drawdown), WES.AX +17.3% alpha (1 trade, 100%
  win rate, noise more than signal). Signal family confirmed to
  have real defensive properties; misapplied as standalone long-
  only on a bull-trending universe. Banked as data point for V2
  grid sweep and any future signal exploration that uses MA
  crossovers in any form.

  Banked follow-ups: WP-INFRA-YFUTILS-FETCH-PRICES-PAGINATED (in
  _ideas.md, current consumer count = 1; backfill_historical writes
  only, doesn't count). WP-SIGNAL-MA-CROSSOVER-GRID-V1 promoted to
  Foundation. ASCII-only-stdout convention promoted to CLAUDE.md.
  Gates: 56ddc53.

8782a6a — 2026-05-18 — WP-SIGNAL-MA-CROSSOVER-GRID-V1
  Engine extraction + V2 5-combo grid sweep with 60/40
  train/test holdout at 2024-07-01. New src/backtest/
  package: __init__.py, engine.py (run_backtest +
  compute_metrics + compute_buy_and_hold + constants),
  signals.py (ma_crossover_signal moved with NaN warm-up
  contract). Engine API signature changed: signal_fn ->
  signal_series. Caller precomputes; engine slices from
  first non-NaN. Required for V3's full-series-precompute
  holdout pattern.

  fetch_prices_full + PAGE_SIZE=1000 appended to
  src/data/yfinance_utils.py (closes banked
  WP-INFRA-YFUTILS-FETCH-PRICES-PAGINATED via second-
  consumer trigger). scripts/backtest_ma_crossover.py
  refactored as thin caller — V1 regression byte-identical
  (md5 c0803f6823eb696c9320dded116d6630 before and after).

  scripts/backtest_ma_crossover_grid.py: 5 combos =
  [(10,30), (20,50), (30,100), (50,100), (50,200)] x 10
  ASX blue chips x 2 windows. Aggregate-only optimisation
  on train Sharpe; tiebreak avg_total_return.

  Headline: every combo loses to B&H on both train and
  test alpha. V2 winner (50, 200) test alpha -5.16%, test
  Sharpe 0.635 — same combo as V1, by design the least-bad
  of the family. V-walk: aggregate train/test Sharpe
  arithmetic reconciles + CBA.AX first golden cross
  2022-04-06 hand-verified.
  6 files changed, 637 insertions, 245 deletions.
  Gates: 45d8220.

bfaa817 — 2026-05-19 — WP-SIGNAL-MA-CROSSOVER-REGIME-FILTER-V1
  Regime-filtered grid sweep: same 5 combos and same 60/40
  split as V2, with MA-crossover signal AND-ed against an
  XJO MA-200 regime filter. One-off scripts/seed_xjo.py
  seeded 1 stocks row + 1260 prices rows for ^AXJO over
  2021-05-18..2026-05-15 (filtered volume>0 + date<=max
  blue-chip date; dropped 5 historical zero-volume bars).
  ^AXJO added to TICKERS dict in scripts/fetch_yfinance.py
  + scripts/backfill_historical.py for future runs.

  src/backtest/signals.py append-only: regime_above_ma(
  df, window=200, close_col='adj_close'). Same NaN-warm-up
  + 0/1 contract as ma_crossover_signal.

  scripts/backtest_ma_crossover_regime_grid.py: V3 grid.
  Regime signal computed once over full XJO series;
  combined per ticker via date-aligned element-wise
  multiplication. DEVIATION: build_combined_signal uses
  .ffill() on regime alignment. Engine first-pass crashed
  on int(NaN) from XJO's 5 historical zero-volume gaps
  inside held positions; ffill matches the live-trader
  "carry yesterday's regime through missing data" semantic
  and avoids spurious exit+re-entry transactions.

  Headline: regime filter REFUTED. V3 winner shifted to
  (30, 100) but every cell of V2-vs-V3 delta is negative.
  V3 winner test alpha -19.42% (vs V2 winner -5.16%). V2's
  best combo (50, 200) becomes V3's worst-degrading.

  Key mechanism: filter CHURNS more than it BLOCKS.
  Universe-wide on (30, 100): 80 V2 entries -> 160 V3
  entries (31 blocked + 111 NEW). The 111 added entries
  are regime cycles inside V2's held positions; each is
  an exit + re-entry round-trip cost. Brokerage + slippage
  dominate the blocking benefit on this universe.

  MA crossover family chapter closed across 3 refutations
  (V1 00e2141 + V2 8782a6a + V3 bfaa817). Defensive
  property real, family dead as primary alpha generator.

  Banked: WP-INFRA-INTRADAY-FILTER (defensive volume>0
  filter for daily fetcher), WP-INFRA-UNIVERSE-CENTRALIZE
  (consolidate duplicated TICKERS dicts), WP-DB-BENCHMARKS-
  TABLE (separate indexes from stocks).
  5 files changed, 541 insertions.
  Gates: 8782a6a.

═══════════════════════════════════════════════════════
SESSION 6 — 2026-05-19
═══════════════════════════════════════════════════════

bfbae14 — 2026-05-19 — WP-SIGNAL-MEAN-REVERSION-ZSCORE-V1
  6-combo z-score mean-reversion grid sweep across 10 blue
  chips with 60/40 holdout at 2024-07-01. New
  mean_reversion_zscore_signal in src/backtest/signals.py
  (stateful mean-touch exit: enter when z < -threshold,
  exit when z >= 0; population stdev, ddof=0). New
  scripts/backtest_mean_reversion_grid.py. Engine reuse
  via existing signal_series protocol.

  Headline: REFUTED. 6/6 combos negative test alpha vs
  B&H. Winner (window=30, threshold=2.0) aggregate train
  Sharpe 0.422; test alpha -18.30% (B&H test Sharpe 0.654).
  Entry-count multiplier 5.25x vs V2 MA crossover winner
  — churn-cost mechanism reaffirmed across signal families.
  Two spec amendments documented in commit body: V2
  train-mask convention (`<=`) for direct comparability;
  winner selection on aggregate TRAIN Sharpe (not test, to
  avoid leakage).
  Gates: 283112f.

fe9100e — 2026-05-19 — WP-INFRA-INTRADAY-FILTER
  Defensive volume<=0 row filter added to
  scripts/fetch_yfinance.py and
  scripts/backfill_historical.py between existing NaN drop
  and Supabase upsert. Drops rows where volume is None,
  NaN, or <= 0; logs per-ticker drop counts (suppressed
  when zero). Hardens against yfinance returning volume==0
  with all other OHLC columns populated.

  Production probe found 7 such rows on existing blue
  chips (ANZ.AX x3, CSL.AX x2, NAB.AX x1, RIO.AX x1) —
  banked as WP-INFRA-PRICES-ZEROVOL-CLEANUP.
  Gates: bfbae14.

4b9037b — 2026-05-19 — WP-INFRA-SCHEMA-DRIFT-SCRIPT
  Created scripts/verify_schema.py (206 lines). Reads
  expected schema (hardcoded with comment pointer to
  migrations/001_initial_schema.sql) and queries Supabase
  PostgREST OpenAPI (GET /rest/v1/ with
  Accept: application/openapi+json) for deployed state.
  Diffs per-table, per-column: missing/extra
  tables/columns, type mismatches, NOT NULL mismatches,
  PK mismatches. ASCII-only stdout; exit 0 on SCHEMA CLEAN,
  1 on drift.

  Production run at fe9100e: SCHEMA CLEAN (25/25 columns
  across stocks, prices, signals).

  Notable Phase A finding: PostgREST does not expose
  system schemas (information_schema). Canonical
  introspection path is the OpenAPI endpoint, which stays
  inside the locked "supabase-py over HTTPS only" decision
  (no native PG driver, no RPC). Deferred to a future v2
  WP: defaults, indexes, triggers, CHECK constraints, FK
  targets, numeric precision/scale.

  T3 exemplified halt-and-resume discipline during Phase B
  when T2's mid-flight uncommitted mods polluted the
  shared working tree; refused to touch T2's work; waited
  for orchestrator-authorised resume.
  Gates: fe9100e.

1e724b2 — 2026-05-19 — WP-INFRA-UNIVERSE-CENTRALIZE
  Consolidated TICKERS dict (previously duplicated across
  scripts/fetch_yfinance.py and
  scripts/backfill_historical.py) into
  src/data/universe.py (62 lines). Both scripts now import
  from the central module. BLUE_CHIPS_ASX (10 tickers,
  alphabetical) and BENCHMARKS (["^AXJO"]) lists added for
  downstream consumers needing separated views. TICKERS
  preserves flat dict[str, str] shape and CBA-first
  insertion order from the original inline dicts.

  Net: 27 lines of duplication removed; single source of
  truth established for the universe.
  Gates: 4b9037b.

2146b34 — 2026-05-19 — WP-DATA-UNIVERSE-ASX200
  Universe expanded 10 blue chips -> 200 ASX 200
  constituents + ^AXJO benchmark. ASX_200 list (sorted
  alphabetically, 200 entries) added to
  src/data/universe.py; TICKERS extended with 190 new
  entries (10 entries overlapping with blue chips
  preserved byte-unchanged).

  Source: Wikipedia S&P/ASX 200 constituents page
  (https://en.wikipedia.org/wiki/S%26P/ASX_200), parsed
  via bs4 direct table extraction. Snapshot
  2026-05-19T06:56+10:00. Chosen over Finnhub (key empty),
  yfinance .components (method nonexistent), ASX official
  feed (market-cap proxy only), and STW ETF holdings (no
  public endpoint).

  scripts/seed_asx200.py (one-shot, idempotent via
  on_conflict) fetched historical OHLCV via inline
  per-ticker pattern (2nd consumer of the pattern;
  consolidation banked as
  WP-INFRA-YFUTILS-PERTICKER-INGEST for 3rd-consumer
  trigger). 189/190 tickers succeeded in 218.8s
  wall-clock; 1 failure: XYX.AX (Block, Inc.) — yfinance
  returned 404, likely Yahoo ticker-mapping issue (banked
  WP-DATA-XYX-RECOVER). XYX.AX has an orphan stocks row
  without prices.

  Pre/post: stocks 11 -> 201 (+190), prices
  13,910 -> 239,694 (+225,784).
  Gates: 1e724b2.

  (Reconcile commits not logged per established convention.)

═══════════════════════════════════════════════════════
SESSION 7 — 2026-05-19 / 2026-05-23
═══════════════════════════════════════════════════════

dfe17de — 2026-05-22 — WP-INFRA-CLAUDEMD-CONCURRENT-STATUS-ASSERTION
  Amended CLAUDE.md "Commit discipline" Rules block (+13
  lines) to encode the two-mode status-assertion pattern
  locked at the session-6 reconcile (4790939). SOLO-TERMINAL
  (default): git status -s MUST show EXACTLY the declared
  file list. CONCURRENT (declared in WP GATE): status MUST
  INCLUDE the declared list; other unstaged files tolerated
  iff in-flight artifacts of another terminal's WP, guarded
  by (a) explicit-pathspec git add and (b) step-5
  git diff --cached --name-only showing EXACTLY the declared
  list. Concurrency mode declared upfront in WP GATE;
  absence of declaration = SOLO.

  Spec-deviation note: T1 shipped without the orchestrator-
  authorised parenthetical "(plus any whitelist-gated paths
  per the rule above)" on the solo-mode bullet. Banked into
  WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2 for fix.
  Gates: 4790939.

c823e20 — 2026-05-23 — WP-SIGNAL-MEAN-REVERSION-ZSCORE-V2
  Re-run of V1 (bfbae14) spec verbatim on the ASX 200
  universe filtered to mature listings -- universe is the
  only variable changed from V1. Same signal function
  (mean_reversion_zscore_signal, population stdev ddof=0,
  mean-touch exit z >= 0), same engine, same 6-combo grid,
  same 60/40 holdout at 2024-07-01 (train_mask <=,
  inclusive), same long-only V1 constraint, same $10k/ticker,
  same costs (0.1% brokerage/side + $0.01/share slippage),
  same winner-selection (aggregate TRAIN Sharpe, tiebreak
  avg train total return; test metrics reported as held-out
  validation, never optimised over). New
  scripts/backtest_mean_reversion_grid_asx200.py.

  Universe filter: src.data.universe.ASX_200 (200) ->
  survivors with >= 504 rows where trade_date <= 2024-07-01.
  Result N=185. Excluded 15: 8 zero-row orphans (AAI, DNL,
  GGP, L1G, RYM, SGH, VGN, XYX) + 7 partial-history (FRW 42,
  CSC 59, NEM 169, ASK 232, RDX 253, LNW 271, LSF 394).

  Headline: REFUTED. All 6 combos negative alpha vs B&H on
  BOTH train and test; test-window alpha range -34.58% to
  -40.13%. Winner (window=50, threshold=2.0, aggregate train
  Sharpe 0.349): test Sharpe 0.269 vs B&H 0.467 (delta
  -0.198), test alpha -35.89%, beats B&H on 57/185 (30.8%)
  test tickers. Highest-train-Sharpe combo is the lowest-
  entry combo (~6.4 entries/ticker train) -- a cash-drag
  Sharpe artefact during trending markets, not edge.

  V-walk: CBA.AX winner combo, first 3 entries, script z vs
  manual arithmetic max delta 2.87e-13 (PASS criterion
  <1e-8). Wall-clock 5.6 min vs 5.1 min estimate. Survivor
  count exact match to Phase A (185 vs 185).

  Family chapter closed cross-universe (narrow V1 bfbae14,
  broad V2 c823e20). Engine + signals.py + universe.py +
  yfinance_utils.py consumed unchanged. No env mutations;
  supabase-py + stock certifi 2026.4.22 reached Supabase
  with Norton TLS interception OFF (verified 2026-05-23
  08:15).

  Spec deviations logged in commit body: (1) .mr_v2_run.log
  matched pre-existing .gitignore "*.log" rule so never
  showed as untracked -- log captured on disk (10,482
  bytes), verified, rm'd pre-push; safer than asserted. (2)
  Long commit body required $TEMP/<unique>.txt -> mv to
  .commit-msg.tmp pattern (bash heredoc parser limit). Both
  banked into WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2.
  Gates: dfe17de.

  (Reconcile commits not logged per established convention.)

═══════════════════════════════════════════════════════
SESSION 8 — 2026-05-31 / 2026-06-01
═══════════════════════════════════════════════════════

a63cb38 — 2026-05-31 — WP-RECONCILE-SESSION-7-CLOSE (T4, resumed)
  Late-landed session-7 reconcile. Original Phase A landed
  2026-05-23 in session-7 chat but Phase B was never
  authorised; HEAD sat at c823e20 with all four state files
  at session-6-close levels until WP-META-SESSION7-CLOSE-
  AUDIT (T4, session-8 opener, no commit) caught the gap.
  Resumed reconcile refreshed the 4 state files to session-
  7-close baseline. Surfaced two orchestrator-side state-
  drift modes: Phase-B-authorization gap (the primary
  reason for the late landing) and banked-state drift
  (WP-INFRA-REQUIREMENTS-PIN missing from _ideas.md despite
  being listed as carry-forward in the session-8 OPEN
  handover). Both calibrations locked in _ideas.md NOTES/
  CALIBRATION + _timeline.md SESSION 7 PROCESS LEARNINGS.
  Gates: 4790939.

80f9993 — 2026-05-31 — WP-SIGNAL-MOMENTUM-V1 (T2)
  Per-ticker absolute lookback momentum, Jegadeesh-Titman
  skip-1-month convention, 3-combo grid (N in {63, 126,
  252}, skip=21, threshold=0 strict), 60/40 train/test
  holdout at 2024-07-01, same 185-survivor ASX 200 universe
  as MR V2 (c823e20). Same engine, same long-only, same
  $10k/ticker, same costs. New
  scripts/backtest_momentum_grid_asx200.py.

  Signal spec: lookback_return = (close[t-skip] /
  close[t-skip-N]) - 1; signal=1 if return >0 strict, else
  0; NaN warm-up for first (skip + N) trade days. Stateless
  per-day; held-position semantics via engine
  (consecutive 1s = continuous hold).

  Headline: REFUTED. All 3 combos negative test alpha vs
  B&H (range -13.50% to -23.83%). Winner (N=252, aggregate
  train Sharpe +0.168 -- only combo with positive train
  Sharpe): test Sharpe 0.289 vs B&H 0.467 (delta -0.178),
  test alpha -13.50%, beats B&H on 50/185 (27.0%) test
  tickers. Shorter lookbacks (N=63, N=126) have negative
  TRAIN Sharpe (-0.127, -0.117) -- decisively worse on
  train than the winner.

  V-walk: CBA.AX winner combo, first 3 train-window 0->1
  transitions, script lookback_return vs manual closes
  arithmetic max delta 0.00e+00 (PASS criterion <1e-8).
  Signal arithmetic exact across two independent code
  paths.

  Critical confound acknowledged: V1 tests the WEAKEST
  momentum formulation -- per-ticker binary timing,
  unranked, unnormalised. Refutation does NOT close the
  cross-sectional door. Banked WP-SIGNAL-MOMENTUM-CROSS-
  SECTIONAL-V1 (Jegadeesh-Titman canonical: top-decile-by-
  12mo-return holding equal-weight, backtested as one
  portfolio not 185 timing signals). Also banked
  WP-SIGNAL-MOMENTUM-LONGSHORT-V1 (same per-ticker spec,
  constraint flipped) gated on WP-INFRA-ENGINE-SHORTSIDE.

  Session-cumulative refutation count: 6 consecutive long-
  only signal-family refutations across 3 distinct
  mechanic families (MA crossover V1/V2/V3 + MR z-score
  V1/V2 + momentum absolute-lookback V1). Long-only
  constraint = prime suspect. Engine + signals.py +
  universe.py + yfinance_utils.py consumed unchanged.
  Gates: a63cb38.

8ba9416 — 2026-06-01 — WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2 (T1)
  Four CLAUDE.md amendments folding session-7 process
  learnings into the working-model document (+39 lines,
  178 -> 217). All Rules-block or Environment-section
  additions; no existing rule modified semantically.

  (a) Solo-mode strict-literal parenthetical: dfe17de's
  SOLO-TERMINAL bullet asserted git status -s MUST show
  EXACTLY the declared file list; the pre-existing
  whitelist-gate rule (e.g. _timeline.md when WP isn't a
  reconcile) was a silent exception the wording
  contradicted. T1 silently shipped dfe17de without the
  orchestrator-authorised parenthetical "(plus any
  whitelist-gated paths per the rule above)"; this
  amendment lands it. +1 line.

  (b) *.log gitignore convention: surfaced c823e20.
  Artefacts matching existing gitignore patterns
  (.mr_v2_run.log matching .gitignore:32 *.log) are
  silently absent from git status -s. Safe but
  non-obvious. New "Why <X>" thematic bullet in Commit-
  discipline Rules block. +8 lines.

  (c) $TEMP/<unique>.txt -> mv .commit-msg.tmp pattern for
  long commit bodies: surfaced c823e20, reused a63cb38 +
  80f9993. Bash heredocs in Bash tool memory-bound at
  ~500 chars; bodies over that truncate. Pattern: write
  body to $TEMP outside repo, AFTER pre-stage status
  assertion + git add + diff --cached, mv to
  .commit-msg.tmp, commit -F + rm. .commit-msg.tmp is NOT
  currently gitignored so mv MUST land post-stage
  (banked WP-INFRA-GITIGNORE-COMMIT-MSG-TMP to eliminate
  the ordering constraint). +15 lines.

  (d) AV TLS interception as supabase-py SSL failure mode:
  surfaced WP-INFRA-SSL-TRUSTSTORE Phase A (session 7,
  2026-05-19, no commit); resolved off-terminal 2026-05-23
  by disabling Norton SSL scanning. New Environment-section
  item 9: diagnostic (leaf cert issuer reading "Norton
  Web/Mail Shield Root" or similar AV-product org name
  indicates interception), fix (OS-side AV toggle),
  explicit anti-fixes (don't pin certifi; don't install
  truststore -- exposes SUPABASE_SERVICE_ROLE_KEY plaintext
  to AV). Folds in banked WP-INFRA-CLAUDEMD-SSL-LESSON.
  +15 lines.

  Dogfooded amendment (c) in this commit: body ~2200 chars
  (above the heredoc memory-bound); written to
  $TEMP/claudemd_v2_body.txt outside the repo so the
  working tree stayed at exactly ` M CLAUDE.md` during the
  pre-stage SOLO strict-literal assertion; then mv to
  .commit-msg.tmp AFTER staged-set verification, commit -F,
  rm. Convention validates itself under its own
  documentation.

  Banks: WP-INFRA-GITIGNORE-COMMIT-MSG-TMP (add
  .commit-msg.tmp to .gitignore; eliminates post-stage-mv
  ordering constraint).
  Gates: dfe17de (a baseline), c823e20 (b + c surfacing),
  a63cb38 (c reuse), 80f9993 (c reuse).

  (Reconcile commits not logged per established convention.)
