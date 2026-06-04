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
- Mean-reversion z-score family REFUTED on ASX blue chips
  2022-2026 (V1 bfbae14, 6/6 combos negative test alpha).
  Re-test on ASX 200 universe banked as session-7 candidate
  opener.
- Churn-cost mechanism is durable cross-family: any signal
  composition adding forced state changes beyond the primary's
  natural trade count stacks brokerage + slippage faster than
  the primary generates alpha. Validated by V3 regime overlay
  (3.5x churn, bfaa817) and MR V1 mean-touch exits (5.25x
  churn, bfbae14). Check ex-ante on ANY multi-component
  strategy: "entry count when component is on vs off?"
- Bull-market backdrop is the dominant explanatory variable
  for all 4 session-4/5/6 refutations. B&H test Sharpe ~0.654
  in rising market structurally beats long-only signals that
  trade less than 100% time-in-market. Empirical, not
  execution flaw.
- Universe-thesis tension noted: ASX retail-noise edge thesis
  is weakest on most-arbitraged blue-chip segment; broader
  ASX 200 universe rebalances this for future tests.
- Wikipedia (via bs4 direct table parse, no env mutation) is
  canonical source for ASX 200 constituents. Re-snapshot
  periodically to capture index rebalances.
- Engine signal_series protocol (caller precomputes signal
  once over full history; slices for train/test or filter
  compositions; engine consumes 0/1 held-position series with
  NaN warm-up) validated across 4 WPs across 2 signal
  families (MA crossover V1/V2/V3, MR V1). Correct
  abstraction; reuse without modification expected for future
  signal families.
- In concurrent multi-terminal sessions, atomic commit chain
  status assertions read as "MUST INCLUDE [these files];
  other declared concurrent artifacts ALLOWED via
  explicit-pathspec git add". Strict literal "MUST show
  exactly" remains the discipline for solo-terminal commits.
  (CLAUDE.md amendment banked as
  WP-INFRA-CLAUDEMD-CONCURRENT-STATUS-ASSERTION.)
- .env contains FINNHUB_API_KEY and ALPHA_VANTAGE_API_KEY as
  PRESENT-BUT-EMPTY placeholders. Stack-aspirational, not
  provisioned. Future WPs needing either must provision or
  plan around the gap.
- Mean-reversion z-score family REFUTED on both narrow (V1
  bfbae14, 10 blue chips) and broad (V2 c823e20, 185 ASX 200
  survivors) universes. Family chapter closed. Next signal work
  must change SIGNAL spec OR LONG-ONLY constraint, not just
  universe.
- Concurrent-tolerant status assertion pattern locked in
  CLAUDE.md (dfe17de). SOLO-TERMINAL strict-literal vs CONCURRENT
  MUST-INCLUDE; mode declared upfront in WP prompt GATE; default
  SOLO.
- Norton AV TLS interception is the supabase-py SSL
  CERTIFICATE_VERIFY_FAILED root cause on this Windows ARM64
  machine. Fix is environmental — Norton Settings → Safe Web →
  HTTPS scanning OFF. certifi pinning does NOT fix it. (Also
  mirrored in ENVIRONMENT NOTES item 14.)
- supabase-py + stock certifi 2026.4.22 reaches Supabase cleanly
  with Norton SSL/TLS scanning disabled. No truststore, no SSL
  bootstrap module, no env vars. Validated end-to-end (T1 probe
  + c823e20 full-grid run).
- Bull-market backdrop + long-only constraint is the dominant
  explanatory variable for 5 consecutive signal-family
  refutations (MA crossover V1/V2/V3, MR z-score V1, MR z-score
  V2). Mean-reversion family closed cross-universe (narrow V1
  bfbae14, broad V2 c823e20). Next signal-family test must vary
  the signal mechanic or the long-only constraint, not just the
  universe.
- Cash-drag Sharpe artefact pattern: in trending markets, Sharpe
  improving as entry count drops is dampened-vol-via-inaction,
  not signal value. Diagnostic check: if train alpha is negative
  across all combos, Sharpe ordering is artefactual.
- Momentum absolute-lookback per-ticker timing family REFUTED
  long-only on broad ASX 200 (80f9993, 3/3 combos negative test
  alpha; winner N=252 test alpha -13.50%). This is the WEAKEST
  momentum formulation; cross-sectional ranked variant
  (Jegadeesh-Titman canonical, banked WP-SIGNAL-MOMENTUM-CROSS-
  SECTIONAL-V1) remains untested. Refutation does NOT close the
  cross-sectional door.
