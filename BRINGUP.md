# BRINGUP.md — StockHub Mac bring-up checklist

> WP-MAC-MIGRATION-TOOLING (2026-09-13). Built off a read-only audit the same
> session that found StockHub has no GB-scale local-data problem: the
> ingested price history (185 ASX tickers + `^AXJO` deep backfill) upserts
> straight to Supabase and never touches local disk. What genuinely only
> exists on this laptop is `.env` (10 keys, no Vercel or other cloud copy),
> the small `results/` backtest-output folder (1.6MB, cheap to rebuild but
> packed anyway), and Claude Code's own per-machine memory folder.
>
> Companion tooling (ported from `C:\Users\admin\tjk-civil`, config-shaped
> for this repo): `scripts/migrate-pack.mjs`, `scripts/migrate-restore.mjs`,
> `scripts/lib/migrate-common.mjs`, `scripts/migrate-pack.config.json`.

**Repo:** https://github.com/Trotzali/StockHub (prod branch `master`)
**This machine's path:** `C:\Users\admin\Projects\StockHub`
**Mac path:** TBD at clone time — Claude Code's memory folder is
recomputed from whatever absolute path the Mac clone lands at
(`computeClaudeProjectKey()` in `scripts/lib/migrate-common.mjs`), not
copied verbatim. Verified against this machine's own live folder
(`C--Users-admin-Projects-StockHub`) — not yet verified against a real
macOS Claude Code install (no Mac available when this was written).

## Fresh-never-resume

Treat the Mac clone as a new machine, not a resumed session. `git clone`
first, restore the pack into that clone, then verify — never try to carry
over a half-set-up Windows working tree by hand. `.venv` in particular does
not survive a manual copy across OSes (binary layout is platform-specific)
— always rebuild it fresh (see "Python venv" below).

## No-MCP / no-hooks note

