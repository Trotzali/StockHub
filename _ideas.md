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

WP-INFRA-PRICES-ZEROVOL-CLEANUP
  One-shot cleanup of the 7 existing volume=0 rows on blue chips
  (ANZ.AX 2022-07-18/19/20; CSL.AX 2021-12-14/15; NAB.AX
  2023-11-15; RIO.AX 2023-11-15). Daily fetcher's new filter
  (fe9100e) prevents reintroduction. Material to backtest
  correctness; small WP, ~15 min. Tiny priority.

WP-INFRA-YFUTILS-PERTICKER-INGEST
  Per-ticker fetch + reshape + volume<=0 filter + upsert pattern
  is now inlined in 2 consumers (backfill_historical.py +
  seed_asx200.py). Consolidate into src/data/yfinance_utils.py
  when a 3rd consumer materialises. Low priority; pattern-
  stabilisation play.

WP-DATA-XYX-RECOVER
  Investigate Yahoo ticker-mapping for Block, Inc.'s ASX listing.
  Wikipedia constituent code is XYX but yfinance returns 404.
  Stocks row exists; prices empty. Likely the listing trades on
  Yahoo under a different symbol (historically SQ2.AX post
  Square/Block rename). Material only if doing Block-specific
  signal work; not blocking universe-level tests. Low priority.

WP-INFRA-SCHEMA-DRIFT-V2
  Extend scripts/verify_schema.py to cover defaults, indexes,
  triggers, CHECK constraints, FK targets, numeric precision/
  scale. v1 (4b9037b) is intentionally presence+format+required+
  PK only; defer expansion until drift in those categories
  surfaces. Low priority.

WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2
  Amalgamate three session-7 process gaps into one CLAUDE.md
  amendment: (a) whitelist-gate parenthetical fix on dfe17de's
  solo-mode bullet ("(plus any whitelist-gated paths per the rule
  above)"), (b) *.log gitignore convention note (don't assert
  untracked-listing for gitignored extensions), (c) $TEMP/<unique>
  -> mv .commit-msg.tmp pattern for commit bodies >~500 chars where
  the bash heredoc parser breaks. ~25 lines. May fold in
  WP-INFRA-CLAUDEMD-SSL-LESSON. Fire as session-8 warm-up.

WP-INFRA-CLAUDEMD-SSL-LESSON
  Add a CLAUDE.md startup-check note documenting AV-TLS-interception
  as a known supabase-py SSL failure mode. Diagnostic recipe (check
  leaf cert issuer org for AV product names -- Norton, Avast, ESET,
  Kaspersky; if a certifi-pin to an older version also fails, suspect
  MITM). Fix recipe (disable AV HTTPS/SSL scanning; do NOT use
  truststore as a workaround -- it silently accepts the MITM). May
  fold into WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2.

WP-INFRA-ROTATE-SERVICE-KEY
  Rotate SUPABASE_SERVICE_ROLE_KEY post-Norton-MITM discovery. The
  key was visible to Norton in plaintext on every supabase-py call
  for an unknown duration (as long as Norton SSL scanning was on).
  No concrete evidence of compromise; Norton is reputable. Hygiene
  rotation is the textbook response to "secret briefly visible to a
  third party". ~10 min: Supabase dashboard action + .env update +
  1-row verification. Fire early session 8.

WP-DATA-ASX200-ORPHANS-V2
  Investigate the 7 zero-row tickers beyond XYX.AX surfaced in MR V2
  Phase A: AAI.AX (Alcoa), DNL.AX (Dyno Nobel), GGP.AX (Greatland),
  L1G.AX (L1 Group), RYM.AX (Ryman), SGH.AX (SGH), VGN.AX (Virgin
  Australia). Session-6 seed (2146b34) reported 189/190 with only
  XYX flagged; reality is 8/190 zero-row. Either silent seed failure
  or post-seed regression. Per-ticker Yahoo-mapping check; recover
  where possible. Low priority; not blocking universe tests at 185
  survivors.

