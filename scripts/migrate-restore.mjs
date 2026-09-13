#!/usr/bin/env node
// WP-MAC-MIGRATION-TOOLING -- migrate-restore.mjs
//
// Ported from C:\Users\admin\tjk-civil (2026-09-13 audit). Two things
// dropped relative to the tjk-civil original, both confirmed inapplicable
// by that audit rather than just omitted:
//   - The 7-script hardcoded-path portability check: StockHub's tracked
//     code has zero "C:\Users\admin"-style hardcoded paths (grep across
//     src/ and scripts/ came back empty -- the only hits were narrative
//     mentions in the four markdown state files). Nothing to patch.
//   - launch-chrome-debug.sh generation: StockHub has no repo-tracked
//     Chrome-debug launch script to give a macOS twin to.
// MANUAL_ENV_KEYS and the end-of-run manual-steps checklist are StockHub's
// own (10 keys, no Vercel, python3/pip not npm).
//
// Runs on macOS (pure Node -- no bash-isms -- so it also runs unchanged on
// Windows/Linux if ever needed for testing). Takes a migrate-pack.mjs
// archive and unpacks it into a freshly-cloned target repo: .env and
// results/ to their normal repo-relative locations, Claude Code's own
// per-machine memory to the NEW path-keyed project folder computed from the
// target clone's own absolute path.
//
// Usage:
//   node scripts/migrate-restore.mjs <pack.zip.enc>              restore into the repo this script lives in
//   node scripts/migrate-restore.mjs <pack.zip.enc> --target DIR restore into DIR instead (testing / explicit target)
//   node scripts/migrate-restore.mjs <pack.zip.enc> --dry        decrypt + plan only, write nothing
//
// Idempotent: safe to re-run. Files identical to what's already there are
// left alone and reported UNCHANGED; only genuinely different/missing files
// are written.

