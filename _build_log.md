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
