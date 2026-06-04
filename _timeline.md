# _timeline.md

Append-only session log. Each session: date, what was opened, what
shipped, what was banked. Reconciled at session close.

═══════════════════════════════════════════════════════
SESSION 1 — 2026-05-15 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Fresh project. No prior state. Handover doc received.
  Working model rules locked (Section 1-15 of working-model.md).
  Anchors confirmed:
    - Project: StockHub
    - Repo: https://github.com/Trotzali/StockHub (empty, public, just created)
    - Working dir: C:\Users\admin\Projects\StockHub
    - Branch: master
    - Shell: PowerShell on Windows 11
    - Python 3.12 (use `python`, not python3)
    - gh CLI 2.87.2 available
    - git identity already set (Troy / admin@tjkcivil.com.au)

T1 BOOTSTRAP (WP-BOOTSTRAP-REPO-INIT)
  Phase A: environment inventory — no writes. Confirmed clean slate.
  Phase B: mkdir working dir, git init, remote add, .gitignore, README,
            four state files seeded, first commit, push to master.
  Result: shipped as 73b2c8d (root commit on master), pushed to
  origin/master, working tree clean.

BANKED THIS SESSION
  WP-CRYPTO-SOCIAL-SIGNAL-ENGINE (in _ideas.md)
  WP-EXPAND-US-MARKETS (in _ideas.md)
  WP-OPTIONS-STRATEGIES (in _ideas.md)
  WP-EXEC-BROKER-API-INTEGRATION (in _ideas.md)
  WP-FRONTEND-NEXTJS-MIGRATION (in _ideas.md)

DECISIONS LOCKED
  - ASX 200 only for validation phase; crypto/shitcoins is a second
    section in the same app, deferred until ASX engine is validated.
  - Branch: master (not main).
  - One hypothesis at a time. No mixing equities and crypto during
    validation.

═══════════════════════════════════════════════════════
CALIBRATION NOTES (SESSION 1)
═══════════════════════════════════════════════════════

Discovered during T1 bootstrap, banked permanently in
_project_state.md → ENVIRONMENT NOTES:

- PS 5.1 mangles multi -m chains with backtick continuation and empty
  -m "" separators. Use `git commit -F <tempfile>` and remove the
  tempfile before push verification.
- PS 5.1 `Set-Content -Encoding utf8` writes UTF-8 WITH BOM. Use the
  Write tool or [System.IO.File]::WriteAllText with a no-BOM
  UTF8Encoding.
- LF→CRLF warnings on `git add` are benign (Windows core.autocrlf).
  Ignore.
- `git push` under PS 5.1 with 2>&1 emits cosmetic NativeCommandError
  text; exit code is authoritative.

═══════════════════════════════════════════════════════
T1 RECONCILE-POST-BOOTSTRAP (d57dbcd)
═══════════════════════════════════════════════════════
Backfilled 73b2c8d into _build_log.md and _timeline.md. Closed
WP-BOOTSTRAP-REPO-INIT in _project_state.md and advanced CURRENT WP
to WP-DB-SCHEMA-INIT. Banked four PS 5.1 gotchas as permanent
ENVIRONMENT NOTES in _project_state.md. Banked WP-DB-MIGRATIONS-CLI
in _ideas.md.

═══════════════════════════════════════════════════════
T1 WP-DB-SCHEMA-INIT (Part A: scaffold)
═══════════════════════════════════════════════════════
No commit. Wrote:
  - migrations/001_initial_schema.sql (93 lines)
  - .env.example (17 lines, committed template)
  - .env (12 lines, gitignored skeleton)
Verified gitignore correctly masks .env via *.env glob (line 16 of
.gitignore), not literal .env (line 11) — functionally identical,
good defensive default.

USER MANUAL STEPS
  - Created Supabase project: stockhub (Sydney / ap-southeast-2, free tier)
  - Populated .env with: SUPABASE_URL, SUPABASE_ANON_KEY,
    SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_HOST, SUPABASE_DB_PASSWORD
    (DB port/name/user already at defaults)
  - Applied migration via Supabase SQL Editor with "Run and enable RLS"
  - Verified three tables present: prices, signals, stocks

═══════════════════════════════════════════════════════
T1 WP-DB-SCHEMA-INIT (Part B: commit) — a1d825d
═══════════════════════════════════════════════════════
AMENDMENT applied (per Section 14 of working-model.md): migration file
edited to add ALTER TABLE ENABLE ROW LEVEL SECURITY for all three
tables. Commits file = DB state. WP-DB-RLS-POLICIES banked in
_ideas.md as the source spec for revision when we need policies.

Staged: .env.example, migrations/001_initial_schema.sql, _ideas.md.
.env confirmed absent from all stage/diff output. Push: master->master,
exit 0.

═══════════════════════════════════════════════════════
SESSION 1 CLOSE — 2026-05-16 AEST
═══════════════════════════════════════════════════════

SHIPPED (4 commits):
  73b2c8d — WP-BOOTSTRAP-REPO-INIT
  d57dbcd — WP-RECONCILE-POST-BOOTSTRAP
  a1d825d — WP-DB-SCHEMA-INIT (with RLS amendment)
  16ebfcb — WP-RECONCILE-SESSION-1-CLOSE

HEAD at close: 16ebfcb

DECISIONS LOCKED THIS SESSION:
  - Master branch (not main)
  - Working dir: C:\Users\admin\Projects\StockHub
  - Supabase free tier in Sydney region, project name "stockhub"
  - .env structure: 5 required Supabase keys + 2 deferred (Finnhub, Alpha Vantage)
  - Schema design: stocks/prices/signals with FK + indexes + updated_at trigger
  - RLS enabled with no policies; service_role bypass is the access pattern
  - Migrations applied via Supabase SQL Editor; CLI tooling deferred
    (WP-DB-MIGRATIONS-CLI banked)

TERMINAL STATES AT CLOSE:
  T1 — idle, on a clean tree at HEAD
  T2-T5 — never activated this session

IMMEDIATE QUEUE (NEXT SESSION):
  WP-DEV-ENV-SETUP — Python venv, requirements.txt with pinned versions
                     (yfinance, supabase, psycopg2-binary, python-dotenv,
                     pandas, streamlit, plotly), .env loader, connection
                     smoke test that queries the three tables and confirms
                     end-to-end Python → .env → Supabase → schema works.

PROCESS NOTES:
  - Bootstrap to schema took 4 commits across one chat. Acceptable for
    session 1 but a session of bigger feature work probably wants to
    stay leaner per commit.
  - PS 5.1 calibration banked permanently in _project_state.md →
    ENVIRONMENT NOTES; future CC prompts inherit.
  - Working model section 14 amendment protocol exercised cleanly for
    the RLS issue. Pattern: source spec banked in _ideas.md, deviation
    documented in commit message + migration file comment.

═══════════════════════════════════════════════════════
SESSION 1 — EXTENSION PAST MILESTONE RECONCILE
═══════════════════════════════════════════════════════

Note: prior reconcile at 16ebfcb labeled itself "SESSION 1 CLOSE"
but session continued in same chat. Treating 16ebfcb as mid-session
milestone; this commit is the actual SESSION 1 close.

═══════════════════════════════════════════════════════
T1 WP-DEV-ENV-SETUP (1ed6d8b) — four rounds
═══════════════════════════════════════════════════════

Round 1: psycopg2-binary 2.9.12 install
  Silent sdist fallback. No pg_config on this box. Build fail. STOP.

Round 2: psycopg2-binary==2.9.10 retry
  Same sdist fallback (no win wheel at that version either). STOP.

Round 3: psycopg[binary] (psycopg3) + --only-binary :all:
  ResolutionImpossible. --only-binary :all: surfaced the real error:
  pip walked psycopg-binary 3.0–3.3.4 looking for win_arm64 wheels
  and found none. ROOT CAUSE: this is a Windows-on-ARM64 (Snapdragon)
  box. PyPI has no PG-driver wheels for win_arm64 at any version.
  Architectural pivot: dropped native PG driver, switched to
  supabase-py over HTTPS/REST.

Round 4: backend+UI stack install
  Exit 0 — but streamlit silently resolved to 0.8 (2018 release).
  T1 correctly diagnosed as semantic-failure-disguised-as-success
  (resolver back-walked streamlit ~7 years to escape pyarrow's
  win_arm64 wheel gap). Refused to commit a known landmine. STOP.

Final round: backend-only 4-package stack
  python-dotenv 1.2.2, supabase 2.25.1, pandas 3.0.3, yfinance 1.3.0.
  All current-stable. Smoke PASSed pre- and post-commit. Shipped as
  1ed6d8b.

═══════════════════════════════════════════════════════
SESSION 1 ACTUAL CLOSE — 2026-05-16 AEST
═══════════════════════════════════════════════════════

SHIPPED (6 commits):
  73b2c8d — WP-BOOTSTRAP-REPO-INIT
  d57dbcd — WP-RECONCILE-POST-BOOTSTRAP
  a1d825d — WP-DB-SCHEMA-INIT (with RLS amendment)
  16ebfcb — WP-RECONCILE-MILESTONE (mid-session, premature "session close" name)
  1ed6d8b — WP-DEV-ENV-SETUP (after four-round ARM64 odyssey)
  401c938 — WP-RECONCILE-SESSION-1-CLOSE (this commit)

HEAD at actual close: 401c938

