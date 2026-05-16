#!/usr/bin/env python
"""scripts/smoke_test_db.py - WP-DEV-ENV-SETUP smoke test.

Validates the Python -> .env -> Supabase -> schema chain end-to-end.

Uses supabase-py (REST/PostgREST over HTTPS). Native PG drivers
(psycopg2-binary, psycopg-binary) are unavailable for win_arm64
on PyPI, so the REST path is the chosen access pattern.

Uses SUPABASE_SERVICE_ROLE_KEY (admin) which bypasses Row Level
Security on the three tables (RLS is enabled with no policies, so
anon/authenticated would see zero rows by design).

Run from project root:
    .\\.venv\\Scripts\\python.exe scripts\\smoke_test_db.py

Exits 0 on PASS, non-zero on any failure.
"""

import os
import sys
from pathlib import Path


EXPECTED_TABLES = ["prices", "signals", "stocks"]
REQUIRED_ENV_KEYS = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
]


def main() -> int:
    root = Path(__file__).resolve().parent.parent

    # 1. Load .env
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("FAIL: python-dotenv not installed.")
        return 1

    env_path = root / ".env"
    if not env_path.exists():
        print(f"FAIL: .env not found at {env_path}")
        return 1
    load_dotenv(env_path)

    # 2. Verify required env keys
    missing = [k for k in REQUIRED_ENV_KEYS if not os.getenv(k)]
    if missing:
        print(f"FAIL: missing .env keys: {missing}")
        return 1

    # 3. Build supabase client
    try:
        from supabase import create_client
    except ImportError:
        print("FAIL: supabase-py not installed.")
        return 1

    try:
        client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        )
    except Exception as e:
        print(f"FAIL: create_client raised: {type(e).__name__}: {e}")
        return 1

    # 4. Verify each expected table is reachable.
    accessible = []
    failed = {}
    for table in EXPECTED_TABLES:
        try:
            client.table(table).select("*").limit(0).execute()
            accessible.append(table)
        except Exception as e:
            failed[table] = f"{type(e).__name__}: {e}"

    if failed:
        print("FAIL: one or more tables not reachable:")
        for t, err in failed.items():
            print(f"  {t}: {err}")
        print(
            "\nHints:"
            "\n  - Confirm SUPABASE_URL matches the project (has https://, no typo)."
            "\n  - Confirm SUPABASE_SERVICE_ROLE_KEY is the service_role secret,"
            "\n    NOT the anon public key."
            "\n  - Confirm tables were created in the public schema."
        )
        return 1

    print("PASS")
    print(f"  URL:             {os.getenv('SUPABASE_URL')}")
    print(f"  Tables reachable (service_role, RLS bypassed):")
    for t in accessible:
        print(f"    - {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