- 6 consecutive long-only signal-family refutations across 3
  distinct mechanic families (MA crossover V1/V2/V3, MR z-score
  V1/V2, momentum absolute-lookback V1). The constant is the
  long-only constraint, not the signal mechanic. Long-only
  constraint = prime suspect. Next test must vary the constraint
  axis (long-short) before retesting more signal mechanics.
  Prerequisite: WP-INFRA-ENGINE-SHORTSIDE.
- Cash-drag Sharpe artefact promoted from MR-specific finding to
  universal long-only-in-trending-market property. Validated
  cross-family across MR V2 (c823e20) and Momentum V1 (80f9993):
  in both, the lowest-entry-count combo wins on test Sharpe via
  dampened-vol-from-inaction while train alpha is uniformly
  negative across the grid.
- Supabase legacy HS256-signed JWT in-place rotation EOL'd. The
  current SUPABASE_SERVICE_ROLE_KEY is a legacy HS256 JWT;
  Supabase no longer offers same-key rotation. Forward path is
  JWT-signing-key migration (generate new signing key, swap,
  retire old). Banked WP-INFRA-SUPABASE-NEW-KEY-MIGRATION
  supersedes WP-INFRA-ROTATE-SERVICE-KEY (S7-banked, S8-closed-
  deferred). Also mirrored in ENVIRONMENT NOTES item 15.
- $TEMP/<unique>.txt -> mv .commit-msg.tmp long-body commit
  pattern validated under its own documentation: 8ba9416 used the
  pattern to commit the pattern's spec (~2200 char body, above
  the ~500 char heredoc memory-bound). Convention is recursive-
  safe. .commit-msg.tmp gitignore-add banked as
  WP-INFRA-GITIGNORE-COMMIT-MSG-TMP to eliminate the post-stage-
  mv ordering constraint.
- CLAUDE.md "Why <X>" bullet ordering in the Commit-discipline
  Rules block is thematic, not numerical. New bullets append by
  theme proximity, not by numbered step. Established by 8ba9416
  (added "Why .gitignore-matching artefacts hide" and "Why long
  commit bodies use $TEMP/mv" thematic bullets without
  renumbering the existing "Why step N exists" ones).
- Carry-forward banked lists in session-open handovers are NOT
  source-of-truth. _ideas.md BANKED is. Future session-open
  handovers must `grep`-verify carry-forward claims against
  _ideas.md before treating them as authoritative. (Promoted
  from S7 calibration; same family as the Phase-B-authorization-
  gap protocol fix. Mirrored as calibration note in _ideas.md.)
- Long-short engine built + regression-clean; spec FROZEN at
  3cd4d0b. Ternary {NaN, -1, 0, +1} stateful held-position;
  cash-based sizing sign-flipped on short leg; symmetric costs
  (0.1% brokerage + $0.01 slippage both legs every entry/exit);
  pure-drag borrow charged daily on abs short notional, entry-
  inclusive / exit-exclusive day-counting, default annualized
  rate 0.0 (tunable per ticker); reverse-MTM at exit (drag IS
  the daily charge); reports BOTH gross-of-borrow and net-of-
  borrow metrics. Long-only callers regression-clean (aggregate
  delta vs baseline = 0; byte-identical CSV outputs across MA
  crossover V1/V2/V3, MR z-score V1/V2, momentum V1).
- Borrow tiering (src/backtest/borrow_tiering.py): median daily
  $-volume terciles via qcut → annualized 1% top / 4% mid / 8%
  bottom liquidity. Full-sample classification (structural cost
  assumption, not return leakage). Paginated fetch (PostgREST
  1000-row cap workaround applies; this is the second consumer
  of fetch_prices_full's pagination idiom after the V2 grid
  caller).
- MR family CLOSED under per-ticker absolute timing formulation:
  long-only refuted (c823e20, test alpha -35.89%) AND long-short
  refuted WORSE (cc2e4c6, test net alpha -81.16%). Further MR
  work must change SIGNAL STRUCTURE (cross-sectional or regime-
  conditional, banked WP-SIGNAL-MR-CROSSSECTIONAL-V1 +
  WP-SIGNAL-MR-REGIME-CONDITIONAL), not re-run a per-ticker
  formulation.
