#!/usr/bin/env node
// WP-MAC-MIGRATION-TOOLING -- migrate-pack.mjs
//
// Ported from C:\Users\admin\tjk-civil (2026-09-13 audit) -- logic
// unmodified except the output filename prefix (tjk-civil- -> stockhub-)
// and the console header text. Everything else (staging, zip, encrypt,
// retention) is the generic, config-shaped implementation.
//
// Runs on Windows (or any OS -- no bash-isms, pure Node). Collects the files
// that would NOT survive a fresh `git clone` (secrets, real data, Claude
// Code's own per-machine memory) into a staging folder, zips it, and
// encrypts the zip with a password using AES-256-GCM + scrypt (real,
// authenticated encryption -- see scripts/lib/migrate-common.mjs's own
// comment for why this beats shelling out to a weaker `zip -e`).
//
// Usage:
//   node scripts/migrate-pack.mjs             interactive one-off pack (prompts for password)
//   node scripts/migrate-pack.mjs --dry       print the exact plan, write nothing
//   node scripts/migrate-pack.mjs --auto      non-interactive: password from
//                                             the configured password file,
//                                             packs straight to the vault,
//                                             rotates retention
//   node scripts/migrate-pack.mjs --set-password
//                                             prompt once (with confirm),
//                                             write the auto-mode password
//                                             file, then exit (no pack run)
//
// Idempotent: every run is a fresh, independent pack. Re-running never
// corrupts or depends on a prior run's state (retention just deletes old
// archives past the configured count).

import { existsSync, statSync, readdirSync, mkdirSync, rmSync, cpSync, createWriteStream, readFileSync, writeFileSync, unlinkSync } from "node:fs";
import { join, basename } from "node:path";
import { tmpdir } from "node:os";
import { createRequire } from "node:module";

import {
  findRepoRoot, loadConfig, getPackItems, passwordFileExclusionNote,
  EXCLUDED_JUNK_CATEGORIES, resolveVaultPaths, melbourneStamp,
  promptNewPassword, promptPassword, readPasswordFile, writePasswordFile,
  encryptBuffer, formatBytes,
} from "./lib/migrate-common.mjs";

const require = createRequire(import.meta.url);
const archiver = require("archiver");

const args = process.argv.slice(2);
const DRY = args.includes("--dry");
const AUTO = args.includes("--auto");
const SET_PASSWORD = args.includes("--set-password");
const HELP = args.includes("--help") || args.includes("-h");
const outputFlagIdx = args.indexOf("--output");
const OUTPUT_OVERRIDE = outputFlagIdx >= 0 ? args[outputFlagIdx + 1] : null;

if (HELP) {
  console.log(`
migrate-pack.mjs -- pack the files a git clone won't carry over

  (no flags)       interactive pack, prompts for a fresh password each run
  --dry            print the plan, write nothing
  --auto           non-interactive: password from the configured password
                   file, packs to the vault, rotates retention
  --set-password   prompt (with confirm) and write the auto-mode password
                   file, then exit
  --output <dir>   write the archive to <dir> instead of the resolved vault
                   backups dir (skips Drive detection entirely) -- for
                   testing/verification without touching the real vault
  --help           this message
`);
  process.exit(0);
}

function dirSize(p) {
  const st = statSync(p);
  if (st.isFile()) return st.size;
  let total = 0;
  for (const entry of readdirSync(p)) total += dirSize(join(p, entry));
  return total;
}

function zipDirectory(srcDir, outZipPath) {
  return new Promise((resolve, reject) => {
    const output = createWriteStream(outZipPath);
    const archive = archiver("zip", { zlib: { level: 9 } });
    output.on("close", resolve);
    archive.on("error", reject);
    archive.pipe(output);
    archive.directory(srcDir, false);
    archive.finalize();
  });
}