WP-INFRA-REQUIREMENTS-PIN
  Author a proper requirements.txt with pinned versions (separate
  runtime / dev manifests if useful). Project currently has no
  pinned dependency manifest; reproducibility relies on local
  interpreter state + the `--only-binary :all:` pip policy. Treated
  as carry-forward banked in the Session 8 OPEN handover but absent
  from _ideas.md -- orchestrator-side miss surfaced and corrected in
  this reconcile. Low priority while project remains solo +
  single-env.

WP-SIGNAL-MOMENTUM-V1
  Fresh signal family on the broader ASX 200 universe -- cross-
  sectional momentum or absolute lookback return. First untested
  family now that MA-crossover and mean-reversion are both closed.
  Tests whether the structural refutation shape is "long-only timing
  fails in bull markets" (momentum would also refute) or
  "mean-reversion specifically fails in trending markets" (momentum
  could work, since trend-following IS the alignment). Highest
  information yield for session 8. Settle design in chat before
  Phase A: cross-sectional ranking vs absolute lookback; 3/6/12-month
  window set; skip-1 convention; rebalance frequency; long-only V1.

WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1
  Re-run the just-refuted MR z-score family with the long-only
  constraint flipped to long-short. Isolates the constraint-axis from
  the family-axis: if long-short MR shows life where long-only died,
  the killer was the constraint not the signal. (Confirmed NOT
  previously banked -- the "long-short banked since session 3" note
  did not materialise in _ideas.md or _project_state.md.) Stretch
  candidate for session 8.

═══════════════════════════════════════════════════════
RETIRED (closed this session)
═══════════════════════════════════════════════════════

Closing-SHA trail for WPs that left the Banked section because
they shipped or were superseded. Maintained from session 6 onward
to preserve provenance over silent-delete.

WP-DATA-UNIVERSE-ASX200             — closed 2146b34 (session 6)
WP-INFRA-UNIVERSE-CENTRALIZE        — closed 1e724b2 (session 6)
WP-INFRA-INTRADAY-FILTER            — closed fe9100e (session 6)
WP-INFRA-SCHEMA-DRIFT-SCRIPT        — closed 4b9037b (session 6)
WP-SIGNAL-MEAN-REVERSION-ZSCORE-V1  — closed bfbae14 (session 6,
                                      REFUTED 6/6 negative test
                                      alpha; never in Banked
                                      section, retired direct from
                                      in-flight session-6 work)
WP-INFRA-CLAUDEMD-CONCURRENT-STATUS-ASSERTION
                                    — closed dfe17de (session 7)
WP-SIGNAL-MEAN-REVERSION-ZSCORE-V2  — closed c823e20 (session 7,
                                      REFUTED on 185 ASX 200
                                      survivors; family closed
                                      cross-universe)
WP-INFRA-CERTIFI-PIN                — CLOSED UNSHIPPED (session 7;
                                      premise refuted -- certifi pin
                                      to 2025.11.12 failed identical
                                      SSL error; no commit)
WP-INFRA-SSL-TRUSTSTORE             — CLOSED UNSHIPPED (session 7;
                                      Phase A found Norton AV TLS
                                      MITM; correct halt; superseded
                                      by orchestrator-side Norton-off
                                      fix; no commit)

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

Process learnings (SESSION 6):
- Mean-reversion z-score with mean-touch exit (long entry when
  z < -threshold, exit when z >= 0) refuted as alpha generator on
  ASX blue chips 2022-2026. Pattern: high test Sharpe (0.582
  winner) but decisively negative alpha because B&H is running
  hot in the test slice. Family re-test on ASX 200 universe
  banked.
- Churn-cost mechanism is now established cross-family (validated
  V3 + MR V1; promoted from V3-specific calibration to durable
  design constraint). Applies to ANY multi-component strategy.
  Check ex-ante: "entry count when component is on vs off?"
- Bull-market test-window structurally flatters B&H over long-only
  signals. 4/4 session-4-to-6 refutations share this shape.
  Implication for future tests: report B&H Sharpe alongside signal
  Sharpe; alpha is the gold metric, not Sharpe in isolation.