import { existsSync, readFileSync, writeFileSync, mkdirSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { createRequire } from "node:module";

import {
  findRepoRoot, loadConfig, claudeMemoryDir,
  computeClaudeProjectKey, promptPassword, decryptBuffer, formatBytes,
} from "./lib/migrate-common.mjs";

const require = createRequire(import.meta.url);
const AdmZip = require("adm-zip");

const args = process.argv.slice(2);
const DRY = args.includes("--dry");
const HELP = args.includes("--help") || args.includes("-h");
const targetFlagIdx = args.indexOf("--target");
const TARGET_OVERRIDE = targetFlagIdx >= 0 ? args[targetFlagIdx + 1] : null;
const packPath = args.find((a) => !a.startsWith("--") && a !== TARGET_OVERRIDE);

if (HELP || !packPath) {
  console.log(`
migrate-restore.mjs -- unpack a migrate-pack.mjs archive into a fresh clone

  node scripts/migrate-restore.mjs <pack.zip.enc>              restore into the repo this script lives in
  node scripts/migrate-restore.mjs <pack.zip.enc> --target DIR restore into DIR instead
  node scripts/migrate-restore.mjs <pack.zip.enc> --dry        decrypt + plan only, write nothing
`);
  process.exit(packPath ? 0 : 1);
}

// The manual env keys from the 2026-09-13 audit's Phase 1 §2 -- all 10 keys
// this project uses. Unlike tjk-civil, StockHub has NO Vercel (or any other
// cloud secrets store) -- these exist ONLY in the pack and on whichever
// machine wrote it, so this checklist is the one real verification that
// matters here.
const MANUAL_ENV_KEYS = [
  "SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY",
  "SUPABASE_DB_HOST", "SUPABASE_DB_PORT", "SUPABASE_DB_NAME",
  "SUPABASE_DB_USER", "SUPABASE_DB_PASSWORD",
  "FINNHUB_API_KEY", "ALPHA_VANTAGE_API_KEY",
];

function writeIfDifferent(destPath, data, log) {
  const exists = existsSync(destPath);
  if (exists) {
    const current = readFileSync(destPath);
    if (Buffer.isBuffer(data) ? current.equals(data) : current.toString("utf8") === data) {
      log.push({ status: "UNCHANGED", path: destPath });
      return;
    }
  }
  if (!DRY) {
    mkdirSync(dirname(destPath), { recursive: true });
    writeFileSync(destPath, data);
  }
  log.push({ status: exists ? "UPDATED" : "CREATED", path: destPath });
}

async function main() {
  const packAbsPath = packPath;
  if (!existsSync(packAbsPath)) {
    console.error(`FATAL: pack file not found: ${packAbsPath}`);
    process.exit(1);
  }

  const targetRoot = TARGET_OVERRIDE ?? findRepoRoot();
  if (!existsSync(join(targetRoot, ".git"))) {
    console.error(`FATAL: ${targetRoot} doesn't look like a git repo (no .git) -- pass --target <freshly-cloned-repo-dir>.`);
    process.exit(1);
  }
  loadConfig(targetRoot); // validates scripts/migrate-pack.config.json is present/well-formed

  console.log(`Pack:       ${packAbsPath}`);
  console.log(`Target:     ${targetRoot}`);
  console.log(DRY ? "Mode:       DRY RUN -- will decrypt + plan, write nothing\n" : "Mode:       restore\n");

  const password = await promptPassword("Archive password: ");
  const encBuf = readFileSync(packAbsPath);
  let plainZip;
  try {
    plainZip = decryptBuffer(encBuf, password);
  } catch (e) {
    console.error(`FATAL: could not decrypt (${e.message}) -- wrong password, or not a migrate-pack archive.`);
    process.exit(1);
  }
  console.log(`Decrypted OK: ${formatBytes(encBuf.length)} -> ${formatBytes(plainZip.length)}\n`);

  const zip = new AdmZip(plainZip);
  const entries = zip.getEntries().filter((e) => !e.isDirectory);

  // ── Restore each entry to its target destination ──
  const memDir = claudeMemoryDir(targetRoot);
  const log = [];
  for (const entry of entries) {
    const name = entry.entryName;
    const destPath = name.startsWith("claude-memory/")
      ? join(memDir, name.slice("claude-memory/".length))
      : join(targetRoot, name);
    writeIfDifferent(destPath, entry.getData(), log);
  }

  console.log("RESTORE:");
  for (const l of log) console.log(`  [${l.status.padEnd(9)}] ${l.path}`);
  console.log();

  // ── Verification checklist ──
  console.log("===============================================================");
  console.log("VERIFICATION CHECKLIST");
  console.log("===============================================================\n");

  const envPath = join(targetRoot, ".env");
  if (existsSync(envPath)) {
    const envContent = readFileSync(envPath, "utf8");
    const foundKeys = new Set(
      envContent.split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("#") && l.includes("="))
        .map((l) => l.slice(0, l.indexOf("=")).trim())
    );
    console.log("env keys (from the 2026-09-13 audit's full key list -- no Vercel, no other cloud copy):");
    for (const k of MANUAL_ENV_KEYS) {
      console.log(`  [${foundKeys.has(k) ? "present" : "MISSING"}] ${k}`);
    }
  } else {
    console.log(`.env not present at ${envPath} (pack may not have included it, or restore was --dry) -- MISSING, all ${MANUAL_ENV_KEYS.length} keys unverified.`);
  }
  console.log();

  const memMdPath = join(memDir, "MEMORY.md");
  const claudeKey = computeClaudeProjectKey(targetRoot);
  console.log(`Claude memory: project key computed as "${claudeKey}"`);
  console.log(`  target dir: ${memDir}`);
  console.log(`  MEMORY.md ${existsSync(memMdPath) ? "present" : DRY ? "would be installed (DRY)" : "MISSING"}`);
  if (existsSync(memDir)) {
    const count = readdirSync(memDir).filter((f) => f.endsWith(".md")).length;
    console.log(`  ${count} .md fact file(s) present`);
  }
  console.log();

  console.log("Manual steps still owed (nothing here can be scripted -- see BRINGUP.md):");
  console.log("  1. ~/.claude/settings.json (user-level, NOT in this repo) -- its SessionStart hook");
  console.log("     shells to PowerShell to kill stray chrome-devtools-mcp processes; that command");
  console.log("     doesn't exist on macOS. Replace it with something like:");
  console.log(`       pkill -f chrome-devtools-mcp || true`);
  console.log("  2. Claude Code: fresh login expected -- ~/.claude/.credentials.json was deliberately");
  console.log("     never packed (never move auth credentials between machines).");
  console.log("  3. python3 -m venv .venv, then:");
  console.log("       python3 -m pip install --only-binary :all: -r requirements.lock");
  console.log("     (.venv is never packed -- platform-specific binaries anyway; rebuild fresh, don't");
  console.log("     expect the Windows .venv to work here.)");
  console.log("  4. npm install (this package.json's only job is archiver+adm-zip for this tooling).");
  console.log("  5. Run scripts/smoke_test_db.py -- PASS confirms the Supabase REST path (env vars +");
  console.log("     supabase-py + the prices/signals/stocks tables) is alive end-to-end on this machine.");
  console.log("     This is the real 'did the migration work' signal, not just a green pip install.");
  console.log("  6. No Vercel step -- this project has none. All 10 env keys above exist ONLY in this");
  console.log("     pack and on the machine that wrote it; there is no second cloud copy to fall back on.");
  console.log();

  console.log(DRY ? "[DRY] Nothing written. Re-run without --dry to actually restore." : "Done.");
}

main().catch((err) => {
  console.error("FATAL:", err.message);
  process.exit(1);
});
