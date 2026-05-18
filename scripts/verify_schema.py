"""WP-INFRA-SCHEMA-DRIFT-SCRIPT: Verify deployed Supabase schema vs migration.

Reads expected schema (hardcoded below) and queries Supabase via the
PostgREST OpenAPI endpoint (GET /rest/v1/ with
Accept: application/openapi+json) for the actual deployed schema.
Diffs by column presence, PostgREST native type (format), NOT NULL
(required), and PK membership (parsed from the column description
<pk/> marker).

Scope (v1): presence, format, required, PK only.
Deferred (would-be WP-INFRA-SCHEMA-DRIFT-V2):
  - defaults (PostgREST-lossy for serials; brittle for now())
  - indexes, triggers, CHECK constraints, FK targets (not in OpenAPI)
  - numeric precision/scale (PostgREST drops it)

Usage: python scripts/verify_schema.py
Exit: 0 = SCHEMA CLEAN, 1 = SCHEMA DRIFT DETECTED.
"""
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# Source of truth: migrations/001_initial_schema.sql
# Keep this dict in sync with that file. Any migration change requires
# a paired update here (or this script will surface drift).
EXPECTED: dict[str, dict[str, dict[str, object]]] = {
    "stocks": {
        "ticker":     {"format": "text",                     "required": True,  "pk": True},
        "name":       {"format": "text",                     "required": True,  "pk": False},
        "exchange":   {"format": "text",                     "required": True,  "pk": False},
        "sector":     {"format": "text",                     "required": False, "pk": False},
        "industry":   {"format": "text",                     "required": False, "pk": False},
        "market_cap": {"format": "numeric",                  "required": False, "pk": False},
        "is_active":  {"format": "boolean",                  "required": True,  "pk": False},
        "added_at":   {"format": "timestamp with time zone", "required": True,  "pk": False},
        "updated_at": {"format": "timestamp with time zone", "required": True,  "pk": False},
    },
    "prices": {
        "ticker":     {"format": "text",                     "required": True,  "pk": True},
        "trade_date": {"format": "date",                     "required": True,  "pk": True},
        "open":       {"format": "numeric",                  "required": True,  "pk": False},
        "high":       {"format": "numeric",                  "required": True,  "pk": False},
        "low":        {"format": "numeric",                  "required": True,  "pk": False},
        "close":      {"format": "numeric",                  "required": True,  "pk": False},
        "adj_close":  {"format": "numeric",                  "required": True,  "pk": False},
        "volume":     {"format": "bigint",                   "required": True,  "pk": False},
        "fetched_at": {"format": "timestamp with time zone", "required": True,  "pk": False},
    },
    "signals": {
        "id":           {"format": "bigint",                   "required": True, "pk": True},
        "ticker":       {"format": "text",                     "required": True, "pk": False},
        "signal_type":  {"format": "text",                     "required": True, "pk": False},
        "signal_date":  {"format": "date",                     "required": True, "pk": False},
        "generated_at": {"format": "timestamp with time zone", "required": True, "pk": False},
        "payload":      {"format": "jsonb",                    "required": True, "pk": False},
        "status":       {"format": "text",                     "required": True, "pk": False},
    },
}

PK_MARKER = re.compile(r"<pk/>")


def fetch_openapi(url: str, key: str) -> dict:
    """GET /rest/v1/ with Accept: application/openapi+json."""
    r = httpx.get(
        f"{url.rstrip('/')}/rest/v1/",
        headers={
            "Accept": "application/openapi+json",
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
        timeout=15.0,
    )
    r.raise_for_status()
    return r.json()


def parse_actual(openapi: dict) -> dict[str, dict[str, dict[str, object]]]:
    """Build the same shape as EXPECTED from the OpenAPI document."""
    defs = openapi.get("definitions", {})
    out: dict[str, dict[str, dict[str, object]]] = {}
    for tname, tdef in defs.items():
        required = set(tdef.get("required", []))
        cols: dict[str, dict[str, object]] = {}
        for cname, cmeta in tdef.get("properties", {}).items():
            descr = cmeta.get("description") or ""
            cols[cname] = {
                "format": cmeta.get("format", "<missing>"),
                "required": cname in required,
                "pk": bool(PK_MARKER.search(descr)),
            }
        out[tname] = cols
    return out


def diff_table(
    table: str,
    expected_cols: dict,
    actual_cols: dict | None,
) -> tuple[list[str], int]:
    """Return (lines, drift_count) for one table."""
    lines: list[str] = [f"[{table}]"]
    if actual_cols is None:
        lines.append("  DRIFT TABLE MISSING")
        return lines, len(expected_cols) + 1

    drift = 0
    matched = 0

    for col, exp in expected_cols.items():
        if col not in actual_cols:
            lines.append(f"  {col:14s} DRIFT MISSING")
            drift += 1
            continue
        act = actual_cols[col]
        issues: list[str] = []
        if exp["format"] != act["format"]:
            issues.append(
                f"format expected={exp['format']!r} actual={act['format']!r}"
            )
        if exp["required"] != act["required"]:
            issues.append(
                f"required expected={exp['required']} actual={act['required']}"
            )
        if exp["pk"] != act["pk"]:
            issues.append(f"pk expected={exp['pk']} actual={act['pk']}")
        if issues:
            lines.append(f"  {col:14s} DRIFT {'; '.join(issues)}")
            drift += 1
        else:
            tag = f"({act['format']}, " + (
                "required" if act["required"] else "nullable"
            )
            if act["pk"]:
                tag += ", pk"
            tag += ")"
            lines.append(f"  {col:14s} MATCH {tag}")
            matched += 1

    extra = sorted(set(actual_cols) - set(expected_cols))
    for col in extra:
        a = actual_cols[col]
        lines.append(
            f"  {col:14s} DRIFT EXTRA (format={a['format']}, "
            f"required={a['required']}, pk={a['pk']})"
        )
        drift += 1

    summary = f"  summary: {matched}/{len(expected_cols)} cols match"
    if extra:
        summary += f"; {len(extra)} extra col(s)"
    lines.append(summary)
    return lines, drift


def main() -> int:
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

    openapi = fetch_openapi(url, key)
    actual = parse_actual(openapi)

    print("====================================")
    print("Schema drift check -- production")
    print("====================================")

    total_drift = 0
    expected_tables = set(EXPECTED)
    actual_tables = set(actual)

    for table, cols in EXPECTED.items():
        lines, drift = diff_table(table, cols, actual.get(table))
        for line in lines:
            print(line)
        total_drift += drift

    extra_tables = sorted(actual_tables - expected_tables)
    if extra_tables:
        print("[extra tables]")
        for t in extra_tables:
            print(f"  {t}  DRIFT EXTRA TABLE")
        total_drift += len(extra_tables)

    present = len(expected_tables & actual_tables)
    print(
        f"Tables: {present}/{len(expected_tables)} expected present, "
        f"{len(extra_tables)} extra"
    )

    if total_drift == 0:
        print("Result: SCHEMA CLEAN")
        return 0
    print(f"Result: SCHEMA DRIFT DETECTED ({total_drift} issue(s))")
    return 1


if __name__ == "__main__":
    sys.exit(main())