Note: the two placeholder slots above were patched to 401c938 by the
SESSION 2 open hygiene step (WP-HYGIENE-TIMELINE-SHA-BACKFILL —
same pattern as the 16ebfcb patch earlier in session 1; reconcile
can't self-reference its own SHA).

DECISIONS LOCKED THIS EXTENSION (additions to prior 16ebfcb block):
  - Architecture: Windows 11 ARM64 (Snapdragon). Permanent ENVIRONMENT NOTE.
  - Pip default: --only-binary :all: always; sanity-check resolved
    versions before pinning.
  - DB driver: supabase-py over HTTPS only. No native PG drivers.
  - UI stack: pyarrow ARM64 wheel gap blocks streamlit. UI WP gated
    on WP-UI-FRONTEND-STACK-ARM64-RESOLUTION.
  - .env keys for supabase-py path: SUPABASE_URL +
    SUPABASE_SERVICE_ROLE_KEY (SUPABASE_DB_* keys retained in .env /
    .env.example for future direct-SQL escape hatch; unused now).

TERMINAL STATES AT CLOSE:
  T1 — idle, on a clean tree at HEAD (heavily exercised session;
       four-round recovery handled cleanly, judgment calls on streamlit
       silent-downgrade were sound)
  T2-T5 — never activated this session

IMMEDIATE QUEUE (NEXT SESSION):
  WP-DATA-YFINANCE-FETCHER — populate stocks + prices tables with
                              ASX 200 daily OHLC via yfinance.

PROCESS NOTES (additions to prior):
  - "What architecture is this box" should be in every new-project
    Phase A bootstrap inventory. Cheap check that would have caught
    the ARM64 reality four rounds earlier.
  - Pip's exit 0 is necessary but not sufficient. Resolver back-walks
    are a real failure mode that --only-binary :all: + manual version
    sanity-checks catches.
  - Banking discipline held: WP-UI-FRONTEND-STACK-ARM64-RESOLUTION and
    WP-DB-DIRECT-SQL-ESCAPE-HATCH captured cleanly without
    scope-creeping the current WP.

═══════════════════════════════════════════════════════
SESSION 2 — 2026-05-16 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Opened with handover from chat 1. T1, T2, T3 activated;
  T4/T5 idle throughout.

WP-HYGIENE-TIMELINE-SHA-BACKFILL (T1, 70e7193)
  Phase A caught third [actual-close-sha] on line 196
  (meta-note, not placeholder). Route 1: patch lines
  192+194 to 401c938, rewrite line 196-198 to past tense.
  Saved a file corruption.

WP-DATA-YFINANCE-FETCHER Phase A recon (T3, no commit)
  9-objective read-only investigation. Surfaced
  auto_adjust=True dropping Adj Close, pandas 3.x
  future_stack requirement, Ticker.history vs yf.download
  tz divergence, no rate-throttling at 20 sequential.
  Findings drove the WP-DATA-YFINANCE-FETCHER design.

WP-INFRA-CLAUDE-MD (T2, 9600a81)
  Phase A gate caught HEAD=401c938; T1's hygiene push
  landed mid-flight, Phase B `git pull --ff-only`
  integrated as fast-forward. First demonstration of the
  parallel-terminal sequencing pattern.

WP-DATA-YFINANCE-FETCHER (T1, 7bacd7f)
  Phase A flagged pins already tighter than proposed;
  NaN-guard gap on close-only drop. Decisions: skip pin
  widening, harden NaN guard across all 6 NOT NULL price
  columns. Dry-run validated: 10 stocks + 70 prices,
  zero dropped.

WP-VERIFY-DEPLOYED-SCHEMA V-walk (T2, no commit)
  Pre-write V-walk, ran parallel to T1 fetcher Phase B.
  25/25 columns present by name, 25/25 types match per
  PostgREST OpenAPI. HEAD-moved-during-walk anomaly
  (9600a81 → 7bacd7f) — second demonstration of the
  parallel-terminal sequencing pattern. VERDICT:
  NO_DRIFT_DETECTED.

PROCESS LEARNINGS
  - Rule 0 Phase A caught two real failures this session:
    third [actual-close-sha] occurrence (file corruption
    avoided) and NaN-guard gap (failed upsert avoided).
  - Parallel-terminal sequencing demonstrated twice;
    `git pull --ff-only` is the safeguard.
  - CLAUDE.md authored mid-session paid for itself within
    the same session.
  - pandas 3.x in venv was a discovery, not a plan.

═══════════════════════════════════════════════════════
SESSION 2 CLOSE — 2026-05-16 AEST
═══════════════════════════════════════════════════════

SHIPPED (3 WPs with commits + this reconcile):
  70e7193 — WP-HYGIENE-TIMELINE-SHA-BACKFILL
  9600a81 — WP-INFRA-CLAUDE-MD
  7bacd7f — WP-DATA-YFINANCE-FETCHER

READ-ONLY WPs (no commit):
  T3 — WP-DATA-YFINANCE-FETCHER Phase A recon
  T2 — WP-VERIFY-DEPLOYED-SCHEMA V-walk

PRODUCTION STATE AT CLOSE:
  Supabase: 10 stocks, 70 prices, 0 signals
  Deployed schema: verified clean via PostgREST OpenAPI
  introspection (NO_DRIFT_DETECTED, 25/25 columns)

HEAD at SESSION 2 close: 5799004 (opportunistic backfill
at session-3 close — the `git log -1 --oneline` wording
was the no-placeholder pattern at write time). Improvement
over session-1 placeholder pattern — reconcile commits
don't need to self-reference; git log is authoritative.
No next-session-open hygiene patch needed.

TERMINAL STATES AT CLOSE:
  T1 — idle (closed hygiene WP + fetcher WP + this reconcile)
  T2 — idle (closed CLAUDE.md WP + read-only V-walk)
  T3 — idle (closed fetcher Phase A recon)
  T4-T5 — held / spare; never activated this session

IMMEDIATE QUEUE (SESSION 3):
  Between WPs. Next Foundation gate is
  WP-DATA-HISTORICAL-BACKFILL (5-year per-ticker load).
  Banked alternatives for session-3 selection in
  _ideas.md: WP-DATA-UNIVERSE-ASX200,
  WP-DATA-STOCKS-METADATA-ENRICHMENT, WP-INFRA-SCHEDULER,
  WP-INFRA-SCHEMA-DRIFT-SCRIPT.

═══════════════════════════════════════════════════════
SESSION 3 — 2026-05-17 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Opened with HEAD = 5799004 (session-2 close).
  Foundation arc continuing — daily fetcher live; need
  shared-helpers refactor + 5y historical backfill before
  signal-hypothesis work begins.

WP-INFRA-SRC-LAYOUT (T1, 4be60e1)
  Pure refactor. Extracted trade_date, df_to_records,
  chunked, upsert_prices, UPSERT_BATCH_SIZE from
  scripts/fetch_yfinance.py into src/data/yfinance_utils.py.
  Import mechanism Phase A decision: sys.path manipulation
  over pyproject.toml editable install — lighter for an
  MVP. V-walked locally post-refactor: 10 stocks + 70
  prices, zero dropped. Shipped cleanly per the atomic
  chain — and yet broken on origin/master. `git status -s`
  showed `?? src/`, which hides which files inside got
  .gitignore'd. The `data/` pattern (unanchored) silently
  excluded src/data/yfinance_utils.py and
  src/data/__init__.py. Discovered post-push; recovered
  in fd8ba2e.

WP-INFRA-GITIGNORE-RESCOPE (T1, fd8ba2e)
  Recovery. Anchored `data/` → `/data/` so the pattern
  matches only at repo root; nested data/ directories
  (like src/data/) are now tracked. Ships the two
  src/data/ files that were missed. V-walked post-fix:
  10 stocks + 70 prices, zero dropped, idempotent rerun
  matches baseline. Methodology lesson banked:
  `git check-ignore -v <new-paths>` belongs in the pre-
  stage assertion chain (empty stdout / exit 1 = PASS).
  Adopted for the very next WP (def6718).

WP-DATA-HISTORICAL-BACKFILL (T2, def6718)
  One-shot scripts/backfill_historical.py. Sequential
  per-ticker yf.Ticker(t).history(period="5y") over the
  10 ASX blue chips. yf.download batch caps at ~60d per
  T3 session-2 recon, so per-ticker is the only viable
  5y path. Consumes existing helpers from
  src/data/yfinance_utils.py — module unchanged.
  IPO/delisting tolerance: WARN if <1000 rows, do not
  fail. 3-attempt exponential backoff.
  V-walked: dry-run 12,650 total (10 × 1265), no WARNs,
  zero NaN drops; full run 12,580 new rows upserted,
  zero dropped; idempotency rerun net 0; post-run SELECT
  confirms 12,650 prices, 10 tickers, per-ticker
  earliest 2021-05-17 uniform, latest 2026-05-15, count
  1265 each. Pre-stage trip wire passed (post-fd8ba2e
  methodology). Banked follow-up:
  WP-INFRA-YFUTILS-EXTEND-RETRY-WRAPPER.

PROCESS LEARNINGS
  - First "shipped broken, recovered same session" arc.
    Local V-walk PASSed (working tree had the files);
    broken state only manifested on a fresh clone of
    origin/master. Calibration: V-walks against the
    working tree don't catch staging-set gaps; only
    `git check-ignore -v <new-paths>` does.
  - Anchored gitignore patterns (/data/) over unanchored
    (data/) for project-specific top-level directories.
    Banked in _ideas.md calibration.
  - Methodology adoption was same-session: fd8ba2e
    banked the lesson, def6718 applied it inline in its
    commit body. CLAUDE.md amendment at session close
    promotes it to a permanent rule.

═══════════════════════════════════════════════════════
SESSION 3 CLOSE — 2026-05-17 AEST
═══════════════════════════════════════════════════════

SHIPPED (3 WPs with commits + this reconcile):
  4be60e1 — WP-INFRA-SRC-LAYOUT (shipped broken)
  fd8ba2e — WP-INFRA-GITIGNORE-RESCOPE (recovery)
  def6718 — WP-DATA-HISTORICAL-BACKFILL

PRODUCTION STATE AT CLOSE:
  Supabase: 10 stocks, 12,650 prices, 0 signals
  Per-ticker price coverage: 2021-05-17 → 2026-05-15
    (1265 rows each — uniform across all 10 blue chips)
  Code: scripts/fetch_yfinance.py and
    scripts/backfill_historical.py both consume
    src/data/yfinance_utils.py via sys.path prelude.

HEAD at SESSION 3 close: 56ddc53 (opportunistic backfill at
session-4 close — the `git log -1 --oneline` wording was the
no-placeholder pattern at write time; same pattern as the
session-2 → session-3 backfill).

TERMINAL STATES AT CLOSE:
  T1 — idle (closed WP-INFRA-SRC-LAYOUT,
              WP-INFRA-GITIGNORE-RESCOPE)
  T2 — idle (closed WP-DATA-HISTORICAL-BACKFILL)
  T3 — idle (closed WP-RECONCILE-SESSION-3-CLOSE)
  T4-T5 — held / spare; never activated this session

IMMEDIATE QUEUE (SESSION 4):
  Between WPs. Foundation arc effectively complete
  (daily fetcher + 5y historical + shared helpers
  module). Next gate is either the signal-hypothesis arc
  (WP-SIGNAL-HYPOTHESIS-V1 / WP-INDICATORS-TA-CORE) or
  the UI shell (gated on
  WP-UI-FRONTEND-STACK-ARM64-RESOLUTION). Banked
  alternatives for session-4 selection in _ideas.md:
  WP-INFRA-YFUTILS-EXTEND-RETRY-WRAPPER,
  WP-DATA-UNIVERSE-ASX200,
  WP-DATA-STOCKS-METADATA-ENRICHMENT,
  WP-INFRA-SCHEDULER, WP-INFRA-SCHEMA-DRIFT-SCRIPT.


═══════════════════════════════════════════════════════
SESSION 4 — 2026-05-18 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Opened with HEAD = 56ddc53 (session-3 close).
  Foundation arc complete. Signal-hypothesis arc opens.
  Backtest design baseline locked in orchestrator chat at
  session-3 close: 50/200 SMA, long-only, hold-until-
  opposite, $10k per ticker, 0.1% brokerage + $0.01
  slippage per side, B&H baseline gross.

WP-SIGNAL-MA-CROSSOVER-V1 (T1, 00e2141)
  Phase A surfaced three operational findings: PostgREST
  1000-row cap requires pagination for full per-ticker
  reads; tickers carry .AX suffix throughout (.AX -> _AX
  for CSV filenames); ASCII-only stdout discipline needed
  to avoid PowerShell cp1252 crashes (probe exit 1 on
  →). Edge-case amendment added: compute_metrics
  graceful on trade_count == 0 (genuinely flat universe).
  Phase B shipped: 10 tickers, 32 trades total, 1066 eval
  days each (warm-up 200 rows excluded). CBA.AX V-walked
  by hand — first golden cross 2022-04-06 confirmed,
  equity-curve start matches MA-200 cutoff 2022-02-25,
  B&H math reconciled to the cent ($19,617.57). Signal as
  written refuted: avg alpha -30 percentage points vs
  B&H; signal beats B&H on 2/10 tickers (CSL.AX +47.6%
  defensive, WES.AX +17.3% noise). Banked follow-ups:
  WP-INFRA-YFUTILS-FETCH-PRICES-PAGINATED (consumer count
  = 1), WP-SIGNAL-MA-CROSSOVER-GRID-V1 (next signal WP),
  ASCII-only-stdout convention promoted to CLAUDE.md.

PROCESS LEARNINGS
  - First end-to-end signal-hypothesis backtest. Engine
    proven; signal refuted as a standalone long-only
    strategy. The refutation is the win — discipline says
    test, not test-until-it-works.
  - Phase A 6-probe investigation paid for itself thrice:
    pagination requirement, ticker-suffix correction, and
    ASCII-only discipline all fed straight into Phase B
    spec. Probe file deleted before report per Rule 0.
  - compute_metrics zero-trade branch was added defensively
    on Phase A's recommendation. Did not fire this run (min
    1 trade) but stays for ASX 200 expansion when a low-
    volatility ticker might genuinely produce 0 crossovers.
  - First WP where the data-driven result drives the next
    WP's design rather than the other way around. Grid
    sweep + regime-filter ideas surface naturally from the
    refutation pattern.

