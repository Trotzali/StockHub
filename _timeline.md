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
