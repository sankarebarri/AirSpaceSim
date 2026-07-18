#!/usr/bin/env python3
"""Create a development-only test account for the hosted API.

Local/test use only — never run against a production database with these
defaults. The password is generated unless provided, and is printed once.

Usage:
    python3 scripts/seed_dev_user.py                 # demo@example.test, random password
    python3 scripts/seed_dev_user.py --email you@example.test --password "..."
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = PROJECT_ROOT / "apps" / "api"
for path in (str(PROJECT_ROOT), str(API_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.db.session import get_session_factory, init_db  # noqa: E402
from app.services.auth import get_user_by_email, register_user  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed a development test account.")
    parser.add_argument("--email", default="demo@example.test")
    parser.add_argument(
        "--password",
        default=None,
        help="Password for the account (generated when omitted).",
    )
    parser.add_argument("--display-name", default="Demo Trainee")
    args = parser.parse_args()

    init_db()
    session = get_session_factory()()
    try:
        if get_user_by_email(session, args.email.lower()) is not None:
            print(f"Account already exists: {args.email}")
            return 0
        password = args.password or secrets.token_urlsafe(12)
        register_user(
            session,
            email=args.email,
            password=password,
            display_name=args.display_name,
        )
        print("Development test account created (local/test only):")
        print(f"  Email:    {args.email}")
        print(f"  Password: {password}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