═══════════════════════════════════════════════════════
SESSION 4 CLOSE — 2026-05-18 AEST
═══════════════════════════════════════════════════════

SHIPPED (1 WP with commit + this reconcile):
  00e2141 — WP-SIGNAL-MA-CROSSOVER-V1

PRODUCTION STATE AT CLOSE:
  Supabase: 10 stocks, 12,650 prices, 0 signals (unchanged
  from session-3 close — V1 backtest produces local CSV
  outputs in results/ only, no DB writes).
  Code: scripts/backtest_ma_crossover.py shipped (399
  lines); inline engine + inline paginated-fetch helper.
  Engine + helper extraction trigger fires at second
  consumer (V2 grid sweep, next session).

HEAD at SESSION 4 close: 45d8220 (opportunistic backfill at
session-5 close — the `git log -1 --oneline` wording was the
no-placeholder pattern at write time; same pattern as the
session-2 -> session-3 and session-3 -> session-4 backfills).

TERMINAL STATES AT CLOSE:
  T1 — idle (closed WP-SIGNAL-MA-CROSSOVER-V1 +
              WP-RECONCILE-SESSION-4-CLOSE)
  T2-T5 — idle / spare; not activated this session

IMMEDIATE QUEUE (SESSION 5):
  WP-SIGNAL-MA-CROSSOVER-GRID-V1 — design conversation
  in fresh chat. Parameter grid scope, holdout split,
  optimisation metric, aggregate-only constraint, and
  the engine-extraction decision (V2 IS the second
  consumer of both the inline engine and the paginated-
  fetch helper from 00e2141) settled in that
  conversation before any Phase A fires.


═══════════════════════════════════════════════════════
SESSION 5 — 2026-05-18 / 2026-05-19 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Opened with HEAD = 45d8220 (session-4 close).
  Foundation arc complete. Two signal-family WPs queued
  for this session: GRID-V1 (engine extraction + 5-combo
  parameter sweep with holdout split) and the conditional
  REGIME-FILTER-V1 (banked at session-4 close pending V2
  outcome).

GRID-V1 design conversation
  Locked: 5 (short, long) combos =
  [(10,30), (20,50), (30,100), (50,100), (50,200)];
  60/40 train/test split at 2024-07-01; aggregate-only
  optimisation on train Sharpe with avg_total_return
  tiebreak; per-ticker tuning banned as curve-fitting; V2
  IS the second consumer so extract engine + signal +
  paginated-fetch helper in this WP.

WP-SIGNAL-MA-CROSSOVER-GRID-V1 (T1, 8782a6a)
  Phase A surfaced 4 design questions (Q1: LONG_WINDOW
  coupling in run_backtest; Q2: compute_buy_and_hold not
  yet a function; Q3: signal-function destination; Q4:
  PAGE_SIZE placement). Q1 escalated to engine API change
  signal_fn -> signal_series (caller precomputes; engine
  slices from first non-NaN). Q3 overrode T1's "defer"
  recommendation — V2 is the legitimate second consumer.
  Phase B shipped engine extraction (new src/backtest/
  package + signals.py with ma_crossover_signal moved
  with NaN warm-up contract + compute_buy_and_hold
  extracted), V1 thin-caller refactor (byte-identical CBA
  regression, md5 reconciled), V2 grid script. Headline:
  every combo loses to B&H on train AND test alpha. V2
  winner (50, 200) test alpha -5.16%, test Sharpe 0.635
  — same combo as V1, by design the least-bad of the
  family.

REGIME-FILTER-V1 design conversation
  Locked: regime ticker ^AXJO, regime window MA-200, same
  5 combos and same 60/40 split as V2. One-off
  seed_xjo.py rather than backfill_historical.py rerun
  (scope keeps the WP atomic).