A fresh clone + fresh Claude Code install on the Mac starts with **zero**
MCP servers registered, and the **global** `~/.claude/settings.json`
(user-level, outside any repo — not part of this project's pack) will
either not exist yet or will still be the Windows one if copied by hand.
Concretely:

- `~/.claude/settings.json`'s current `SessionStart` hook shells to
  PowerShell (`Get-CimInstance Win32_Process ... | Invoke-CimMethod
  -MethodName Terminate`) to kill stray `chrome-devtools-mcp` node
  processes. That command does not exist on macOS — replace it with
  `pkill -f chrome-devtools-mcp || true` before first use, or drop the hook
  if it's not needed yet on the Mac.
- Any MCP servers registered in `~/.claude.json` on this machine do NOT
  travel with a `git clone` or with the migrate-pack — they're
  machine-level, out of scope for this repo's pack. Re-register on the Mac
  if/when needed.
- StockHub itself has no project-local `.claude/` directory (no
  `.claude/settings.local.json`, no project hooks) — nothing repo-side to
  migrate on this front.

## Gotchas

See `CLAUDE.md`'s "Mac migration deltas" section for the full per-rule
breakdown. Summary:

- ~~Norton HTTPS-scanning toggle for supabase-py TLS~~ — **retires on Mac**
  (item 9). Norton doesn't exist there. If a cert error shows up on the
  Mac, inspect the issuer before assuming the same root cause.
- `python` vs `python3` **flips** (item 4): Windows rule says use `python`;
  macOS has no bare `python` on PATH by default — use `python3`.
- `pip install --only-binary :all:` (item 6) — **keep this discipline**,
  but the underlying risk shrinks: macOS arm64 (Apple Silicon) wheel
  coverage on PyPI is generally much better than win_arm64's.
- ASCII-only stdout rule (item 8) — **retires on Mac**. cp1252-crashes is a
  PowerShell-only failure mode; Terminal.app/zsh default to UTF-8.
- No `Set-Content -Encoding utf8` BOM trap on Mac (item 2) — **retires**.
  Standard shell redirection and Python's own writes are UTF-8 without a
  BOM by default on macOS.
- `git commit -F <tempfile>` (item 1) — **unchanged**. Not an OS-specific
  workaround, just avoids shell-quoting problems on any platform.
- LF→CRLF noise on `git add` (item 3) — **likely retires**, driven by
  Windows' `core.autocrlf`; confirm empirically on the first Mac `git add`.
- `psycopg2-binary`/native-PG-driver gap (item 7) — exists *because of*
  item 5's win_arm64 gap. Worth re-evaluating on Mac if it ever matters;
  not a Phase 2 action — supabase-py works fine either way.
- ARM64 wheel-gap list (item 5: psycopg2-binary, psycopg-binary, pyarrow)
  — **re-verify on Mac**, don't assume the win_arm64 gaps carry over.

## Pre-launch check block (run on the Mac before declaring done)

```
git fetch origin
git log -1 --oneline
git status -s
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --only-binary :all: -r requirements.lock
npm install
node scripts/migrate-restore.mjs "/path/to/My Drive/Dev Vault/stockhub/backups/stockhub-migrate-pack-<stamp>.zip.enc"
python scripts/smoke_test_db.py
```

`git status -s` should be clean immediately after clone (restore never
touches anything git tracks — it only ever writes `.env`, `results/`, and
the Claude memory folder). `smoke_test_db.py` printing `PASS` is the real
"did the migration work" signal — it confirms the Supabase REST path
(env vars + supabase-py + the `prices`/`signals`/`stocks` tables) is alive
end-to-end on the new machine, not just a green `pip install`.

## Tooling notes (for whoever runs this next)

- Pack manifest is intentionally short — `.env` (required), `results/`
  (optional), Claude memory (required, tolerates empty/missing). No
  data-fixtures-style items the way tjk-civil needed, because the real
  price history lives in Supabase, not on disk.
- Archive magic header is `SHMPK1` (StockHub's own), deliberately different
  from tjk-civil's `TJKMPK1` — a StockHub pack and a tjk-civil pack can
  never be cross-decrypted-and-misinterpreted; wrong-file attempts fail
  with a clear "bad magic header" error either way.
- `npm audit` flags `adm-zip <=0.6.0` (high severity: a crafted-zip
  4GB-allocation DoS, and a zip-slip symlink path-traversal on extraction).
  Accepted, not fixed by bumping to the breaking `0.6.1`: `migrate-restore.mjs`
  only ever calls `AdmZip` on a buffer that has already passed AES-256-GCM
  *authenticated* decryption — an attacker without the archive password
  can't get a tampered/arbitrary zip anywhere near the vulnerable
  extraction path. Revisit only if this tooling is ever pointed at an
  untrusted zip directly.
- Nightly `--auto` scheduling (tjk-civil's "continuous protection" —
  Task Scheduler / launchd) is **not** wired up yet. Packing today is a
  manual `node scripts/migrate-pack.mjs` run. Banked as
  `WP-INFRA-MIGRATE-SCHEDULE` in `_ideas.md` — natural follow-up, not part
  of this WP's authorization.

## Ready-when

- [ ] `git clone` done, `git log -1` matches GitHub's `master` HEAD.
- [ ] `.env` restored (10 keys — see `_project_state.md` / the 2026-09-13
      audit) and `scripts/smoke_test_db.py` prints `PASS` against Supabase.
- [ ] Claude Code memory folder present at the Mac's own path-keyed
      location (`~/.claude/projects/<mac-path-key>/memory/`) with
      `MEMORY.md` — **note:** as of the 2026-09-13 audit the folder exists
      but is EMPTY on this machine (no memory written yet for this
      project), so re-check contents right before the real pack run rather
      than assuming there's something to restore.
- [ ] `python3 -m venv .venv` rebuilt fresh (not copied) and
      `requirements.lock` installs clean with `--only-binary :all:`.
- [ ] `npm install` clean (archiver + adm-zip only — this `package.json`
      has no other job).
- [ ] `results/` present or regenerated (rerun the relevant
      `scripts/backtest_*.py` — cheap, no external API calls needed, reads
      straight from Supabase).
- [ ] `~/.claude/settings.json` `SessionStart` hook fixed for macOS (or
      removed) before relying on it.
- [ ] No scheduled job to migrate — `WP-INFRA-SCHEDULER` (daily
      `fetch_yfinance.py` post-close) is banked in `_ideas.md`, never
      shipped on Windows, nothing to port.
