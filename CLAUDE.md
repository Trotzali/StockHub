# CLAUDE.md — StockHub Working Model

Read automatically by Claude Code on terminal start.
Captures the standing rules so per-prompt scaffolding
focuses on the specific task.

## Project at a glance

- StockHub — ASX stock screening platform
- Repo: https://github.com/Trotzali/StockHub
- Prod branch: `master`
- Working dir: C:\Users\admin\Projects\StockHub
- Stack: Python 3.12 ARM64 venv, Supabase free tier
  (supabase-py over HTTPS only), Plotly, yfinance +
  Finnhub + Alpha Vantage
- Cadence: daily EOD signals only — no intraday

## Environment

Shell: PowerShell 5.1 on Windows 11 ARM64 (Snapdragon).

1. **git commit messages**: do NOT use multi `-m` chains
   with backtick continuation. Use `git commit -F
   <tempfile>`; remove the tempfile before push.
2. **File creation**: do NOT use `Set-Content -Encoding
   utf8` (writes UTF-8 with BOM). Use the Write tool or
   `[System.IO.File]::WriteAllText` with
   `[System.Text.UTF8Encoding]::new($false)`.
3. **Benign noise**: LF→CRLF warnings on `git add` are
   expected. `NativeCommandError` on `git push` with 2>&1
   is cosmetic. Exit code is authoritative.
4. **Python**: use `python` (3.12.10 ARM64, has pip).
   Do NOT use `python3` (3.14, pip not bound).
5. **Architecture is ARM64.** Many PyPI packages with
   native C extensions lack `win_arm64` wheels.
   Confirmed gaps: psycopg2-binary, psycopg-binary,
   pyarrow at modern versions. Pure-Python fine.
6. **Pip install policy: always `--only-binary :all:`.**
   - Silent sdist fallback compiles from source and
     fails on this box.
   - Silent resolver back-walk: pip exits 0 but resolves
     to a stale major.
   Pip exit 0 is necessary but NOT sufficient. Sanity-
   check resolved versions vs current-stable before
   pinning.
7. **DB driver**: supabase-py only. No native PG drivers.
8. **ASCII-only stdout in PowerShell scripts.**
   PowerShell's default cp1252 codec crashes on Unicode
   characters in stdout (`->`, em-dashes, Greek letters,
   box-drawing). Python scripts that print to PowerShell
   stdout must use ASCII equivalents (`->` not `→`, `--`
   not `—`, `alpha` not `α`). Commit message bodies via
   `git commit -F <tempfile>` are UTF-8 file writes per
   item 2, so Unicode in commit messages is FINE — the
   constraint is stdout only. Validated session 4: probe-
   exit `UnicodeEncodeError` crash on `→` in
   WP-SIGNAL-MA-CROSSOVER-V1 Phase A; full Phase B output
   ran clean under ASCII-only discipline.
9. **AV TLS interception as supabase-py SSL failure.**
   If supabase-py reports `[SSL: CERTIFICATE_VERIFY_
   FAILED]`, inspect the leaf cert's issuer before any
   fix attempt. AV-product issuer org names (Norton,
   Avast, ESET, Kaspersky, McAfee, Bitdefender, etc.)
   indicate TLS interception: the AV re-signs every
   cert with its private root, breaking certifi's
   validation. Fix: OS-side toggle (Norton: Settings
   -> Safe Web -> HTTPS scanning OFF). Do NOT pin
   certifi (tried WP-INFRA-CERTIFI-PIN session 7, no
   commit; same error across 2025.11.12 and 2026.4.22).
   Do NOT install `truststore` -- it silently accepts
   the MITM and exposes `SUPABASE_SERVICE_ROLE_KEY` to
   the AV. Surfaced + resolved session 7 (2026-05-23).

## Rule 0 — investigate before executing

Every prompt has Phase A and Phase B.

- **Phase A is read-only.** No writes, no DDL, no
  commits, no DB mutations. Investigate, report, STOP.
- **Phase B executes only after explicit user
  authorisation** (`proceed`, `run it`, `fire`).
  Clarification questions are NOT authorisation.
- Probe scripts from Phase A are deleted in the same
  session — never committed.

## Commit discipline

Every commit is a single atomic Bash chain (one tool
call, chained with `&&`):

1. `cd "C:/Users/admin/Projects/StockHub"`
2. `git status -s` — pre-stage assertion (only expected
   paths should appear)
3. `git check-ignore -v <new-paths>` — silent-ignore
   trip wire. Empty stdout / exit 1 = PASS.
4. `git add <explicit pathspec>` — never `git add .`
5. `git diff --cached --name-only` — confirm only the
   intended files are staged