WP-SIGNAL-MA-CROSSOVER-REGIME-FILTER-V1 (T1, bfaa817)
  Phase A confirmed yfinance ^AXJO returns 1265 clean
  rows with tz-aware Sydney + Adj Close == Close + zero
  NaN. Calendar misalignment (1 day at start) + intraday
  volume=0 bar identified; FK-order verified (stocks
  before prices). Phase B seeded 1260 XJO rows (filtered
  volume>0 + date<=2026-05-15; 5 historical zero-volume
  bars dropped), appended regime_above_ma to
  src/backtest/signals.py, ran V3 grid. First Phase B
  attempt CRASHED on int(NaN) inside the engine — XJO's
  5 historical zero-volume gaps land inside held
  positions, breaking the engine's "NaN only at start"
  assumption. Fixed with .ffill() on regime alignment
  (matches live-trader "carry yesterday's regime through
  missing data" semantic). V3 winner shifted to (30, 100)
  but every cell of V2-vs-V3 delta is negative.
  Churn-vs-block analysis: 80 V2 entries -> 160 V3
  entries on (30, 100) universe-wide; 31 blocked + 111
  new. The regime filter doesn't just block, it churns.
  Refuted as an alpha generator; MA crossover family
  chapter closes across 3 refutations (V1 + V2 + V3).

PROCESS LEARNINGS
  - First multi-WP session (excluding bootstrap arcs).
    Two substantive commits + reconcile in one session.
    Atomic-WP discipline held — each WP was its own
    commit with V-walks, no scope creep across WP
    boundaries.
  - Engine extraction with API signature change was the
    right architecture call. The new signal_series shape
    enabled V3's holdout-split-with-precomputed-signal
    pattern that signal_fn couldn't have done cleanly.
  - The .ffill() deviation in V3 is a real new pattern,
    not a bug fix. Mid-series NaN gaps in auxiliary
    indicators are a class problem; banked as calibration
    for future multi-signal composition.
  - V2 test > train Sharpe inversion + V3 churn-
    dominates-block are both real empirical findings
    worth carrying forward. The MA crossover family is
    done as a primary strategy on this universe; its
    defensive properties remain real.

═══════════════════════════════════════════════════════
SESSION 5 CLOSE — 2026-05-19 AEST
═══════════════════════════════════════════════════════

SHIPPED (2 WPs with commits + this reconcile):
  8782a6a — WP-SIGNAL-MA-CROSSOVER-GRID-V1
  bfaa817 — WP-SIGNAL-MA-CROSSOVER-REGIME-FILTER-V1

PRODUCTION STATE AT CLOSE:
  Supabase: 11 stocks (added ^AXJO at bfaa817),
            13,910 prices (12,650 blue-chip + 1,260 XJO),
            0 signals.
  Code: src/backtest/ package live (engine.py +
        signals.py + __init__.py). scripts/ now hosts
        V1 (thin caller), V2 (grid), V3 (regime grid),
        seed_xjo, daily fetcher, historical backfill.
  MA crossover family closed across three refutations
  (00e2141 V1 + 8782a6a V2 + bfaa817 V3). Defensive
  sleeve property real (CSL.AX V1 +47.6% alpha during
  60% B&H drawdown). Family dead as primary alpha
  generator on ASX blue chips 2022-2026.

HEAD at SESSION 5 close: this commit (see
`git log -1 --oneline`). Same no-placeholder pattern;
opportunistic-backfill candidate at session-6 reconcile.

TERMINAL STATES AT CLOSE:
  T1 — idle (closed WP-SIGNAL-MA-CROSSOVER-GRID-V1,
              WP-SIGNAL-MA-CROSSOVER-REGIME-FILTER-V1,
              + WP-RECONCILE-SESSION-5-CLOSE)
  T2-T5 — idle / spare; not activated this session

IMMEDIATE QUEUE (SESSION 6):
  Design conversation in fresh chat on next signal
  family. Options on the table: momentum (price-driven),
  mean reversion (Bollinger / RSI), volatility breakout,
  universe expansion (WP-DATA-UNIVERSE-ASX200).
  Speculative regime-filter variants retired with the
  MA family. Newly banked WPs ready for selection:
  WP-INFRA-INTRADAY-FILTER, WP-INFRA-UNIVERSE-CENTRALIZE,
  WP-DB-BENCHMARKS-TABLE. Plus carryover Foundation
  items (WP-INFRA-YFUTILS-EXTEND-RETRY-WRAPPER,
  WP-UI-STREAMLIT-SHELL gated, WP-UI-MA-OVERLAY).


═══════════════════════════════════════════════════════
SESSION 6 — 2026-05-19 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Opened with HEAD = 283112f (session-5 close). MA
  crossover family closed across 3 refutations. Picked
  mean-reversion (B) over momentum (A) for the next
  signal hypothesis. Flagged universe-thesis tension up
  front: ASX retail-noise edge thesis is weakest on most-
  arbitraged blue chips, but kept the 10-blue-chip
  universe for V2/V3 comparability.

WP-SIGNAL-MEAN-REVERSION-ZSCORE-V1 (T1, bfbae14)
  6-combo z-score grid with mean-touch exit, 60/40
  holdout. Two amendments caught at Phase A: V2-train-
  mask convention (`<=`, not `<`) flagged by T1 for
  direct comparability; winner-on-test-Sharpe error in
  spec (test-set leakage) caught and corrected to V2
  convention (winner on aggregate train Sharpe).
  REFUTED: 6/6 combos negative test alpha vs B&H.
  Winner (30, 2.0) entry-count multiplier 5.25x vs MA
  crossover V2 winner — churn-cost mechanism reaffirmed.
  New mean_reversion_zscore_signal in
  src/backtest/signals.py; new
  scripts/backtest_mean_reversion_grid.py; engine reuse
  via existing signal_series protocol.

WP-INFRA-INTRADAY-FILTER (T2, fe9100e)
  Defensive volume<=0 filter on daily fetch + historical
  backfill. Drops rows where volume is None, NaN, or
  <= 0; logs per-ticker drop counts (suppressed when
  zero). Production probe surfaced 7 existing zero-
  volume rows on blue chips (ANZ.AX x3, CSL.AX x2,
  NAB.AX x1, RIO.AX x1), banked for cleanup as
  WP-INFRA-PRICES-ZEROVOL-CLEANUP. Hardens against
  yfinance returning volume==0 with all other OHLC
  columns populated.

WP-INFRA-SCHEMA-DRIFT-SCRIPT (T3, 4b9037b)
  scripts/verify_schema.py (206 lines) via PostgREST
  OpenAPI introspection (GET /rest/v1/ with
  Accept: application/openapi+json). Diffs per-table,
  per-column: missing/extra tables/columns, type
  mismatches, NOT NULL mismatches, PK mismatches.
  ASCII-only stdout; exit 0 on SCHEMA CLEAN, 1 on drift.
  Production run at fe9100e: SCHEMA CLEAN 25/25 columns.
  Phase A finding: PostgREST does not expose system
  schemas (information_schema); OpenAPI endpoint is the
  canonical introspection path within the "supabase-py
  over HTTPS only" locked decision. Defaults, indexes,
  triggers, CHECK constraints, FK targets, numeric
  precision/scale deferred to v2 (banked
  WP-INFRA-SCHEMA-DRIFT-V2). T3 hit a concurrency
  tripwire during Phase B (T2's mid-flight uncommitted
  mods polluted shared working tree), halted-without-
  touching-T2's-work, resumed cleanly after T2 landed —
  exemplary boundary respect.

MID-SESSION PIVOT
  Four refutations on the same 10-blue-chip universe in
  roughly bull-market windows is enough evidence to vary
  the universe constant. Flipped the session-6 ordering
  (originally signal-first, then universe) to universe-
  expansion-now.

WP-INFRA-UNIVERSE-CENTRALIZE (T1, 1e724b2)
  Consolidated the duplicated TICKERS dict
  (scripts/fetch_yfinance.py +
  scripts/backfill_historical.py) into
  src/data/universe.py. BLUE_CHIPS_ASX (10) +
  BENCHMARKS (["^AXJO"]) lists added for downstream
  separated views; TICKERS preserves flat
  dict[str, str] shape and CBA-first insertion order
  from the original inline dicts. T1 caught an
  architect-side bug in my A5 example (nested-dict shape
  that contradicted the comment intent — actual shape is
  flat dict[str, str]). Net: 27 lines of duplication
  removed.

WP-DATA-UNIVERSE-ASX200 (T2, 2146b34)
  Universe expanded 20×: 10 blue chips -> 200 ASX 200
  constituents + ^AXJO benchmark. Source: Wikipedia
  S&P/ASX 200 page via bs4 direct parse. Finnhub
  (key empty), yfinance .components (method
  nonexistent), ASX feed (market-cap proxy only), and
  STW ETF holdings (no public endpoint) all ruled out
  at Phase A. seed_asx200.py (one-shot, idempotent)
  fetched historical OHLCV per-ticker; 189/190 succeeded
  in 218.8s; 1 failure (XYX.AX / Block, Inc., yfinance
  404, banked WP-DATA-XYX-RECOVER). Pre/post: stocks
  11 -> 201 (+190), prices 13,910 -> 239,694
  (+225,784).

PROCESS LEARNINGS
  - First true concurrent multi-terminal session
    (T1+T2+T3 in parallel across Phase 2; T1+T2 in
    parallel across Phase 3). Five substantive commits
    shipped without merge conflicts.
  - Three architect-side mistakes caught by terminals
    during the session: nested-dict TICKERS spec (T1
    centralise), winner-on-test-Sharpe spec (T1 mean-
    reversion), strict status assertion in concurrent
    contexts (T2-intraday went pragmatic, T3 halted
    strict, T1-centralise mitigation via explicit-
    pathspec). All banked into locked decisions /
    CLAUDE.md amendment WP. Phase A protocol caught what
    it was designed to catch.
  - Universe-thesis tension flagged at session open
    rather than discovered mid-session — paid off in the
    mid-session pivot decision.
  - Churn-cost mechanism is now durable cross-family
    (V3 + MR V1). Promoted from V3-specific calibration
    to standing design constraint for any multi-
    component strategy.
  - Bull-market backdrop is the dominant explanatory
    variable for all 4 session-4/5/6 refutations.
    B&H Sharpe ~0.654 in rising market structurally
    beats long-only signals trading less than 100%
    time-in-market. Empirical, not execution flaw.

═══════════════════════════════════════════════════════
SESSION 6 CLOSE — 2026-05-19 AEST
═══════════════════════════════════════════════════════

SHIPPED (5 WPs with commits + this reconcile):
  bfbae14 — WP-SIGNAL-MEAN-REVERSION-ZSCORE-V1
  fe9100e — WP-INFRA-INTRADAY-FILTER
  4b9037b — WP-INFRA-SCHEMA-DRIFT-SCRIPT
  1e724b2 — WP-INFRA-UNIVERSE-CENTRALIZE
  2146b34 — WP-DATA-UNIVERSE-ASX200

PRODUCTION STATE AT CLOSE:
  Supabase: 201 stocks, 239,694 prices, 0 signals.
  Per-ticker coverage: 200 ASX 200 constituents + ^AXJO
  benchmark; row counts vary by listing date (mature
  listings ~1265 rows; IPOs post-2021 have shorter
  histories; 5 named short-history tickers: CSC.AX 534,
  FRW.AX 124, L1G.AX 155, LNW.AX 747, RYM.AX 148). One
  orphan: XYX.AX has stocks row but 0 prices, banked
  WP-DATA-XYX-RECOVER.
  Code: src/data/universe.py centralises TICKERS,
  BLUE_CHIPS_ASX, BENCHMARKS, ASX_200. Both fetcher
  scripts import from it. scripts/verify_schema.py adds
  PostgREST OpenAPI schema drift introspection.
  Mean-reversion z-score family closed at V1 on blue
  chips. Re-test on ASX 200 banked. MA crossover family
  remains closed (3 refutations from sessions 4-5).
  Momentum and volatility-breakout families still
  untested. Cumulative: 24 commits on master since
  inception.

HEAD at SESSION 6 close: this commit (see
`git log -1 --oneline`). Same no-placeholder pattern as
prior sessions.

TERMINAL STATES AT CLOSE:
  T1 — idle (closed WP-SIGNAL-MEAN-REVERSION-ZSCORE-V1,
              WP-INFRA-UNIVERSE-CENTRALIZE)
  T2 — idle (closed WP-INFRA-INTRADAY-FILTER,
              WP-DATA-UNIVERSE-ASX200)
  T3 — idle (closed WP-INFRA-SCHEMA-DRIFT-SCRIPT)
  T4 — idle (closing WP-RECONCILE-SESSION-6-CLOSE)
  T5 — held / spare; not activated this session

IMMEDIATE QUEUE (SESSION 7):
  Three natural candidates, ordered by information
  yield:
    1. WP-SIGNAL-MEAN-REVERSION-ZSCORE-V2 — re-run V1's
       6-combo grid on the ASX 200 universe. Direct test
       of universe-thesis tension; either MR shows life
       on broader universe or family is decisively dead.
       Either way, high-information result.
    2. WP-SIGNAL-MOMENTUM-V1 — second untested family on
       the ASX 200 universe. Different family +
       different breadth simultaneously; higher variance
       but potentially the first positive finding.
    3. WP-INFRA-CLAUDEMD-CONCURRENT-STATUS-ASSERTION —
       cosmetic; land early to lock the concurrent-
       tolerant assertion pattern before the next
       parallel multi-WP block.
  Recommended ordering: (3) as warm-up, then (1) as
  primary signal-family test, then (2) if (1) is
  decisive and time permits.


═══════════════════════════════════════════════════════
SESSION 7 — 2026-05-19 / 2026-05-23 (AEST)
  [reconcile late-landed session 8, 2026-05-24]
═══════════════════════════════════════════════════════

OPEN
  Opened with HEAD = 4790939 (session-6 close). Two-phase
  plan: WP-INFRA-CLAUDEMD-CONCURRENT-STATUS-ASSERTION as a
  warm-up to lock the concurrent-tolerant status-assertion
  pattern in CLAUDE.md, then WP-SIGNAL-MEAN-REVERSION-
  ZSCORE-V2 as the primary signal-family test (re-run V1 on
  the broad ASX 200 universe). Note: this session's
  reconcile is calendar-dated session 8 (2026-05-24). It
  late-landed after orchestrator-side audit (WP-META-
  SESSION7-CLOSE-AUDIT) caught the missed Phase B
  authorization -- Phase A of the reconcile landed
  2026-05-23, but Phase B was never authorized, so HEAD sat
  at c823e20 with all four state files at session-6-close
  levels until this resumed reconcile.

WP-INFRA-CLAUDEMD-CONCURRENT-STATUS-ASSERTION (T1, dfe17de)
  Amended CLAUDE.md "Commit discipline" Rules block (+13
  lines) to encode the two-mode status-assertion pattern
  locked at the session-6 reconcile (4790939). SOLO-TERMINAL
  (default): git status -s MUST show EXACTLY the declared
  file list. CONCURRENT (declared in WP GATE): status MUST
  INCLUDE the declared list; other unstaged files tolerated
  iff in-flight artifacts of another terminal's WP, guarded
  by explicit-pathspec git add + step-5 diff --cached
  showing EXACTLY the declared list. Absence of declaration
  = SOLO. Spec deviation: T1 shipped without the
  orchestrator-authorized parenthetical "(plus any
  whitelist-gated paths per the rule above)" on the solo
  bullet -- banked into WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-
  V2. Gate: 4790939.

WP-INFRA-CERTIFI-PIN (T1, investigated-unshipped)
  PREMISE REFUTED. T2's Phase A diagnosis attributed
  supabase-py SSL CERTIFICATE_VERIFY_FAILED to certifi
  2026.4.22 missing an intermediate CA Supabase serves. T1
  Phase A confirmed the failure reproducible and proposed a
  pin to certifi 2025.11.12. Phase B install succeeded but
  the verification probe failed with the IDENTICAL SSL error
  -- the pin did NOT fix it. T1 rolled back to 2026.4.22
  per spec FAIL criteria. No commit; HEAD unchanged.
  Conclusion: certifi-version hypothesis refuted; root cause
  broader. Superseded by WP-INFRA-SSL-TRUSTSTORE diagnostic.

WP-INFRA-SSL-TRUSTSTORE (T1, investigated-unshipped)
  CORRECT HALT. The diagnostic Phase A captured the actual
  cert chain Supabase serves on this machine: leaf issuer
  organization = "generated by Norton Antivirus for SSL/TLS
  scanning", CN "Norton Web/Mail Shield Root". Norton AV is
  doing active TLS interception at the network filter layer
  -- terminating upstream TLS, re-signing every cert with
  Norton's private root CA (installed in the Windows cert
  store at Norton install time), and presenting the
  synthetic cert to applications. This explains T2's
  evidence trio exactly (urllib + system store works,
  httpx + certifi.where fails, httpx + system store works).
  Phase A correctly flagged the spec's TLS-intercept halt
  condition; Phase B never fired. No commit; HEAD unchanged.
  Security implication: SUPABASE_SERVICE_ROLE_KEY was
  visible to Norton in plaintext on every supabase-py call
  for an unknown duration -- banked
  WP-INFRA-ROTATE-SERVICE-KEY.