- Universe-thesis tension: retail-noise-exploitation strategies
  are structurally weakest on most-arbitraged segments. ASX blue
  chips are exactly that segment. Broader-universe retests are
  the next-most-informative control.
- Engine signal_series protocol (held-position 0/1 with NaN warm-
  up, slice-then-pass to engine) is the correct abstraction across
  signal families. Reused across 4 WPs without modification.
  Future signal families plug in identically.
- PostgREST does not expose system schemas (information_schema).
  For Supabase introspection, canonical path is GET /rest/v1/ with
  Accept: application/openapi+json. Stays inside the "supabase-py
  over HTTPS only" locked decision (no native PG driver, no RPC).
- Wikipedia is the canonical source for ASX 200 constituents via
  bs4 direct parse (no env mutation needed; bs4 is a yfinance
  dep). Re-snapshot at quarterly index rebalances.
- In concurrent multi-terminal sessions, status assertions should
  use "MUST INCLUDE [files]; declared concurrent artifacts ALLOWED"
  pattern. Strict "MUST show exactly" is for solo-terminal commits.
  Validated by T2-intraday (pragmatic), T3 (halt-on-strict),
  T1-centralise (explicit-pathspec mitigation).
- .env Finnhub + Alpha Vantage keys are present-but-empty
  placeholders. Stack-aspirational. Future WPs needing those
  sources must provision or plan around the gap.

Process learnings (SESSION 7):
- Diagnostic-first discipline pays off. Norton-MITM discovery
  only happened because WP-INFRA-SSL-TRUSTSTORE Phase A was
  designed to capture the actual cert chain before installing
  truststore. Pattern: when a problem resists multiple
  hypotheses, switch from execution-first to diagnostic-first.
- Corroborated diagnoses can both be wrong. T2 and T1
  independently attributed supabase-py SSL failure to certifi.
  Both were wrong. Corroboration is not validation;
  first-principles diagnosis is.
- Spec deviations must halt-and-report. T1's silent dfe17de
  deviation (omitting orchestrator-authorized parenthetical) is
  the calibration. Orchestrator approval IS the spec; silent
  re-litigation of preferred original position is the discipline
  gap.
- .gitignore inspection in Phase A. When a WP will produce
  untracked artifacts (run logs, build outputs), Phase A should
  check .gitignore for relevant patterns before specifying status
  assertions. T2 c823e20 surfaced this.
- Sharpe-improves-as-entries-drop diagnostic. In a trending bull
  market, if Sharpe improves as combo entry count drops, suspect
  cash-drag artefact. Always cross-check against train alpha -- if
  negative across the grid, the Sharpe ordering is artefactual
  not edge.
- Mean-reversion family closed cross-universe. Same family on a
  third universe slice is unlikely to invert the structural
  shape. Vary the SIGNAL or the CONSTRAINT next, not just the
  universe.
- Norton MITM lesson logged. Future Claude / future Troy: if
  supabase-py SSL fails again, check leaf cert issuer org name
  for AV product names (Norton, Avast, ESET, Kaspersky) BEFORE
  pinning anything. If issuer looks AV-injected, the fix is
  OS-side, not code-side.
- Reconcile Phase B authorization gap (session 7 -> session 8).
  Phase A landed clean; Phase B never fired; orchestrator drafted
  session-N+1 OPEN as if reconcile shipped. Future protocol: any
  session-open handover must include a `git log --oneline -3`
  check that the SHIPPED list's reconcile SHA actually exists on
  master before treating the session as closed. Caught
  retrospectively via WP-META-SESSION7-CLOSE-AUDIT.
- Banked-state drift detected (session 7 retrospective).
  WP-INFRA-REQUIREMENTS-PIN was listed as carry-forward banked in
  the Session 8 OPEN handover but absent from _ideas.md BANKED.
  Orchestrator-side miss; corrected in this reconcile via Edit
  3a. Future protocol: any "carry-forward banked" list in a
  session-open handover should be grep-verified against _ideas.md
  before treating as source-of-truth. Same family of drift as the
  Phase-B-authorization gap above -- both are orchestrator-side
  inter-session state-drift modes catching up retroactively.
