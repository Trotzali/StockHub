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

HEAD at SESSION 2 close: this commit (see
`git log -1 --oneline`). Improvement over session-1
placeholder pattern — reconcile commits don't need to
self-reference; git log is authoritative. No next-session-
open hygiene patch needed.

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