MID-SESSION PIVOT -- Norton-MITM detour and resolution
  The Norton detour cost ~2+ hours on refuted hypotheses
  (certifi pin) before the diagnostic WP found the real
  cause. Resolution was orchestrator-side, off-terminal:
  Troy navigated Norton Settings → Antivirus parent (no
  luck), then Safe Web → Settings tab → HTTPS scanning
  toggle = OFF (other Safe Web toggles left on). T1's
  verification micro-task (2026-05-23 08:15) confirmed
  supabase-py + stock certifi 2026.4.22 reaches Supabase
  clean (1 row from stocks, no SSL error). Two durable
  artefacts: (1) Norton HTTPS interception is now OFF,
  restoring real end-to-end TLS for all HTTPS traffic from
  this box; (2) the security finding is locked in
  calibration + ENVIRONMENT NOTES item 14.

WP-SIGNAL-MEAN-REVERSION-ZSCORE-V2 (T2, c823e20)
  V1 spec (bfbae14) re-run verbatim on the ASX 200 universe
  -- universe the only variable changed. Same signal
  function (population stdev ddof=0, mean-touch exit
  z >= 0), same engine, same 6-combo grid, same 60/40
  holdout at 2024-07-01, same long-only, same $10k/ticker,
  same costs, same winner-selection (aggregate TRAIN
  Sharpe; test reported as held-out). Universe filter
  ASX_200 (200) -> survivors with >= 504 rows pre-
  2024-07-01 = N=185; 15 excluded (8 zero-row orphans + 7
  partial-history). New
  scripts/backtest_mean_reversion_grid_asx200.py. Phase A
  ran urllib-based (pre-Norton-off env blocker); resumed
  and Phase B shipped post-Norton-off. Headline: REFUTED.
  All 6 combos negative alpha on both train and test (test
  range -34.58% to -40.13%). Winner (window=50,
  threshold=2.0) test Sharpe 0.269 vs B&H 0.467, test
  alpha -35.89%, beats B&H on 30.8% of tickers. Highest-
  train-Sharpe combo is the lowest-entry combo -- cash-drag
  Sharpe artefact, not edge. V-walk CBA.AX max delta
  2.87e-13 (PASS <1e-8). Family chapter closed
  cross-universe (narrow V1 bfbae14, broad V2 c823e20).
  Spec deviations logged: .mr_v2_run.log matched pre-
  existing .gitignore *.log (never staged; safer than
  asserted); long commit body required $TEMP/mv pattern.
  Both banked into WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2.
  Gate: dfe17de.

PROCESS LEARNINGS
  - Diagnostic-first discipline catches premise errors
    execution-first misses. The Norton-MITM root cause only
    surfaced because the truststore WP's Phase A was
    designed to capture the actual cert chain before
    acting.
  - Corroborated diagnoses can both be wrong. T2 and T1
    independently blamed certifi; both wrong. Corroboration
    is not validation.
  - Spec deviations must halt-and-report. T1's silent
    omission of the authorized parenthetical at dfe17de is
    the calibration; orchestrator approval IS the spec.
  - .gitignore inspection belongs in Phase A whenever a WP
    produces untracked artifacts (run logs, build outputs).
  - Sharpe-improves-as-entries-drop in a trending bull
    market is the cash-drag artefact; cross-check train
    alpha (if negative across the grid, the Sharpe ordering
    is artefactual).
  - Mean-reversion family closed cross-universe. Vary the
    SIGNAL or the CONSTRAINT next, not just the universe.
  - Norton MITM lesson: if supabase-py SSL fails again,
    check leaf cert issuer for AV product names BEFORE
    pinning. AV-injected issuer = OS-side fix, not
    code-side.
  - Reconcile Phase B authorization gap (session 7 ->
    session 8). Phase A landed clean; Phase B never fired;
    the next session's OPEN was drafted as if the reconcile
    had shipped. Future protocol: session-open handover
    must `git log --oneline -3` to confirm the reconcile
    SHA exists on master before treating a session as
    closed. Caught via WP-META-SESSION7-CLOSE-AUDIT.
  - Banked-state drift (session 7 retrospective). WP-INFRA-
    REQUIREMENTS-PIN was carried as "carry-forward banked"
    in the Session 8 OPEN handover but absent from
    _ideas.md BANKED; corrected in this reconcile. Same
    family of inter-session state-drift as the Phase-B-
    authorization gap above. Future protocol: grep-verify
    every "carry-forward banked" list against _ideas.md
    before treating as source-of-truth.

═══════════════════════════════════════════════════════
SESSION 7 CLOSE — 2026-05-23 AEST
  (reconcile late-landed session 8, 2026-05-24)
═══════════════════════════════════════════════════════

SHIPPED (2 WPs with commits + this reconcile):
  dfe17de — WP-INFRA-CLAUDEMD-CONCURRENT-STATUS-ASSERTION
  c823e20 — WP-SIGNAL-MEAN-REVERSION-ZSCORE-V2

INVESTIGATED, UNSHIPPED (no commits):
  WP-INFRA-CERTIFI-PIN     — premise refuted (certifi pin
                             failed identical SSL error)
  WP-INFRA-SSL-TRUSTSTORE  — Norton AV TLS MITM found;
                             correct halt; superseded by
                             off-terminal Norton-off fix

PRODUCTION STATE AT CLOSE:
  Supabase: 201 stocks, 239,694 prices, 0 signals persisted
  (unchanged from session-6 close -- no data ingestion this
  session; MR V2 computes signals in-backtest, never writes
  to DB). Cumulative: 26 commits on master since inception
  (+dfe17de +c823e20).
  Code: new scripts/backtest_mean_reversion_grid_asx200.py
  (c823e20). CLAUDE.md amended (dfe17de) with the
  concurrent-tolerant status-assertion pattern.
  Environment: Norton AV HTTPS scanning OFF (2026-05-23) --
  supabase-py SSL restored with stock certifi 2026.4.22.
  Mean-reversion z-score family closed CROSS-UNIVERSE (V1
  narrow bfbae14 + V2 broad c823e20). MA crossover family
  remains closed (sessions 4-5). Momentum and volatility-
  breakout families still untested.

HEAD at SESSION 7 close: c823e20 (substantive). This
reconcile commit (see `git log -1 --oneline`) is the
documentation-only close, late-landed in session 8.

TERMINAL STATES AT CLOSE:
  T1 — idle (closed dfe17de; investigated-unshipped
              CERTIFI-PIN + SSL-TRUSTSTORE; verified
              Norton-off env 2026-05-23 08:15)
  T2 — idle (closed c823e20)
  T3 — idle (not activated this session)
  T4 — idle (closing WP-RECONCILE-SESSION-7-CLOSE)
  T5 — held / spare (not activated this session)

IMMEDIATE QUEUE (SESSION 8):
  - Option A (warm-up): WP-INFRA-CLAUDEMD-COMMIT-
    CONVENTIONS-V2 (whitelist parenthetical fix + *.log
    gitignore convention + $TEMP/mv commit-body pattern).
  - Option B (hygiene): WP-INFRA-ROTATE-SERVICE-KEY
    (post-Norton-MITM key rotation).
  - Option C (PRIMARY): WP-SIGNAL-MOMENTUM-V1 — first
    untested family on the broad ASX 200 universe; design
    discussion in chat before Phase A.
  - Stretch: WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1 or
    WP-DATA-ASX200-ORPHANS-V2.


═══════════════════════════════════════════════════════
SESSION 8 — 2026-05-31 / 2026-06-01 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Opened with HEAD = c823e20. The S7 reconcile had never
  landed (Phase A landed 2026-05-23 in the session-7 chat;
  Phase B was never authorised). Session-8 OPEN handover
  drafted as if the reconcile had shipped, but state files
  sat at session-6-close levels and no
  WP-RECONCILE-SESSION-7-CLOSE commit existed on master.
  First task: T4 audit to confirm reconcile state before
  any new substantive work.

WP-META-SESSION7-CLOSE-AUDIT (T4, investigated-unshipped)
  Pure read-only diagnostic. Two probes: git log search
  for RECONCILE-SESSION-7 across all refs (zero matches);
  grep _project_state.md for the session-7 bull-market
  locked decision (found the S6 entry only; no S7 entry,
  no "consecutive" keyword). Verbatim findings reported.
  Composite conclusion: HEAD = c823e20 (S7 substantive
  close), no S7 reconcile commit exists, _project_state.md
  bullet at lines 47-51 references "session-4/5/6
  refutations" only -- consistent with a missed-Phase-B
  reconcile gap. Pre/post status divergence: zero. No
  file writes. No probe scripts. Triggered the next
  action.

WP-RECONCILE-SESSION-7-CLOSE (T4, a63cb38) -- RESUMED
  Resumed S7 reconcile. Phase A re-fired with full edit
  plan (verbatim old_str/new_str per file). Six
  orchestrator decisions locked at firing time (D1-D6):
  the S6 bull-market bullet stays intact + S7 layers on
  top; pipeline-specs fold into the OPEN-WPs narrative
  paragraph; backfill 4790939 at the S6 reconcile
  placeholder; Norton-MITM enters BOTH LOCKED DECISIONS
  and ENVIRONMENT NOTES; commit body + _timeline.md flag
  the late landing; _ideas.md gains an 8th SESSION 7
  calibration note on the Phase-B-authorization gap.
  Phase B applied 8 edits across _project_state.md, 3
  edits across _ideas.md (including Delta-3-added
  WP-INFRA-REQUIREMENTS-PIN once banked-state drift was
  surfaced), 1 append to _build_log.md, 1 append to
  _timeline.md. $TEMP/mv long-body pattern used for the
  3460-char commit body (pre-stage SOLO status clean
  before mv). Push fast-forward c823e20..a63cb38.
  Surfaced two orchestrator-side state-drift modes:
  Phase-B-authorization gap (primary cause of the late
  landing) and banked-state drift (WP-INFRA-REQUIREMENTS-
  PIN absent from _ideas.md despite being listed as
  carry-forward in the S8 OPEN handover). Both locked in
  calibration notes for future protocol guards.

WP-SIGNAL-MOMENTUM-V1 (T2, 80f9993)
  Per-ticker absolute lookback momentum, Jegadeesh-Titman
  skip-1-month convention. 3-combo grid (N in {63, 126,
  252}, skip=21, threshold=0 strict), 60/40 train/test
  holdout at 2024-07-01, same 185-survivor ASX 200
  universe as MR V2 (c823e20). Signal: lookback_return =
  (close[t-skip] / close[t-skip-N]) - 1; signal=1 if >0
  strict, else 0; NaN warm-up for (skip + N) trade days.
  Stateless per-day; engine consumes 0/1 held-position
  series. New scripts/backtest_momentum_grid_asx200.py.
  Engine + signals.py + universe.py + yfinance_utils.py
  unchanged.

  Headline: REFUTED. All 3 combos negative test alpha vs
  B&H (range -13.50% to -23.83%). Winner (N=252) is the
  only combo with positive train Sharpe (+0.168); test
  Sharpe 0.289 vs B&H 0.467 (delta -0.178), test alpha
  -13.50%, beats B&H on 50/185 (27.0%) test tickers.
  Shorter lookbacks (N=63, N=126) decisively worse on
  TRAIN (negative Sharpes). V-walk: CBA.AX winner combo,
  first 3 train transitions, script vs manual arithmetic
  max delta 0.00e+00 (PASS criterion <1e-8).

  Critical confound: V1 tests the WEAKEST momentum
  formulation (per-ticker binary timing, unranked,
  unnormalised). Refutation does NOT close the
  cross-sectional door. Banked WP-SIGNAL-MOMENTUM-CROSS-
  SECTIONAL-V1 (Jegadeesh-Titman canonical: top-decile
  ranked portfolio, equal-weight, monthly rebalance) and
  WP-SIGNAL-MOMENTUM-LONGSHORT-V1 (per-ticker constraint
  flip; gated on WP-INFRA-ENGINE-SHORTSIDE).

  Refutation count update: now 6 consecutive long-only
  signal-family refutations across 3 distinct mechanic
  families. The constant is the long-only constraint.

