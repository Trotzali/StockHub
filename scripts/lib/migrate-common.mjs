// WP-MAC-MIGRATION-TOOLING -- shared helpers for scripts/migrate-pack.mjs and
// scripts/migrate-restore.mjs. Pure Node (fs/path/os/crypto/readline only --
// no bash-isms, no third-party crypto deps), so both scripts run identically
// on Windows and macOS.
//
// Ported from C:\Users\admin\tjk-civil (2026-09-13 audit) -- reused
// unmodified except getPackItems() (StockHub's own pack manifest, see below)
// and EXCLUDED_JUNK_CATEGORIES (StockHub's own junk list). Everything else
// -- path-key computation, encryption, Drive detection, password prompts --
// is generic and untouched, exactly per the reference implementation's own
// "config-shaped, drop into another repo" design.

import { existsSync, readFileSync, readdirSync, writeFileSync, chmodSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir, platform } from "node:os";
import { fileURLToPath } from "node:url";
import {
  randomBytes,
  scryptSync,
  createCipheriv,
  createDecipheriv,
} from "node:crypto";

// ─────────────────────────────────────────────────────────────────────────
// Repo root / config
// ─────────────────────────────────────────────────────────────────────────

// Walk up from this file's own directory looking for .git -- correct
// regardless of the cwd the script was invoked from, and regardless of OS
// (no reliance on process.cwd()).
export function findRepoRoot() {
  let dir = dirname(fileURLToPath(import.meta.url)); // scripts/lib
  for (let i = 0; i < 10; i++) {
    if (existsSync(join(dir, ".git"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  throw new Error("Could not find repo root (no .git found walking up from " + import.meta.url + ")");
}

export function loadConfig(repoRoot) {
  const configPath = join(repoRoot, "scripts", "migrate-pack.config.json");
  if (!existsSync(configPath)) {
    throw new Error(`Missing config: ${configPath}`);
  }
  const cfg = JSON.parse(readFileSync(configPath, "utf8"));
  const required = ["vaultRoot", "project", "backupsSubfolder", "dataSubfolder", "retentionCount", "passwordFile", "fallbackLocalDir"];
  for (const key of required) {
    if (cfg[key] === undefined) throw new Error(`${configPath} missing required key "${key}"`);
  }
  return cfg;
}

// ─────────────────────────────────────────────────────────────────────────
// Claude Code project-memory path-key computation
//
// Verified empirically against every existing ~/.claude/projects/* directory
// on this machine (9 real examples spanning spaces, hyphens, mixed-case
// drive letters, incl. this repo's own "C--Users-admin-Projects-StockHub" --
// confirmed against the live folder in the 2026-09-13 audit): the key is
// the absolute repo path with every character that is not [A-Za-z0-9]
// replaced 1-for-1 with "-" (no collapsing runs, case preserved verbatim).
// e.g. "C:\Users\admin\Projects\StockHub" (Windows) ->
// "C--Users-admin-Projects-StockHub"; "/Users/troy/StockHub" (macOS) would
// become "-Users-troy-StockHub". NOT independently confirmed against a real
// macOS Claude Code install (no Mac available in this session) -- flagged
// in BRINGUP.md as needing first-real-run verification there.
// ─────────────────────────────────────────────────────────────────────────
export function computeClaudeProjectKey(absPath) {
  return absPath.replace(/[^A-Za-z0-9]/g, "-");
}

export function claudeMemoryDir(absRepoPath) {
  return join(homedir(), ".claude", "projects", computeClaudeProjectKey(absRepoPath), "memory");
}

// ─────────────────────────────────────────────────────────────────────────
// Pack item manifest -- the single source of truth both scripts read from.
// resolve(ctx) returns the absolute source path; destRel is where it lands
// inside the archive (and where restore puts it back, repo-root-relative
// except the "claude-memory" item which is home-relative).
//
// StockHub's own manifest (2026-09-13 audit) -- deliberately short: this
// project has no GB-scale local data (ingested price history lives in
// Supabase, never touches disk -- see BRINGUP.md), so there's no
// data-fixtures/xlsx-style item list the way tjk-civil needed.
// ─────────────────────────────────────────────────────────────────────────
export function getPackItems(ctx) {
  // ctx = { repoRoot, repoAbsPath }
  return [
    { id: "env", label: ".env", type: "file", required: true,
      resolve: () => join(ctx.repoRoot, ".env"), destRel: ".env" },
    { id: "results", label: "results/ (backtest outputs -- cheap to rebuild, packed anyway as cheap insurance)", type: "dir", required: false,
      resolve: () => join(ctx.repoRoot, "results"), destRel: "results" },
    { id: "claude-memory", label: "Claude Code memory/ (MEMORY.md + all fact files)", type: "dir", required: true,
      resolve: () => claudeMemoryDir(ctx.repoAbsPath), destRel: "claude-memory" },
  ];
}

// Deliberately NEVER packed, whatever the config says -- see
// docs/migration.md (tjk-civil) "Why the password file is never inside its
// own pack" for the reasoning (this repo doesn't have its own copy of that
// doc yet -- BRINGUP.md carries the equivalent note for StockHub). Reported
// in the manifest as an explicit, named exclusion, not silently dropped.
export function passwordFileExclusionNote(cfg) {
  return `${cfg.passwordFile} (the --auto decryption password itself -- packing a password inside the archive it decrypts is circular and defeats the point; carry it over separately, out of band)`;
}

// Static, human-readable -- mirrors the 2026-09-13 audit's own StockHub
// findings exactly, printed so the manifest states what was deliberately
// left out and why, not just what was packed.
export const EXCLUDED_JUNK_CATEGORIES = [
  ".venv/ -- Python virtualenv, rebuild via `python3 -m venv .venv` + `pip install --only-binary :all: -r requirements.lock` (see BRINGUP.md)",
  "scripts/__pycache__/, src/__pycache__/, src/backtest/__pycache__/, src/data/__pycache__/ -- Python bytecode cache, auto-regenerated",
  "Ingested price history (185 ASX tickers + ^AXJO deep backfill) -- never touches local disk; lives in Supabase's prices/signals/stocks tables, reachable once .env is restored",
];

// ─────────────────────────────────────────────────────────────────────────
// Drive for Desktop mount detection
// ─────────────────────────────────────────────────────────────────────────
export function detectDriveMount(cfg) {
  const plat = platform();
  const candidates = cfg.driveMountCandidates?.[plat] ?? [];

  if (plat === "win32") {
    for (const drive of candidates) {
      const p = join(drive + "\\", "My Drive");
      if (existsSync(p)) return { found: true, path: p, platform: plat };
    }
    // Fall back to scanning C..Z if the config list didn't hit (still cheap --
    // existsSync, no traversal).
    for (const code of "CDEFGHIJKLMNOPQRSTUVWXYZ") {
      const p = `${code}:\\My Drive`;
      if (existsSync(p)) return { found: true, path: p, platform: plat };
    }
    return { found: false, path: null, platform: plat };
  }

  if (plat === "darwin") {
    for (const base of candidates) {
      const dir = base.replace(/^~/, homedir());
      if (!existsSync(dir)) continue;
      let entries = [];
      try { entries = readdirSync(dir); } catch { continue; }
      const match = entries.find((e) => e.startsWith("GoogleDrive-"));
      if (match) {
        const p = join(dir, match, "My Drive");
        if (existsSync(p)) return { found: true, path: p, platform: plat };
      }
    }
    return { found: false, path: null, platform: plat };
  }

  return { found: false, path: null, platform: plat };
}

export function resolveVaultPaths(repoRoot, cfg) {
  const mount = detectDriveMount(cfg);
  const root = mount.found ? mount.path : join(repoRoot, cfg.fallbackLocalDir);
  return {
    mount,
    vaultRoot: root,
    backupsDir: join(root, cfg.vaultRoot, cfg.project, cfg.backupsSubfolder),
    dataDir: join(root, cfg.vaultRoot, cfg.project, cfg.dataSubfolder),
  };
}

// ─────────────────────────────────────────────────────────────────────────
// Melbourne timestamp -- kept from the tjk-civil original for filename
// sort-order consistency across both repos' packs; StockHub's own reports
// stamp in AEST too (see CLAUDE.md Identity stamping), so this lines up.
// ─────────────────────────────────────────────────────────────────────────
export function melbourneStamp(date = new Date()) {
  const dtf = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Australia/Melbourne",
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  });
  const p = Object.fromEntries(dtf.formatToParts(date).map((x) => [x.type, x.value]));
  return `${p.year}${p.month}${p.day}-${p.hour}${p.minute}${p.second}`;
}

// Non-TTY fallback line reader -- a persistent module-level buffer, NOT
// readline.createInterface. Deliberate: creating+closing a fresh readline
// Interface on the same piped process.stdin for each of two sequential
// prompts (password, then confirm) loses the second line in practice --
// closing the first interface can drop already-buffered-but-undelivered
// bytes before a second interface attaches. A persistent buffer across
// calls sidesteps that entirely.
let _nonTtyBuffer = "";
function readLineFromStdinNonTTY() {
  return new Promise((resolve) => {
    function tryResolve() {
      const idx = _nonTtyBuffer.indexOf("\n");
      if (idx < 0) return false;
      const line = _nonTtyBuffer.slice(0, idx).replace(/\r$/, "");
      _nonTtyBuffer = _nonTtyBuffer.slice(idx + 1);
      cleanup();
      resolve(line);
      return true;
    }
    function onData(chunk) { _nonTtyBuffer += chunk; tryResolve(); }
    function onEnd() { const line = _nonTtyBuffer; _nonTtyBuffer = ""; cleanup(); resolve(line); }
    function cleanup() {
      process.stdin.removeListener("data", onData);
      process.stdin.removeListener("end", onEnd);
    }
    process.stdin.setEncoding("utf8");
    if (tryResolve()) return; // already-buffered line from a prior call
    process.stdin.on("data", onData);
    process.stdin.on("end", onEnd);
    process.stdin.resume();
  });
}

// ─────────────────────────────────────────────────────────────────────────
// Password prompt -- masked when stdin is a TTY, plainly-flagged fallback
// when it isn't. No dependency: standard raw-mode stdin recipe.
// ─────────────────────────────────────────────────────────────────────────
export function promptPassword(query) {
  return new Promise((resolve, reject) => {
    const stdin = process.stdin;
    if (!stdin.isTTY) {
      // Non-interactive context (e.g. piped input in a test harness) -- no
      // masking possible; read one line plainly rather than hang forever.
      process.stdout.write(query + " (WARNING: input not masked, no TTY) ");
      readLineFromStdinNonTTY().then((line) => {
        process.stdout.write(line + "\n");
        resolve(line);
      });
      return;
    }
    process.stdout.write(query);
    stdin.setRawMode(true);
    stdin.resume();
    stdin.setEncoding("utf8");
    let input = "";
    const onData = (char) => {
      if (char === "\n" || char === "\r" || char === "\u0004") {
        cleanup();
        process.stdout.write("\n");
        resolve(input);
      } else if (char === "\u0003") {
        cleanup();
        process.stdout.write("\n");
        reject(new Error("Cancelled (Ctrl-C)"));
      } else if (char === "\u007f" || char === "\b") {
        input = input.slice(0, -1);
      } else {
        input += char;
      }
    };
    function cleanup() {
      stdin.setRawMode(false);
      stdin.pause();
      stdin.removeListener("data", onData);
    }
    stdin.on("data", onData);
  });
}

export async function promptNewPassword() {
  const MIN_LEN = 12;
  for (;;) {
    const pw1 = await promptPassword("New archive password: ");
    if (pw1.length < MIN_LEN) {
      console.log(`  Too short (${pw1.length} chars) -- use at least ${MIN_LEN} for AES-256/scrypt to mean anything. Try again.`);
      continue;
    }
    const pw2 = await promptPassword("Confirm password: ");
    if (pw1 !== pw2) {
      console.log("  Passwords did not match -- try again.");
      continue;
    }
    return pw1;
  }
}

export function readPasswordFile(path) {
  if (!existsSync(path)) return null;
  const raw = readFileSync(path, "utf8").trim();
  return raw.length ? raw : null;
}

export function writePasswordFile(path, password) {
  writeFileSync(path, password + "\n", { encoding: "utf8" });
  try { chmodSync(path, 0o600); } catch { /* best-effort -- no-op on Windows */ }
}

// ─────────────────────────────────────────────────────────────────────────
// Encryption -- AES-256-GCM (authenticated: tamper/wrong-password both throw
// on decrypt, never silently return garbage) with a scrypt-derived key.
// Pure node:crypto, no third-party lib and no shelling out to 7z/zip --
// genuinely strong, not the legacy ZipCrypto a plain `zip -e` would give you.
//
// File format: MAGIC(7) | VERSION(1) | salt(16) | iv(12) | authTag(16) | ciphertext
// Buffer-based (not streamed) -- fine for this use case (.env, backtest
// CSVs, memory markdown -- single-digit MB, not GBs); keeps the
// header/tag framing simple and unambiguous to get right.
// ─────────────────────────────────────────────────────────────────────────
const MAGIC = Buffer.from("SHMPK1", "ascii"); // 6 bytes -- "StockHub Migrate PacK v1"
const VERSION = Buffer.from([1]);
const SCRYPT_OPTS = { N: 32768, r: 8, p: 1, maxmem: 128 * 1024 * 1024 };

export function encryptBuffer(plainBuf, password) {
  const salt = randomBytes(16);
  const iv = randomBytes(12);
  const key = scryptSync(password, salt, 32, SCRYPT_OPTS);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const ciphertext = Buffer.concat([cipher.update(plainBuf), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([MAGIC, VERSION, salt, iv, tag, ciphertext]);
}

export function decryptBuffer(encBuf, password) {
  let offset = 0;
  const magic = encBuf.subarray(offset, offset + MAGIC.length); offset += MAGIC.length;
  if (!magic.equals(MAGIC)) {
    throw new Error("Not a valid migrate-pack archive (bad magic header) -- wrong file?");
  }
  const version = encBuf[offset]; offset += 1;
  if (version !== 1) throw new Error(`Unsupported pack format version ${version}`);
  const salt = encBuf.subarray(offset, offset + 16); offset += 16;
  const iv = encBuf.subarray(offset, offset + 12); offset += 12;
  const tag = encBuf.subarray(offset, offset + 16); offset += 16;
  const ciphertext = encBuf.subarray(offset);
  const key = scryptSync(password, salt, 32, SCRYPT_OPTS);
  const decipher = createDecipheriv("aes-256-gcm", key, iv);
  decipher.setAuthTag(tag);
  // Throws (bad auth tag) on a wrong password or any tampering -- never
  // silently returns corrupted plaintext.
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]);
}

// ─────────────────────────────────────────────────────────────────────────
// Small formatting helper shared by both scripts' manifest printing.
// ─────────────────────────────────────────────────────────────────────────
export function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  const units = ["KB", "MB", "GB"];
  let v = n / 1024;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(1)} ${units[i]}`;
}