6. Write commit message to a tempfile (heredoc)
7. `git commit -F <tempfile>`
8. `rm <tempfile>`
9. `git push origin master`
10. `git log -1 --oneline` + `git status -s` for the
    report

Rules:
- One work product per commit.
- Commit messages narrate the work, reference gating
  commits where relevant, and bank follow-up WPs
  explicitly.
- Whitelist-gate for known-safe unstaged files
  (e.g. `_timeline.md` when the WP isn't a reconcile).
- Deviations from locked specs are documented in the
  commit message AND banked in `_ideas.md`.
- Why step 3 exists: `git status -s` shows `?? src/`
  for an untracked directory — shorthand that hides
  which files inside got .gitignore'd. 4be60e1 shipped
  with `src/data/yfinance_utils.py` silently excluded
  by a `data/` pattern; recovered in fd8ba2e by
  anchoring to `/data/`. The check-ignore step catches
  the gap before push, not after.
- Why .gitignore-matching artefacts hide from status:
  files matching `*.log` and similar gitignore patterns
  (`.mr_v2_run.log` swallowed by `.gitignore:32 *.log`,
  session 7 c823e20) never appear in `git status -s`.
  Phase A must `git check-ignore -v <expected-artefacts>`
  upfront when a WP produces files that may match an
  existing pattern; strict-literal status assertions
  silently pass even when these artefacts are on disk.
- Why step 2 has two modes:
  - SOLO-TERMINAL (default): `git status -s` MUST show
    EXACTLY the declared file list (plus any whitelist-
    gated paths per the rule above). Any other unstaged
    path = halt and reconcile.
  - CONCURRENT (declared in WP prompt GATE): status MUST
    INCLUDE the declared list; other unstaged files are
    permitted iff they are in-flight artifacts of
    another terminal's WP. Discipline preserved via
    explicit-pathspec `git add` (never `git add .`) plus
    a strict step-5 `git diff --cached --name-only`
    showing EXACTLY the declared list. Locked session 6
    (4790939) after five concurrent terminal moves
    exposed the gap.
- Why long commit bodies use $TEMP/mv: bash heredocs in
  Claude Code's Bash tool parser memory-bound at ~500
  characters; bodies over that truncate. Workaround
  proven across c823e20 / a63cb38 / 80f9993:
    1. Write body to `$TEMP/<unique>.txt` (Write tool,
       not heredoc).
    2. AFTER pre-stage `git status -s` + `git add` +
       `git diff --cached --name-only`, `mv` the temp
       file to `.commit-msg.tmp` in the repo root.
    3. `git commit -F .commit-msg.tmp`, then `rm`.
  Critical ordering: `.commit-msg.tmp` is NOT gitignored,
  so the mv MUST land AFTER the strict-literal SOLO
  status assertion — otherwise it appears as `??` and
  breaks the assertion. Banked: add `.commit-msg.tmp`
  to .gitignore so this ordering constraint disappears.

## State files (source of truth)

- `_project_state.md` — scope, locked decisions, current
  WP, open WPs, ENVIRONMENT NOTES.
- `_build_log.md` — every shipped commit with SHA and
  one-paragraph summary.
- `_timeline.md` — append-only session log.
- `_ideas.md` — banked future WPs and design directions.

Reconciled at session close (and mid-session milestones)
via a reconcile prompt at any idle terminal.

## Work package naming

`WP-[AREA]-[DESCRIPTOR]`. Banked WPs live in
`_project_state.md` or `_ideas.md` until executed.
Closed WPs migrate to `_build_log.md` with the commit SHA.

## Identity stamping

Every CC report starts AND ends with:

    TERMINAL: T<n>
    TIMESTAMP: <YYYY-MM-DD HH:MM AEST>

Plus WP at the top and HEAD + STATUS at the bottom
(PASS / FAIL / RECON COMPLETE etc.).

## Communication

- Plain English in chat, technical detail in code blocks.
- Lead with synthesis and judgment — ONE recommended
  path, not option menus.
- Short, direct fragments. Full absolute paths and URLs.
- Browser V-walks on production are definitive over log
  analysis (HTTP 200 ≠ browser PASS).
- Hard refresh / app-kill before V-walking UX-affecting
  deploys.
- Dry-run before any data mutation.
- Investigate before architectural claims — fire Rule 0
  probes, don't speculate.
- Warn proactively about context compaction at natural
  break points.

## What every per-prompt block should still contain

CLAUDE.md covers the standing rules. The prompt itself
only specifies:

- IDENTITY: which terminal, which WP
- GATE: task-specific preconditions
- HANDS-OFF: zones beyond the obvious
- PHASE A: read-only investigation for this task
- PHASE B: execution for this task (after authorisation)
- PASS / FAIL: how to know the WP closed cleanly
- REPORT: any task-specific addition to the default
  report shape