WP-INFRA-ROTATE-SERVICE-KEY (CLOSED DEFERRED)
  Attempted as session-8 hygiene per S7 banking
  (post-Norton-MITM key rotation, ~10 min estimate).
  Mid-attempt discovery: Supabase legacy HS256-signed
  JWT API keys (the format currently in .env) no longer
  support in-place rotation -- the dashboard's
  "rotate this key" flow is EOL'd. The S7-banked WP
  assumed a trivial dashboard click; reality requires
  JWT-signing-key migration with new-key generation +
  key-swap deployment. Closed deferred. Banked
  successor: WP-INFRA-SUPABASE-NEW-KEY-MIGRATION.
  Implications captured in ENVIRONMENT NOTES item 15.

WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2 (T1, 8ba9416)
  Four CLAUDE.md amendments folding S7 process learnings
  into the working-model doc (+39 lines, 178 -> 217).
  All Rules-block or Environment-section additions; no
  existing rule modified semantically. (a) Solo-mode
  strict-literal parenthetical (+1 line): dfe17de
  shipped without the orchestrator-authorised
  "(plus any whitelist-gated paths per the rule above)";
  this amendment lands it. (b) *.log gitignore
  convention (+8 lines, new "Why <X>" thematic bullet):
  artefacts matching existing gitignore patterns are
  silently absent from git status -s; Phase A must
  check-ignore upfront for any WP producing files that
  may match. (c) $TEMP/<unique>.txt -> mv .commit-msg.tmp
  long-body pattern (+15 lines, new thematic bullet at
  end of Rules block): bash heredocs memory-bound at
  ~500 chars; write body to $TEMP outside repo, AFTER
  pre-stage status assertion + git add + diff --cached,
  mv to .commit-msg.tmp, commit -F + rm. .commit-msg.tmp
  is NOT currently gitignored so the mv MUST land
  post-stage; banked WP-INFRA-GITIGNORE-COMMIT-MSG-TMP
  to eliminate the constraint. (d) AV-TLS-interception
  diagnostic (+15 lines, new Environment-section item 9):
  folds in banked WP-INFRA-CLAUDEMD-SSL-LESSON --
  diagnostic (leaf cert issuer reading AV-product org
  name), fix (OS-side toggle), explicit anti-fixes (no
  certifi pin; no truststore install). Dogfooded
  amendment (c) in this commit: body ~2200 chars,
  written to $TEMP/claudemd_v2_body.txt outside the repo
  so the working tree stayed at exactly ` M CLAUDE.md`
  during the pre-stage SOLO strict-literal assertion;
  then mv to .commit-msg.tmp AFTER staged-set
  verification. Convention validates itself.

PROCESS LEARNINGS
  - Momentum absolute-lookback per-ticker timing variant
    refuted. WEAKEST momentum formulation; cross-sectional
    ranked variant (Jegadeesh-Titman canonical) still
    untested. Don't claim family-refutation when only the
    weakest formulation has been tested; bank stronger
    variants explicitly.
  - 6 consecutive long-only refutations across 3 distinct
    mechanic families. Constant is the long-only
    constraint, not the signal mechanic. Next test must
    vary the constraint axis.
  - Cash-drag Sharpe artefact diagnostic durable cross-
    family (MR V2 + Momentum V1). Promote from MR-
    specific to universal long-only-in-trending-market
    property. Cross-check train alpha to falsify.
  - Supabase legacy HS256 JWT in-place rotation EOL'd.
    Discovered when attempting ROTATE-SERVICE-KEY; pivot
    to new-key migration WP. Plan provisioning effort for
    any future Supabase key rotation -- no longer a
    trivial dashboard click.
  - $TEMP/mv long-body pattern self-validates: 8ba9416's
    body used the very pattern it documents. Convention
    is recursive-safe. Banked WP-INFRA-GITIGNORE-COMMIT-
    MSG-TMP to remove the post-stage-mv ordering
    constraint.
  - CLAUDE.md "Why <X>" thematic-not-numerical ordering.
    Append by theme, not by counter -- protects against
    renumbering churn when new themes surface.
  - Carry-forward banked lists in session-open handovers
    are NOT source-of-truth. _ideas.md BANKED is.
    Promoted from S7 calibration to LOCKED DECISION in
    _project_state.md.
  - Engine architecture inflection. 6 of 6 refuted
    signals reused engine.py + signals.py + universe.py
    unmodified -- long-only abstraction proven. Next
    family (long-short) requires first non-trivial engine
    extension (position {-1, 0, +1}, two-sided PnL/costs,
    gross-long/gross-short/net cash accounting). Banked
    WP-INFRA-ENGINE-SHORTSIDE as prerequisite for the
    constraint-axis pivot. First engine-shape change
    since 8782a6a (session 5).

═══════════════════════════════════════════════════════
SESSION 8 CLOSE — 2026-06-01 AEST
═══════════════════════════════════════════════════════

SHIPPED (3 WPs with commits + this reconcile):
  a63cb38 — WP-RECONCILE-SESSION-7-CLOSE (T4, resumed;
            late-landed after S8-opening META audit
            surfaced the Phase B gap)
  80f9993 — WP-SIGNAL-MOMENTUM-V1 (T2)
  8ba9416 — WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2 (T1)

INVESTIGATED, UNSHIPPED (no commits):
  WP-META-SESSION7-CLOSE-AUDIT  — T4 diagnostic only;
                                  surfaced missed S7
                                  Phase B authorization;
                                  triggered a63cb38
                                  resumed reconcile
  WP-INFRA-ROTATE-SERVICE-KEY   — CLOSED DEFERRED;
                                  Supabase legacy HS256
                                  in-place rotation
                                  EOL'd; superseded by
                                  WP-INFRA-SUPABASE-
                                  NEW-KEY-MIGRATION

PRODUCTION STATE AT CLOSE:
  Supabase: 201 stocks, 239,694 prices, 0 signals
  persisted (unchanged from session-6 close -- session 7
  and session 8 were both backtest-only). Cumulative:
  30 commits on master since inception (+a63cb38
  +80f9993 +8ba9416 over session-7's 26, +this
  reconcile).
  Code: new scripts/backtest_momentum_grid_asx200.py
  (80f9993). CLAUDE.md +39 lines (8ba9416) across 4
  amendments codifying S7 process gaps.
  Environment: Norton AV HTTPS scanning OFF (S7),
  verified clean across all S8 commits. Supabase legacy
  HS256 JWT in-place rotation discovered EOL'd;
  WP-INFRA-ROTATE-SERVICE-KEY closed deferred and
  superseded by WP-INFRA-SUPABASE-NEW-KEY-MIGRATION.
  Signal-family scorecard: 3 mechanic families tested
  long-only on ASX 200 (MA crossover, MR z-score,
  momentum absolute-lookback); 6 consecutive
  refutations; common constant = long-only constraint.

HEAD at SESSION 8 close: 8ba9416 (substantive). This
reconcile commit (see `git log -1 --oneline`) is the
documentation close.

TERMINAL STATES AT CLOSE:
  T1 — idle (closed 8ba9416; dogfooded $TEMP/mv
              long-body pattern under its own
              documentation)
  T2 — idle (closed 80f9993)
  T3 — idle (not activated this session)
  T4 — idle (closed WP-META-SESSION7-CLOSE-AUDIT
              diagnostic; closed a63cb38 resumed
              reconcile; closing
              WP-RECONCILE-SESSION-8-CLOSE)
  T5 — held / spare (not activated this session)