- Lifting the long-only constraint did NOT rescue MR -- it HURT
  it. Long-only was the LESS BAD configuration (-35.89% vs
  -81.16% test alpha). The short leg's trend-fighting in the
  bull-market test window is the binding problem, not the
  constraint itself. Net-vs-gross borrow gap ~3.6 pts is dwarfed
  by the -77.55% gross loss -- borrow drag is real but small;
  the short leg lost money fighting the trend, not paying
  borrow. Constraint-axis thesis remains OPEN for MOMENTUM
  (where short leg trend-aligns rather than trend-fights);
  long-short momentum is now the cleaner test of the long-only-
  constraint-vs-signal-mechanic question.
- Concurrent-push fix: after `git commit` run
  `git fetch origin master`; if `origin/master` == your commit's
  parent push directly (clean FF); if origin advanced HALT and
  let the orchestrator sequence the rebase. Do NOT
  `git pull --rebase` on a shared dirty tree; do NOT autostash
  (disturbs other terminals' in-flight files). Banked CLAUDE.md
  amendment WP-INFRA-CLAUDEMD-CONCURRENT-PUSH-AMENDMENT.
- All self-fetches from Supabase must paginate (PostgREST 1000-
  row cap applies beyond fetch_prices_full). Affects any new
  consumer reading > 1000 rows from prices or any future high-
  row-count table; reuse the existing pagination helper rather
  than reimplementing.
- Cross-test finding (S9 + S10): BOTH long-short tests (MR-LS
  cc2e4c6, momentum-XSEC-LS 7ea4c08) died on the SHORT leg in a
  rising market, borrow immaterial both times (net-vs-gross gap
  ~3.6 pts on MR-LS, ~0.94 pts on momentum-XSEC). Short-side
  selection is structurally loss-making in this regime/universe.
  The cross-test invalidates "borrow drag" as the killer and
  isolates the short-leg-directional-mismatch problem.
- Long top-decile momentum sleeve (J=252, K=18, monthly rebal)
  produced +6.87% test return ~= ^AXJO +6.65% -- no alpha,
  effectively beta. Sum-of-per-ticker long B&H over the same
  test window = +33.91%, so holding the universe beat the long-
  short by ~36 pts. Selecting 36 of 185 names and shorting the
  wrong 18 forfeited the bulk of the market's return.
- CONCLUSION: across 3 signal families (MA crossover, MR z-
  score, momentum -- both absolute timing and cross-sectional
  ranked) x {long-only, long-short} on the liquid ASX-200
  survivor universe over a multi-year bull, no simple price-
  based edge beats holding the universe. Price-only-on-liquid-
  ASX thesis CLOSED (negative). Cross-sectional momentum family
  closed (the canonical Jegadeesh-Titman formulation also
  fails). Refutation count unchanged at 7 but qualitatively
  conclusive: per-ticker timing, cross-sectional ranking, and
  long-only/long-short variants all exhausted on this universe.
- STRATEGIC PIVOT (decided at S10 close): (a) out-of-data-type
  -- pivot to fundamentals/quality FIRST, on the CURRENT liquid
  universe (isolate the signal-type variable; low turnover;
  reuse existing plumbing). Gated on
  WP-DATA-FUNDAMENTALS-FEASIBILITY-PROBE (what fields are
  reliably sourceable for ASX via yfinance / Finnhub /
  AlphaVantage; history depth; Finnhub + AlphaVantage keys
  still placeholders → provisioning needed). (b) Out-of-
  universe smaller-cap SECOND, only if quality shows a pulse
  (change one variable at a time -- if we change both
  data-type AND universe at once we can't isolate which
  rescued any positive result). (c) Defensive trend-overlay
  sleeve in parallel (risk-management, NOT alpha; pays the
  cash-drag premium during sustained bull regimes; crash
  backtests are low-power -- interpret with care).
- Late-landed-reconcile booking convention CONFIRMED across two
  precedents: a63cb38 (S7 reconcile late-landed in S8 by weeks
  due to Phase-B-authorization gap; booked as S8 SHA-date-WP
  entry) + af791a2 (S9 reconcile late-landed in S10 by ~12
  hours; booked as S10 SHA-date-WP entry). On-schedule
  reconciles (60d4181, this WP) remain unbooked per closer-
  parenthetical-only convention. The trigger is calendar-date
  separation from the substantive commits of the closing
  session, not the magnitude of the delay.

═══════════════════════════════════════════════════════
CURRENT WP
═══════════════════════════════════════════════════════
(between WPs — SESSION 10 closed. Cross-sectional momentum long-
short REFUTED (7ea4c08, TEST net alpha vs ^AXJO -8.71%, ^AXJO
+6.65% vs L/S net -2.05%). Short leg the killer (-8.93% vs long
+6.87% ~= beta); borrow drag immaterial (+0.94%). Cross-test
finding: BOTH long-short tests (MR-LS cc2e4c6, momentum-XSEC-LS
7ea4c08) died on the short leg in a rising market, isolating short-
side directional mismatch as the structural problem. CONCLUSION:
no simple price-based edge on liquid ASX-200 survivors over the
multi-year bull -- price-only-on-liquid-ASX thesis CLOSED; cross-
sectional momentum family closed; refutation tally 7 (qualitatively
conclusive). STRATEGIC PIVOT: out-of-data-type fundamentals/quality
FIRST on current universe (isolate signal-type variable), out-of-
universe smaller-cap SECOND, plus defensive trend-overlay sleeve.
The S9-close primary (WP-SIGNAL-MOMENTUM-LONGSHORT-V1) was
superseded mid-session by the orchestrator's pivot to cross-
sectional momentum, which delivered the broader-implication
refutation that obviated the original constraint-axis question.
SESSION 11 opens with WP-DATA-FUNDAMENTALS-FEASIBILITY-PROBE as
primary (gating for the fundamentals/quality arc). See "Immediate
queue — session 11" below.)

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
  WP-RECONCILE-SESSION-5-CLOSE        — 283112f

Closed in SESSION 6:
  WP-SIGNAL-MEAN-REVERSION-ZSCORE-V1  — bfbae14  (T1, 6-combo z-score grid
                                                  REFUTED 6/6 negative test
                                                  alpha; churn-cost mechanism
                                                  cross-family confirmed)
  WP-INFRA-INTRADAY-FILTER            — fe9100e  (T2, defensive volume<=0 row
                                                  filter on daily fetch +
                                                  historical backfill)
  WP-INFRA-SCHEMA-DRIFT-SCRIPT        — 4b9037b  (T3, scripts/verify_schema.py
                                                  via PostgREST OpenAPI;
                                                  SCHEMA CLEAN 25/25)
  WP-INFRA-UNIVERSE-CENTRALIZE        — 1e724b2  (T1, consolidated TICKERS
                                                  dict into
                                                  src/data/universe.py)
  WP-DATA-UNIVERSE-ASX200             — 2146b34  (T2, 10 -> 201 stocks via
                                                  Wikipedia parse; 189/190
                                                  new tickers in 218.8s;
                                                  XYX.AX 404 banked)
  WP-RECONCILE-SESSION-6-CLOSE        — 4790939

Closed in SESSION 7 (2026-05-19 .. 2026-05-23; reconcile late-landed
session 8, 2026-05-31):
  WP-INFRA-CLAUDEMD-CONCURRENT-STATUS-ASSERTION
                                      — dfe17de  (T1, +13 lines CLAUDE.md
                                                  Commit-discipline Rules
                                                  block; SOLO vs CONCURRENT
                                                  status-assertion modes)
  WP-SIGNAL-MEAN-REVERSION-ZSCORE-V2  — c823e20  (T2, V1 spec re-run on
                                                  185 ASX 200 survivors;
                                                  REFUTED 6/6 negative test
                                                  alpha; family closed
                                                  cross-universe)
  Investigated, unshipped (no commits):
  WP-INFRA-CERTIFI-PIN                — CLOSED UNSHIPPED (T1; premise
                                        refuted -- certifi 2025.11.12
                                        failed identical SSL error;
                                        rolled back to 2026.4.22)
  WP-INFRA-SSL-TRUSTSTORE             — CLOSED UNSHIPPED (T1; Phase A
                                        found Norton "Web/Mail Shield
                                        Root" leaf cert = AV TLS MITM;
                                        correct halt; superseded by
                                        orchestrator-side Norton-off fix)
  WP-RECONCILE-SESSION-7-CLOSE        — a63cb38  (T4, resumed; landed
                                                  2026-05-31 after
                                                  WP-META-SESSION7-CLOSE-
                                                  AUDIT caught missed
                                                  Phase B)

Closed in SESSION 8 (2026-05-31 .. 2026-06-01):
  WP-SIGNAL-MOMENTUM-V1               — 80f9993  (T2, per-ticker absolute
                                                  lookback 3-combo grid
                                                  REFUTED on 185 ASX 200
                                                  survivors; winner N=252
                                                  test alpha -13.50%;
                                                  cross-sectional variant
                                                  banked)
  WP-INFRA-CLAUDEMD-COMMIT-CONVENTIONS-V2
                                      — 8ba9416  (T1, +39 lines CLAUDE.md
                                                  across 4 amendments
                                                  codifying S7 process
                                                  gaps; dogfooded
                                                  amendment c; folds in
                                                  CLAUDEMD-SSL-LESSON as
                                                  amendment d)
  Investigated, unshipped (no commits):
  WP-META-SESSION7-CLOSE-AUDIT        — CLOSED UNSHIPPED (T4, diagnostic
                                        only; surfaced missed S7 Phase B
                                        authorization; triggered a63cb38
                                        resumed reconcile)
  WP-INFRA-ROTATE-SERVICE-KEY         — CLOSED DEFERRED (Supabase legacy
                                        HS256 in-place rotation EOL'd;
                                        superseded by WP-INFRA-SUPABASE-
                                        NEW-KEY-MIGRATION)
  WP-RECONCILE-SESSION-8-CLOSE        — 60d4181

Closed in SESSION 9 (2026-06-03):
  WP-INFRA-GITIGNORE-COMMIT-MSG-TMP   — 85da176  (T1, anchored
                                                  /.commit-msg.tmp in
                                                  .gitignore; relaxes
                                                  mv-after-stage ordering
                                                  from 8ba9416 amend c)
  WP-INFRA-REQUIREMENTS-PIN           — cfc0e06  (T3, split to 6-pin
                                                  requirements.txt +
                                                  requirements.lock with
                                                  ARM64 transitive set;
                                                  bs4 made explicit)
  WP-INFRA-ENGINE-SHORTSIDE           — 3cd4d0b  (T2, long-short
                                                  extension with pure-drag
                                                  borrow; ternary
                                                  {NaN,-1,0,+1}; symmetric
                                                  costs; regression-clean
                                                  delta 0; engine FROZEN)
  WP-SIGNAL-MEAN-REVERSION-LONGSHORT-V1
                                      — cc2e4c6  (T2, MR family closed
                                                  cross-constraint;
                                                  REFUTED WORSE than long-
                                                  only -- test net alpha
                                                  -81.16% vs -35.89%;
                                                  short leg trend-fights)
  WP-RECONCILE-SESSION-9-CLOSE        — af791a2  (T4, late-landed by
                                                  ~12h into S10; booked
                                                  per late-landed
                                                  precedent)

Closed in SESSION 10 (2026-06-04):
  WP-SIGNAL-MOMENTUM-CROSS-SECTIONAL-V1
                                      — 7ea4c08  (T1, cross-sectional
                                                  momentum L/S, monthly
                                                  rebal, K=18/leg,
                                                  dollar-neutral; REFUTED
                                                  test net alpha vs ^AXJO
                                                  -8.71%; short leg the
                                                  killer; cross-sectional
                                                  momentum family closed;
                                                  price-only-on-liquid-
                                                  ASX thesis CLOSED)
  WP-RECONCILE-SESSION-10-CLOSE       — (see `git log -1 --oneline`)

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
V2 grid, bfaa817 V3 regime-filtered). Mean-reversion z-score family
closed CROSS-UNIVERSE AND CROSS-CONSTRAINT across three refutations
(bfbae14 V1 narrow long-only, c823e20 V2 broad long-only, cc2e4c6
V1 broad long-short -- LS made it WORSE not better). Momentum
family closed CROSS-FORMULATION across two refutations (80f9993
per-ticker absolute lookback long-only; 7ea4c08 cross-sectional
ranked long-short -- the Jegadeesh-Titman canonical formulation
also fails on this universe). Long-short variant of per-ticker
momentum (WP-SIGNAL-MOMENTUM-LONGSHORT-V1) was the S9-close primary
recommendation but was superseded mid-S10 by the orchestrator's
pivot to cross-sectional momentum; it remains banked, deprioritised
post-strategic-pivot.

Engine: FROZEN at 3cd4d0b. Long-short capable; regression-clean
across all 6 prior long-only callers (aggregate delta 0; byte-
identical CSV outputs). Ternary {NaN,-1,0,+1} stateful held-
position; symmetric costs (0.1% brokerage + $0.01/share slippage
both legs every entry/exit); pure-drag borrow charged daily on abs
short notional (default annualised 0.0; tunable per ticker via
borrow tiering). signals.py: ma_crossover, mean_reversion_zscore,
momentum_absolute_lookback, mean_reversion_zscore_longshort, +
cross-sectional momentum ranking helpers (7ea4c08). borrow_tiering.py
(S9) and cross-sectional ranking + monthly-rebal portfolio plumbing
(S10) reused the frozen engine via signal_series ternary; no engine-
surface-area changes since 3cd4d0b.

Production state at session-10 close: 38 commits on master (37
through 7ea4c08 + this reconcile; git-authoritative; the S9 drift
correction stands). 201 stocks, 239,694 prices, 0 signals persisted
(signals computed in-backtest, never written to DB). No data
ingestion this session -- stocks / prices unchanged from session-6
close. Per-ticker coverage unchanged: 200 ASX 200 constituents +
^AXJO benchmark. Orphan/short-history tickers unchanged (XYX banked
WP-DATA-XYX-RECOVER; 7 zero-row tickers banked
WP-DATA-ASX200-ORPHANS-V2). ^AXJO sits in stocks table (cosmetic
mismatch; refactor banked WP-DB-BENCHMARKS-TABLE).

Signal-family scorecard (post-S10): refutation tally 7 -- count
unchanged from S9 but qualitatively conclusive. 3 signal families
(MA crossover, MR z-score, momentum) x {long-only, long-short} x
{per-ticker timing, cross-sectional ranked} exhausted on the liquid
ASX-200 survivor universe over the 2022-2026 bull window. No simple
price-based edge beats holding the universe. Cross-test isolation
(S9 + S10): short-side selection structurally loss-making in this
regime/universe; borrow drag immaterial (~3.6 pts on MR-LS, ~0.94
pts on momentum-XSEC-LS); the binding problem is short-leg
directional mismatch. Price-only-on-liquid-ASX thesis CLOSED
(negative).

STRATEGIC PIVOT (S10 close): out-of-data-type fundamentals/quality
FIRST on current liquid universe (isolate signal-type variable),
out-of-universe smaller-cap SECOND (one variable at a time), plus
defensive trend-overlay sleeve in parallel (risk-management, not
alpha). Banked structural-MR pivots (WP-SIGNAL-MR-CROSSSECTIONAL-V1
+ WP-SIGNAL-MR-REGIME-CONDITIONAL) remain on the bench as price-
based residuals; the strategic pivot deprioritises them relative to
the fundamentals/quality arc.

Environment: Norton AV HTTPS scanning OFF (S7), verified clean
across all S8/S9/S10 commits. Supabase legacy HS256-signed JWT
in-place rotation EOL'd (S8 finding); WP-INFRA-SUPABASE-NEW-KEY-
MIGRATION still open. .commit-msg.tmp gitignored (85da176); long-
body commit pattern uses direct-write to .commit-msg.tmp.
Transient node API ECONNREFUSED observed during a T-fire window
on 2026-06-04; network / Norton-toggle / proxy all verified clean;
resolved on retry; no config change. See ENVIRONMENT NOTES items
14-15 (Norton + Supabase JWT).

UI shell remains gated on WP-UI-FRONTEND-STACK-ARM64-RESOLUTION.

Banked WPs (session 6 outcomes, still open):
  WP-INFRA-PRICES-ZEROVOL-CLEANUP — one-shot cleanup of the 7 existing
                                    volume=0 rows on blue chips (ANZ.AX
                                    2022-07-18/19/20; CSL.AX 2021-12-14/
                                    15; NAB.AX 2023-11-15; RIO.AX
                                    2023-11-15). Daily fetcher's filter
                                    (fe9100e) prevents reintroduction.
                                    Tiny priority.
  WP-INFRA-YFUTILS-PERTICKER-INGEST
                                  — per-ticker fetch + reshape +
                                    volume<=0 filter + upsert pattern
                                    inlined in 2 consumers; consolidate
                                    when a 3rd materialises. Low priority.
  WP-DATA-XYX-RECOVER             — Yahoo ticker-mapping for Block, Inc.
                                    (XYX 404; likely SQ2.AX). Low priority.
  WP-INFRA-SCHEMA-DRIFT-V2        — extend verify_schema.py to defaults,
                                    indexes, triggers, CHECK, FK targets,
                                    numeric precision/scale. Low priority.

Banked WPs (session 7 outcomes, still open):
  WP-DATA-ASX200-ORPHANS-V2       — investigate 7 zero-row tickers (AAI,
                                    DNL, GGP, L1G, RYM, SGH, VGN);
                                    per-ticker Yahoo mapping. Low priority.

Banked WPs (session 8 outcomes, still open):
  WP-INFRA-SUPABASE-NEW-KEY-MIGRATION
                                  — supersedes WP-INFRA-ROTATE-SERVICE-
                                    KEY. Generate new Supabase JWT
                                    signing key, swap in .env, verify
                                    supabase-py reach, retire old key.
                                    Driven by Supabase legacy-JWT
                                    in-place rotation EOL (S8 finding).
  WP-SIGNAL-MOMENTUM-LONGSHORT-V1 — same momentum spec as V1 (absolute
                                    lookback, N in {63,126,252}, skip=21)
                                    but constraint flipped to long-short
                                    via the frozen engine + borrow
                                    tiering. Was S9-close primary
                                    recommendation; superseded mid-S10
                                    by the orchestrator's pivot to
                                    cross-sectional momentum (7ea4c08).
                                    Deprioritised post-S10 strategic
                                    pivot (fundamentals/quality first);
                                    remains banked as a price-based
                                    residual probe.

Banked WPs (session 9 outcomes, still open; deprioritised by S10
strategic pivot):
  WP-SIGNAL-MR-CROSSSECTIONAL-V1  — long bottom-decile-z / short top-
                                    decile-z daily; market-neutral.
                                    Needs ranking/portfolio plumbing.
                                    Was a price-based MR-residual probe;
                                    deprioritised post-S10 strategic
                                    pivot but kept as bench candidate
                                    if fundamentals/quality arc reveals
                                    interactions with MR signal.
  WP-SIGNAL-MR-REGIME-CONDITIONAL — gate MR L/S signal on ^AXJO 200-DMA
                                    regime. Pairs with
                                    WP-SIGNAL-MR-CROSSSECTIONAL-V1 as
                                    structural-pivot candidates;
                                    similarly deprioritised post-S10.
  WP-INFRA-CLAUDEMD-CONCURRENT-PUSH-AMENDMENT
                                  — codify the concurrent-push pattern
                                    in CLAUDE.md Commit-discipline:
                                    after commit `git fetch origin
                                    master`; if origin == parent push
                                    FF directly; if origin advanced
                                    HALT and let orchestrator sequence.
                                    ~10-line amendment. Process WP;
                                    not affected by strategic pivot.

Banked WPs (session 10 outcomes):
  WP-DATA-FUNDAMENTALS-FEASIBILITY-PROBE
                                  — PROMOTED TO PRIMARY for session 11.
                                    Gating WP for the fundamentals/
                                    quality arc. What fundamental fields
                                    are reliably sourceable for ASX via
                                    yfinance / Finnhub / AlphaVantage
                                    (P/E, P/B, ROE, debt/equity,
                                    earnings yield, revenue growth,
                                    etc.); history depth (point-in-time
                                    vs latest-snapshot; restatement
                                    handling); coverage of the current
                                    185-survivor universe. Finnhub +
                                    AlphaVantage keys still present-
                                    but-empty placeholders in .env --
                                    provisioning needed. Read-only
                                    investigation only; no Phase B
                                    until data-source feasibility is
                                    locked.
  WP-SIGNAL-QUALITY-VALUE-XSEC-V1 — quality/value cross-sectional
                                    signal on the current liquid
                                    universe (185 ASX 200 survivors).
                                    Composite ranking on a small basket
                                    of fundamental ratios (e.g. low
                                    P/E + high ROE + low debt/equity).
                                    Monthly or quarterly rebal; long
                                    top-decile, short bottom-decile (or
                                    long-only if SUPABASE-NEW-KEY-
                                    MIGRATION exposes constraint
                                    issues). GATED on
                                    WP-DATA-FUNDAMENTALS-FEASIBILITY-
                                    PROBE.
  WP-OVERLAY-TREND-REGIME-CRASH-SLEEVE
                                  — always-on ^AXJO 200-DMA trend
                                    overlay; insurance-with-premium
                                    framing (pays the cash-drag premium
                                    during sustained bulls in exchange
                                    for reducing exposure during
                                    trend-down regimes). Risk-
                                    management WP, NOT alpha-
                                    generation. Reuses regime_above_ma
                                    helper (bfaa817). Low-power crash-
                                    backtest caveat: the available
                                    sample (2021-2026) contains few
                                    crash episodes; metric
                                    interpretation requires care.
  WP-SIGNAL-MOMENTUM-XSEC-QUINTILE-V1
                                  — breadth robustness probe; low prior.
                                    Banked in 7ea4c08 commit body. Same
                                    cross-sectional ranking + monthly
                                    rebal as 7ea4c08 but with quintile
                                    breadth (K=37/leg) rather than
                                    decile (K=18/leg). Tests whether
                                    the 7ea4c08 refutation is robust to
                                    breadth or specific to the decile
                                    cut. Low prior: the cross-test
                                    finding (short-leg-directional-
                                    mismatch is structural) suggests
                                    breadth won't rescue.

Immediate queue — session 11:

  - Reconcile (this WP) -- mandatory first action, landing now.
  - WP-DATA-FUNDAMENTALS-FEASIBILITY-PROBE (PRIMARY) -- gating
    investigation for the fundamentals/quality arc. Phase A
    read-only: what fields, what history, what coverage, what
    provisioning is needed. Outcomes will lock the spec for
    WP-SIGNAL-QUALITY-VALUE-XSEC-V1.
  - WP-INFRA-SUPABASE-NEW-KEY-MIGRATION -- hygiene closeout;
    pairs well with the fundamentals provisioning if
    AlphaVantage/Finnhub get keys provisioned at the same time.
  - WP-INFRA-CLAUDEMD-CONCURRENT-PUSH-AMENDMENT -- ~10-line
    process WP; pairs naturally with a reconcile slot or any
    quick warm-up slot.
  - WP-OVERLAY-TREND-REGIME-CRASH-SLEEVE -- defensive sleeve;
    can run in parallel with the fundamentals arc since it's
    risk-management not signal-generation; reuses existing
    regime_above_ma helper.
  - Stretch: WP-SIGNAL-MOMENTUM-XSEC-QUINTILE-V1 (breadth
    robustness on cross-sectional momentum; low prior).

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
All 5 terminals idle post-session-10 close.
T1 — idle (closed 7ea4c08 WP-SIGNAL-MOMENTUM-CROSS-SECTIONAL-V1
            -- REFUTED; cross-sectional momentum family closed;
            price-only-on-liquid-ASX thesis CLOSED)
T2 — idle (not activated this session; closed S9's cc2e4c6 and
            3cd4d0b)
T3 — idle (not activated this session; closed S9's cfc0e06)
T4 — idle (closed af791a2 WP-RECONCILE-SESSION-9-CLOSE late-
            landed; closing WP-RECONCILE-SESSION-10-CLOSE)
T5 — held / spare (not activated this session)

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

14. Norton AV TLS interception (surfaced SESSION 7)
    Norton SSL/TLS scanning toggle at Norton Settings → Safe Web →
    HTTPS scanning is OFF as of 2026-05-23. Do NOT re-enable — it
    MITM-terminates upstream TLS and re-signs every cert with
    Norton's private root, which breaks supabase-py and every
    certifi-using HTTPS library (CERTIFICATE_VERIFY_FAILED). Other
    Norton protections remain ON. Diagnostic if supabase-py SSL
    fails again: inspect the leaf cert issuer — "Norton Web/Mail
    Shield Root" or any AV-product organization name means the AV
    is intercepting; the fix is the OS-side toggle, NOT a code-side
    certifi pin (pinning to certifi 2025.11.12 was tried and failed
    identically). Security note: SUPABASE_SERVICE_ROLE_KEY was
    visible to Norton in plaintext on every supabase-py call while
    scanning was on — rotation banked as WP-INFRA-SUPABASE-NEW-KEY-
    MIGRATION (supersedes the S7-banked WP-INFRA-ROTATE-SERVICE-KEY
    after Supabase legacy in-place rotation found EOL'd; see item
    15 below). Norton-off status verified clean across all session-8
    commits (a63cb38 / 80f9993 / 8ba9416).

15. Supabase JWT-signing-key auto-rotation (surfaced SESSION 8)
    Supabase legacy HS256-signed JWT API keys (the format currently
    in .env for SUPABASE_SERVICE_ROLE_KEY and SUPABASE_ANON_KEY) no
    longer support in-place rotation — the dashboard's "rotate this
    key" flow is EOL'd. Forward path is JWT-signing-key migration:
    generate new signing key in Supabase dashboard, deploy new key
    to .env, verify supabase-py reach with 1-row probe, retire old
    key. Banked WP-INFRA-SUPABASE-NEW-KEY-MIGRATION. The S7-banked
    WP-INFRA-ROTATE-SERVICE-KEY is superseded (CLOSED DEFERRED in
    S8 after the in-place flow was found EOL'd mid-attempt).
    Implication: future Supabase key rotations require new-key-
    migration provisioning effort, not the trivial dashboard click
    assumed at S7 banking time.