async function main() {
  const repoRoot = findRepoRoot();
  const cfg = loadConfig(repoRoot);
  const repoAbsPath = repoRoot; // findRepoRoot() already returns the absolute path

  if (SET_PASSWORD) {
    const pw = await promptNewPassword();
    const pwPath = join(repoRoot, cfg.passwordFile);
    if (DRY) {
      console.log(`[DRY] Would write password file: ${pwPath}`);
    } else {
      writePasswordFile(pwPath, pw);
      console.log(`Password file written: ${pwPath} (chmod 600 where supported)`);
      console.log(`Make sure ${cfg.passwordFile} is in .gitignore (it should already be -- this WP added it).`);
    }
    return;
  }

  const ctx = { repoRoot, repoAbsPath };
  const items = getPackItems(ctx);

  console.log(`Repo root:  ${repoRoot}`);
  console.log(`Config:     scripts/migrate-pack.config.json (vault "${cfg.vaultRoot}/${cfg.project}")`);
  console.log(DRY ? "Mode:       DRY RUN -- nothing will be written\n" : AUTO ? "Mode:       --auto (non-interactive)\n" : "Mode:       interactive\n");

  // ── Resolve each item, size it, split present/missing ──
  const present = [];
  const missing = [];
  for (const item of items) {
    const src = item.resolve();
    if (existsSync(src)) {
      present.push({ ...item, src, size: dirSize(src) });
    } else {
      missing.push(item);
    }
  }

  console.log("PACK MANIFEST -- will be packed:");
  for (const p of present) {
    console.log(`  [${p.type}] ${p.label.padEnd(48)} ${formatBytes(p.size).padStart(10)}   <- ${p.src}`);
  }
  const totalSize = present.reduce((a, p) => a + p.size, 0);
  console.log(`  TOTAL: ${formatBytes(totalSize)}\n`);

  console.log("DELIBERATELY EXCLUDED (junk -- per the 2026-09-13 migration audit):");
  for (const cat of EXCLUDED_JUNK_CATEGORIES) console.log(`  - ${cat}`);
  console.log(`  - ${passwordFileExclusionNote(cfg)}`);
  console.log();

  if (missing.length) {
    console.log("WARNING -- expected but missing (not fatal, just flagged):");
    for (const m of missing) {
      console.log(`  ${m.required ? "[REQUIRED]" : "[optional]"} ${m.label} -- not found, skipped`);
    }
    console.log();
  }

  const required_missing = missing.filter((m) => m.required);
  if (required_missing.length && !DRY) {
    console.log("Continuing despite missing REQUIRED item(s) above -- pack will just be incomplete for those.");
    console.log("(Not treated as fatal: e.g. the Claude memory folder legitimately won't exist yet on a brand-new machine/session.)\n");
  }

  let backupsDir;
  if (OUTPUT_OVERRIDE) {
    backupsDir = OUTPUT_OVERRIDE;
    console.log(`--output override: writing to ${backupsDir} (Drive detection skipped -- NOT the real vault).\n`);
  } else {
    const { mount, backupsDir: resolved } = resolveVaultPaths(repoRoot, cfg);
    backupsDir = resolved;
    if (mount.found) {
      console.log(`Drive for Desktop detected (${mount.platform}): ${mount.path}`);
    } else {
      console.log(`WARNING: Google Drive for Desktop NOT detected on this machine (checked ${mount.platform === "win32" ? "drive letters C:-Z: for a \\My Drive folder" : "~/Library/CloudStorage for a GoogleDrive-* folder"}).`);
      console.log(`         Falling back to a LOCAL directory -- this pack will NOT be cloud-synced until Drive for Desktop is installed and the config/mount is re-detected.`);
    }
    console.log(`Backups dir: ${backupsDir}\n`);
  }

  if (DRY) {
    console.log("[DRY] Would create staging dir, zip it, encrypt to:");
    console.log(`[DRY]   ${join(backupsDir, `stockhub-migrate-pack-${melbourneStamp()}.zip.enc`)}`);
    console.log(`[DRY] Would then enforce retention (keep newest ${cfg.retentionCount} in ${backupsDir}).`);
    console.log("\n[DRY] Nothing written. Re-run without --dry to actually pack.");
    return;
  }

  // ── Password ──
  let password;
  if (AUTO) {
    const pwPath = join(repoRoot, cfg.passwordFile);
    password = readPasswordFile(pwPath);
    if (!password) {
      console.error(`FATAL: --auto needs a password file at ${pwPath} -- create one first with:`);
      console.error(`  node scripts/migrate-pack.mjs --set-password`);
      process.exit(1);
    }
  } else {
    password = await promptNewPassword();
  }

  // ── Stage ──
  const stamp = melbourneStamp();
  const stagingDir = join(tmpdir(), `stockhub-migrate-pack-${stamp}`);
  mkdirSync(stagingDir, { recursive: true });
  for (const p of present) {
    const dest = join(stagingDir, p.destRel);
    mkdirSync(join(dest, ".."), { recursive: true });
    cpSync(p.src, dest, { recursive: true });
  }

  // ── Zip ──
  const plainZipPath = join(tmpdir(), `stockhub-migrate-pack-${stamp}.zip`);
  await zipDirectory(stagingDir, plainZipPath);
  const plainSize = statSync(plainZipPath).size;

  // ── Encrypt ──
  const plainBuf = readFileSync(plainZipPath);
  const encBuf = encryptBuffer(plainBuf, password);
  mkdirSync(backupsDir, { recursive: true });
  const outName = `stockhub-migrate-pack-${stamp}.zip.enc`;
  const outPath = join(backupsDir, outName);
  writeFileSync(outPath, encBuf);

  // ── Cleanup staging + plain zip (never leave the unencrypted zip on disk) ──
  rmSync(stagingDir, { recursive: true, force: true });
  unlinkSync(plainZipPath);

  console.log(`Packed:    ${formatBytes(plainSize)} plain -> ${formatBytes(encBuf.length)} encrypted`);
  console.log(`Written:   ${outPath}`);

  // ── Retention ──
  const existing = readdirSync(backupsDir)
    .filter((f) => f.startsWith("stockhub-migrate-pack-") && f.endsWith(".zip.enc"))
    .map((f) => ({ name: f, path: join(backupsDir, f), mtime: statSync(join(backupsDir, f)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime);
  const toDelete = existing.slice(cfg.retentionCount);
  for (const f of toDelete) {
    unlinkSync(f.path);
    console.log(`Retention: deleted ${f.name} (kept newest ${cfg.retentionCount})`);
  }
  if (!toDelete.length) {
    console.log(`Retention: ${existing.length}/${cfg.retentionCount} archives in ${backupsDir} -- nothing to delete.`);
  }

  console.log("\nDone.");
}

main().catch((err) => {
  console.error("FATAL:", err.message);
  process.exit(1);
});
