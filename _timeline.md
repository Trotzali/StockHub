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