IMMEDIATE QUEUE (SESSION 9):
  - Reconcile (this WP) -- mandatory first action,
    landing now.
  - WP-INFRA-GITIGNORE-COMMIT-MSG-TMP -- optional T1
    warm-up; eliminates the post-stage-mv ordering
    constraint for all future long-body commits.
  - WP-INFRA-ENGINE-SHORTSIDE -- agreed prerequisite
    for the constraint-axis pivot. Engine refactor:
    position series {-1, 0, +1}, two-sided PnL,
    brokerage + slippage both sides, gross-long +
    gross-short + net cash accounting. The now-locked
    next move; sizeable WP, must complete before any
    long-short signal test fires.
  - First long-short signal test (WP-SIGNAL-MOMENTUM-
    LONGSHORT-V1 vs WP-SIGNAL-MEAN-REVERSION-LONGSHORT-
    V1) -- TO BE SETTLED IN SESSION-9 STRATEGY
    DISCUSSION. Both gated on WP-INFRA-ENGINE-SHORTSIDE.
    No primary marked; orchestrator decides based on
    the long-only-constraint-vs-signal-mechanic
    question framing.
  - WP-INFRA-SUPABASE-NEW-KEY-MIGRATION -- hygiene
    closeout; rotate the post-Norton-MITM-exposed
    service-role key via the new JWT-signing-key
    migration path (Supabase legacy in-place rotation
    EOL'd).


═══════════════════════════════════════════════════════
SESSION 9 — 2026-06-03 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Opened with HEAD = 60d4181 (S8 reconcile close, the
  documentation close that landed 2026-06-01 after the
  three S8 substantive commits). Session-9 strategy
  discussion settled the long-short ordering: build the
  engine first (WP-INFRA-ENGINE-SHORTSIDE as gated
  prerequisite), then fire the cleaner of the two long-
  short signal tests. MR-LS was chosen as the first
  signal test on the long-only-vs-signal-mechanic
  question on the grounds that MR already had two
  long-only refutations (cross-universe at c823e20) so
  any rescue or worsening from constraint-flip would be
  directly comparable. Two infra prerequisites also
  shipped: WP-INFRA-GITIGNORE-COMMIT-MSG-TMP (relax the
  post-stage-mv ordering from 8ba9416 amendment c) and
  WP-INFRA-REQUIREMENTS-PIN (S7-banked reproducibility
  hole, closed cfc0e06).

WP-INFRA-GITIGNORE-COMMIT-MSG-TMP (T1, 85da176)
  Anchored `/.commit-msg.tmp` entry added to .gitignore
  at repo root. Closes the post-stage-mv ordering
  constraint documented in CLAUDE.md "Why long commit
  bodies use $TEMP/mv" (added by 8ba9416 amendment c).
  Prior reconciles (a63cb38, 60d4181) had to time the mv
  from $TEMP to .commit-msg.tmp AFTER the strict-literal
  SOLO status assertion to avoid the `??` pollution;
  with the anchored gitignore entry the mv may land at
  any point in the chain, or the body can be written
  directly to .commit-msg.tmp without any mv at all.
  Triggered a follow-up CLAUDE.md amendment (line 154-
  160) formalising the relaxation. Tiny WP; .gitignore
  +1 line. Gate: 60d4181.

WP-INFRA-REQUIREMENTS-PIN (T3, cfc0e06)
  Split dependency manifest into requirements.txt (6
  top-level pins: python-dotenv, supabase, pandas,
  yfinance, beautifulsoup4 + 1 other; bs4 made explicit
  after being an implicit yfinance transitive that
  seed_asx200.py started consuming directly) and
  requirements.lock (full ARM64 transitive set via
  `pip freeze`). Reproducibility hole banked in S7
  reconcile (resumed S8) now closed; fresh-machine setup
  has a pinned manifest. Lock-file portability note in
  header: NOT portable to x64 Windows without a
  regenerate-on-target-arch step. Verified no install
  drift via pip install --dry-run --only-binary :all:
  against the lock file. Gate: 85da176.

WP-INFRA-ENGINE-SHORTSIDE (T2, 3cd4d0b)
  Extended src/backtest/engine.py from long-only
  ({0, 1}) to long-short ({NaN, -1, 0, +1}) with
  stateful held-position semantics. Spec FROZEN at this
  commit for reuse by all -LONGSHORT signal WPs. Key
  extensions: ternary position series with NaN warm-up
  and stateful held-position (consecutive same-side bars
  = continuous hold; +1 -> -1 = exit-long + enter-short
  on same bar at signal-day close); PnL sign-flipped on
  short leg; symmetric costs (0.1% brokerage + $0.01/
  share slippage both legs every entry/exit); pure-drag
  borrow charged daily on abs short notional (entry-
  inclusive / exit-exclusive day-counting, default
  annualized 0.0 -- tunable per ticker; reverse-MTM at
  exit; the drag IS the daily charge); cash accounting
  splits into gross-long + gross-short + net (reports
  BOTH gross-of-borrow and net-of-borrow metrics).
  V-walk regression: all 6 prior long-only callers (MA
  crossover V1/V2/V3, MR z-score V1/V2, momentum V1)
  re-run -- aggregate delta vs baseline = 0 (byte-
  identical CSV outputs). signal_series protocol
  unchanged for long-only callers. Engine API now
  FROZEN. Gate: cfc0e06.

WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1 (T2, cc2e4c6)
  Re-run of MR z-score family with long-only constraint
  flipped to long-short via the frozen engine. Same
  signal function (extended to long-short: long when
  z < -threshold, short when z > +threshold, exit when
  |z| <= 0), same engine, same 6-combo grid, same 60/40
  holdout at 2024-07-01, same N=185 ASX 200 survivor
  universe as MR V2 (c823e20), same $10k/ticker, same
  symmetric costs both legs, borrow charged via the
  frozen engine's pure-drag model using borrow tiering
  (src/backtest/borrow_tiering.py: median daily $-volume
  terciles via qcut, annualized 1% top / 4% mid / 8%
  bottom liquidity; full-sample classification;
  paginated fetch -- the 1000-row cap workaround applies
  to this new self-fetch consumer too).

  Headline: REFUTED, DECISIVELY WORSE than long-only.
  Winner combo (window=50, threshold=2.0) test net alpha
  -81.16% vs B&H (long-only V2 winner was -35.89%; LS
  made it -45.27 pts worse). Test gross alpha -77.55%;
  net-vs-gross gap ~3.6 pts -- borrow drag is real but
  small relative to the -77.55% gross loss. The short
  leg lost money fighting the trend, not paying borrow.

  KEY REFRAME: lifting the long-only constraint did NOT
  rescue MR -- it HURT it. The long-only refutation was
  the LESS BAD outcome; LS made it dramatically worse
  because the short leg trend-fights in the bull-market
  test window. The binding problem is the short leg's
  directional mismatch with universe-level drift, not
  the constraint itself. The S8 read ("6 consecutive
  long-only refutations -> long-only is the prime
  suspect") was the natural hypothesis but S9 falsifies
  it for MR.

  Implication for the constraint-axis thesis: long-only
  constraint is NOT the universal killer it appeared to
  be. For MR, long-only was actually the LESS BAD
  configuration. Constraint-axis thesis remains OPEN
  for MOMENTUM (where short leg trend-aligns -- sell
  weak-trending tickers in a bull market -- rather than
  trend-fights); long-short momentum is now the cleaner
  test of the long-only-constraint-vs-signal-mechanic
  question.

  MR family CLOSED under per-ticker absolute timing.
  Further MR work must change SIGNAL STRUCTURE (banked
  WP-SIGNAL-MR-CROSSSECTIONAL-V1 long bottom-decile-z /
  short top-decile-z market-neutral; banked
  WP-SIGNAL-MR-REGIME-CONDITIONAL gating L/S on ^AXJO
  200-DMA), not re-run a per-ticker formulation.

  Refutation tally: 7 -- 6 long-only (MA crossover x3,
  MR x2, momentum x1) + 1 long-short (MR-LS V1). The
  long-only hypothesis is nuanced not universal: killer
  for MA/momentum (TBD for momentum-LS), HELPER for MR.
  Gate: 3cd4d0b.

PROCESS LEARNINGS
  - Long-only constraint is NOT the universal killer.
    When N refutations share a constraint, that's a
    HYPOTHESIS not a conclusion; lifting the constraint
    is the falsification test and the result can go
    either way. For MR it went the wrong way.
  - Borrow drag is small relative to directional
    mismatch (3.6 pts vs 77.55 pts gross loss on MR-LS
    V1). Don't over-engineer borrow modelling at signal-
    design stage; tiered 1/4/8 pct defaults sufficient
    until a winner emerges.
  - Constraint-axis thesis remains OPEN for momentum
    (short leg trend-aligns); long-short momentum is the
    cleaner test of the long-only-vs-signal-mechanic
    question. Settled as primary for session 10.
  - Engine spec FROZEN at 3cd4d0b. Future signal
    families plug in via signal_series of {-1, 0, +1}
    (or {0, 1}); no further engine surface-area changes
    expected unless a new structural axis (cross-
    sectional portfolio rebalancing) requires it.
  - Borrow tiering classification choice: full-sample
    (structural cost assumption) over rolling-window
    (return-leakage risk). qcut on median daily $-volume.
  - Concurrent-push pattern locked: fetch after commit;
    FF-if-unmoved or HALT-on-divergence. Do NOT
    `pull --rebase` on shared dirty tree; do NOT
    autostash. Banked WP-INFRA-CLAUDEMD-CONCURRENT-PUSH-
    AMENDMENT to codify.
  - Self-fetch pagination is durable: any new consumer
    > 1000 rows must reuse the existing pagination
    helper. Surfaced during borrow_tiering.py
    implementation (median-ADV needed full per-ticker
    history; hit PostgREST cap on first attempt).
  - Requirements pinning split: 6-pin runtime
    requirements.txt + full ARM64 transitive
    requirements.lock; lock file NOT portable to x64
    without regenerate-on-target-arch.

═══════════════════════════════════════════════════════
SESSION 9 CLOSE — 2026-06-03 AEST
═══════════════════════════════════════════════════════

SHIPPED (4 substantive WPs with commits + this reconcile):
  85da176 — WP-INFRA-GITIGNORE-COMMIT-MSG-TMP (T1)
  cfc0e06 — WP-INFRA-REQUIREMENTS-PIN (T3)
  3cd4d0b — WP-INFRA-ENGINE-SHORTSIDE (T2; engine FROZEN)
  cc2e4c6 — WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1 (T2;
            REFUTED worse than long-only)

PRODUCTION STATE AT CLOSE:
  Supabase: 201 stocks, 239,694 prices, 0 signals
  persisted (unchanged from session-6 close; S7/S8/S9
  all backtest-only). Cumulative: 36 commits on master
  (35 through cc2e4c6 + this reconcile; supersedes the
  handover's drifted 34/30 figures -- git-authoritative).
  Code: src/backtest/engine.py extended long-short and
  FROZEN at 3cd4d0b; src/backtest/borrow_tiering.py new
  (median-ADV terciles 1/4/8 pct); src/backtest/
  signals.py + mean_reversion_zscore_longshort;
  requirements.txt + requirements.lock new (cfc0e06);
  .commit-msg.tmp anchored-gitignored (85da176).
  Engine API FROZEN: signal_series of {-1,0,+1} or
  {0,1}; symmetric costs both legs; pure-drag borrow;
  gross + net reporting.
  Signal-family scorecard: refutation tally 7 (6 long-
  only + 1 long-short). MR family closed cross-
  universe AND cross-constraint under per-ticker
  absolute timing; structural pivots banked. Long-only-
  constraint thesis falsified for MR; remains OPEN for
  momentum (next test).

HEAD at SESSION 9 close: cc2e4c6 (substantive). This
reconcile commit (see `git log -1 --oneline`) is the
documentation close.

TERMINAL STATES AT CLOSE:
  T1 — idle (closed 85da176)
  T2 — idle (closed 3cd4d0b engine FROZEN; closed
              cc2e4c6 MR-LS REFUTED worse than long-only)
  T3 — idle (closed cfc0e06)
  T4 — idle (closing WP-RECONCILE-SESSION-9-CLOSE)
  T5 — held / spare (not activated this session)

IMMEDIATE QUEUE (SESSION 10):
  - Reconcile (this WP) -- mandatory first action,
    landing now.
  - WP-SIGNAL-MOMENTUM-LONGSHORT-V1 (PRIMARY) -- cleaner
    test of the long-only-constraint hypothesis on a
    signal where the short leg trend-aligns. Uses
    frozen engine (3cd4d0b) + borrow tiering.
  - WP-INFRA-SUPABASE-NEW-KEY-MIGRATION -- hygiene
    closeout for the post-Norton-MITM key exposure.
  - WP-INFRA-CLAUDEMD-CONCURRENT-PUSH-AMENDMENT --
    ~10-line CLAUDE.md amendment codifying the
    concurrent-push pattern.
  - Stretch: WP-SIGNAL-MR-CROSSSECTIONAL-V1 OR
    WP-SIGNAL-MR-REGIME-CONDITIONAL (structural MR
    pivots; only if MOMENTUM-LONGSHORT-V1 is decisive
    and time permits).


═══════════════════════════════════════════════════════
SESSION 10 — 2026-06-04 (AEST)
═══════════════════════════════════════════════════════

OPEN
  Opened with HEAD = cc2e4c6 (S9 substantive close;
  reconcile not yet landed -- a Phase A had landed
  2026-06-03 but Phase B was authorized in the morning of
  2026-06-04). Two-action plan: (1) ship the S9 reconcile
  first (af791a2, late-landed by ~12h per the precedent),
  (2) fire the next signal WP. The S9-close primary was
  WP-SIGNAL-MOMENTUM-LONGSHORT-V1; mid-session the
  orchestrator pivoted to WP-SIGNAL-MOMENTUM-CROSS-
  SECTIONAL-V1 instead -- the cross-sectional canonical
  formulation has a stronger academic prior and tests a
  more general question (does the canonical Jegadeesh-
  Titman result translate to ASX-200), and a refutation
  there would have broader implications than the per-
  ticker long-short flip.

WP-RECONCILE-SESSION-9-CLOSE (T4, af791a2, late-landed)
  Late-landed by ~12 hours from S9's substantive commits
  (2026-06-03) to 2026-06-04T07:02 close. Booked per the
  late-landed-reconcile precedent (a63cb38 in S8 by
  weeks). 4 state files refreshed to S9-close baseline:
  6 new LOCKED DECISIONS (long-short engine FROZEN spec,
  borrow tiering, MR family closed cross-constraint,
  long-only-not-universal-killer reframe, concurrent-push
  fix, paginate self-fetches); 4 entries removed from
  _ideas.md BANKED + 3 new added (MR-CROSSSECTIONAL-V1,
  MR-REGIME-CONDITIONAL, CLAUDEMD-CONCURRENT-PUSH-
  AMENDMENT); 8 SESSION 9 calibration notes; cumulative
  recorded 36 commits (35 through cc2e4c6 + the
  reconcile; supersedes the S8-handover's drifted 34/30
  figures -- git-authoritative).

WP-SIGNAL-MOMENTUM-CROSS-SECTIONAL-V1 (T1, 7ea4c08)
  Cross-sectional momentum long-short via the frozen
  engine (3cd4d0b): per-ticker ternary from a daily
  cross-sectional rank, monthly rebalance, fixed K=18/leg,
  equal $10k/name ($180k/leg, $360k gross, dollar-
  neutral), per-ticker tiered borrow (median-ADV terciles
  1/4/8 pct annualised from borrow_tiering.py). J grid
  in {63, 126, 252}; winner J=252 by aggregate TRAIN net
  Sharpe (+0.216); TEST held out per the locked
  guardrail. New: cross-sectional ranking + monthly-rebal
  portfolio plumbing layered on the frozen engine via
  signal_series ternary; no engine-surface-area changes.

  Headline: REFUTED. TEST net total return -2.05%,
  Sharpe -0.174, alpha vs ^AXJO -8.71% (^AXJO +6.65%
  over 2024-07-31..2026-05-18 test window). Borrow drag
  only +0.94% (gross -1.11% vs net -2.05%) -- borrow not
  the driver, same pattern as MR-LS V1 (cc2e4c6).

  Decomposition (winner J=252, TEST): long top-decile
  sleeve +6.87% ~= ^AXJO +6.65% (long leg is BETA, no
  alpha); short bottom-decile sleeve -8.93% (THE KILLER;
  bottom-decile names out-rallied top-decile -- junk-
  rally / momentum-crash signature); sum-of-per-ticker
  long B&H +33.91% (holding the universe crushed the L/S
  by ~36 pts).

  CROSS-TEST FINDING (S9 + S10 together): both long-
  short tests (MR-LS cc2e4c6, momentum-XSEC-LS 7ea4c08)
  died on the SHORT leg in a rising market, borrow
  immaterial both times. Short-side selection is
  structurally loss-making in this regime/universe.
  Survivorship flatters momentum yet it still failed --
  strengthens the refutation.

  CONCLUSION: across 3 signal families x {long-only,
  long-short} x {per-ticker timing, cross-sectional
  ranked} on liquid ASX-200 survivors over a multi-year
  bull, no simple price-based edge beats holding the
  universe. Price-only-on-liquid-ASX thesis CLOSED
  (negative). Cross-sectional momentum family closed.
  Refutation tally 7 -- unchanged in count but
  qualitatively conclusive: the canonical Jegadeesh-
  Titman formulation also fails on this universe.

  V-walks (rank, hold, holdout-split, sum-invariant) all
  PASS; sum-invariant delta 0.0 net+gross -- result
  trustworthy, not an implementation bug.

  Banked: WP-SIGNAL-MOMENTUM-XSEC-QUINTILE-V1 (breadth
  robustness, low prior; in commit body). Strategic fork
  OPEN at commit time, decided at S10 reconcile.

MID-SESSION STRATEGIC PIVOT (decided at S10 reconcile)
  Three options on the table after 7ea4c08:
    (a) Accept the negative result on liquid-ASX price
        signals and pivot to a different DATA TYPE
        (fundamentals/quality) on the SAME universe.
    (b) Pivot to a different UNIVERSE (smaller-cap, less
        institutionally arbitraged) keeping price-based
        signals.
    (c) Both simultaneously (smaller-cap + fundamentals).
  Decision: (a) FIRST, (b) SECOND only if (a) reveals
  edge, NEVER both at once. Rationale: change one
  variable at a time -- changing both simultaneously
  cannot isolate which variable rescued any positive
  result. Plus a parallel defensive trend-overlay sleeve
  (risk-management, not alpha) since it's independent of
  signal-arc choices.

  S9-close primary (WP-SIGNAL-MOMENTUM-LONGSHORT-V1)
  superseded: the cross-sectional momentum refutation
  delivered a more general result (the canonical formulation
  also fails) that obviated the original long-only-
  constraint-vs-signal-mechanic question for momentum.
  Momentum-LS stays banked as a price-based residual but
  deprioritised post-pivot.

ENVIRONMENT NOTE
  Transient node API ECONNREFUSED observed during a
  T-fire window on 2026-06-04. Network connectivity,
  Norton-toggle (still OFF per S7), and proxy
  configuration all verified clean. Resolved on retry
  with no config change. Diagnostic-first discipline
  reinforced: temptation to "try something" was resisted
  in favour of verifying environment first. If recurring,
  surface for deeper investigation; if isolated, file as
  transient infra noise.

PROCESS LEARNINGS
  - Cross-test isolation: two failure modes that share a
    common pattern across families are more durable
    findings than any single-family narrative. S9 + S10
    both isolate short-side directional mismatch as the
    structural killer; borrow drag is incidental in both.
  - Canonical academic formulations also fail. The
    cross-sectional momentum Jegadeesh-Titman result --
    the strongest prior in the US-equities literature --
    does not translate to liquid ASX-200 survivors over
    this bull. Bull-regime-driven cross-sectional flattening
    AND institutional-arbitrage-driven retail-edge erosion
    are both candidate hypotheses; neither is conclusion.
  - Long top-decile sleeve ~= beta. The long leg of a
    rank-based long-short captures no alpha; the ~36-pt
    differential vs sum-of-per-ticker B&H is the
    opportunity cost of selecting 36 of 185 names plus
    the active loss from shorting the wrong 18.
  - Strategic pivot decision framework: change ONE
    variable at a time. After exhausting price signals on
    a fixed universe, change DATA TYPE first (price ->
    fundamentals/quality) on the SAME universe, then
    UNIVERSE second (liquid -> smaller-cap) only if (a)
    reveals edge. The inverse ordering (universe first)
    was considered and rejected on this principle.
  - Defensive overlay framing: risk-management WP, NOT
    alpha. Pays a cash-drag premium for tail-regime
    protection; crash backtests on 2021-2026 sample are
    low-power; bar is regime-independence of protection.
  - Session-close primary recommendations are ranking
    guides, not commitments; the orchestrator retains
    pivot authority based on broader context. S9-close
    primary (MOMENTUM-LONGSHORT-V1) was superseded mid-S10
    by the cross-sectional pivot which delivered a
    broader-implication refutation.
  - Late-landed-reconcile booking convention now has 2
    precedents (a63cb38, af791a2); trigger is calendar-
    date separation, not magnitude of delay.
  - Transient infra noise (ECONNREFUSED): diagnostic-first
    discipline pays off; verify environment before trying
    interventions. Isolated occurrence; no action.

═══════════════════════════════════════════════════════
SESSION 10 CLOSE — 2026-06-04 AEST
═══════════════════════════════════════════════════════

SHIPPED (1 substantive + 1 late-landed reconcile + this reconcile):
  af791a2 — WP-RECONCILE-SESSION-9-CLOSE (T4, late-landed
            by ~12h; booked per late-landed precedent)
  7ea4c08 — WP-SIGNAL-MOMENTUM-CROSS-SECTIONAL-V1 (T1;
            REFUTED; cross-sectional momentum family
            closed; price-only-on-liquid-ASX thesis CLOSED)

PRODUCTION STATE AT CLOSE:
  Supabase: 201 stocks, 239,694 prices, 0 signals
  persisted (unchanged from session-6 close; S7-S10 all
  backtest-only). Cumulative: 38 commits on master (37
  through 7ea4c08 + this reconcile; git-authoritative;
  the S9 drift correction stands).
  Code: src/backtest/engine.py FROZEN at 3cd4d0b;
  cross-sectional ranking + monthly-rebal plumbing for
  7ea4c08 layered on the frozen engine via signal_series
  ternary (no engine-surface-area changes). signals.py:
  ma_crossover, mean_reversion_zscore, momentum_absolute_
  lookback, mean_reversion_zscore_longshort + cross-
  sectional momentum helpers.
  Signal-family scorecard: refutation tally 7
  (qualitatively conclusive). 3 signal families x
  {long-only, long-short} x {per-ticker timing, cross-
  sectional ranked} exhausted on liquid ASX-200 over
  2022-2026 bull. Price-only-on-liquid-ASX thesis CLOSED.
  Cross-test isolation: short-side directional mismatch
  is structural; borrow drag immaterial both long-short
  tests.
  Environment: Norton HTTPS scanning OFF (S7), clean
  across all S10 commits. Transient ECONNREFUSED on
  2026-06-04 resolved on retry with no config change.

HEAD at SESSION 10 close: 7ea4c08 (substantive). This
reconcile commit (see `git log -1 --oneline`) is the
documentation close.

TERMINAL STATES AT CLOSE:
  T1 — idle (closed 7ea4c08 -- cross-sectional momentum
              REFUTED, family closed, price-only-on-
              liquid-ASX thesis CLOSED)
  T2 — idle (not activated this session)
  T3 — idle (not activated this session)
  T4 — idle (closed af791a2 late-landed S9 reconcile;
              closing WP-RECONCILE-SESSION-10-CLOSE)
  T5 — held / spare (not activated this session)

IMMEDIATE QUEUE (SESSION 11):
  - Reconcile (this WP) -- mandatory first action,
    landing now.
  - WP-DATA-FUNDAMENTALS-FEASIBILITY-PROBE (PRIMARY) --
    gating investigation for the fundamentals/quality
    arc per the S10 strategic pivot. Read-only Phase A:
    what fields, what history, what coverage, what
    provisioning is needed.
  - WP-INFRA-SUPABASE-NEW-KEY-MIGRATION -- hygiene
    closeout; pairs naturally with fundamentals
    provisioning if AlphaVantage/Finnhub keys get
    provisioned at the same time.
  - WP-INFRA-CLAUDEMD-CONCURRENT-PUSH-AMENDMENT --
    ~10-line process WP; pairs with a reconcile slot.
  - WP-OVERLAY-TREND-REGIME-CRASH-SLEEVE -- defensive
    sleeve; can run in parallel with the fundamentals
    arc (independent code path; risk-management not
    signal-generation).
  - Stretch: WP-SIGNAL-MOMENTUM-XSEC-QUINTILE-V1
    (breadth robustness on cross-sectional momentum;
    low prior given the cross-test finding).
