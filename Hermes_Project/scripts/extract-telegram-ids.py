#!/usr/bin/env python3
"""
Read hermes-data/users.json and print Telegram chat IDs as a comma-separated
list, ready to drop into the TELEGRAM_ALLOWED_USERS env var in
/opt/hermes/docker-compose.yml.

Run scripts/sync-from-vps.ps1 first if you want the latest version -- this
script reads the LOCAL mirror, which is one-way synced from the VPS.

Usage:
    python3 scripts/extract-telegram-ids.py
    python3 scripts/extract-telegram-ids.py --format env
    python3 scripts/extract-telegram-ids.py --format json
    python3 scripts/extract-telegram-ids.py --path /custom/users.json
"""
import argparse
import json
import sys
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "hermes-data" / "users.json"


def main() -> int:
    p = argparse.ArgumentParser(
        description="Extract Telegram chat IDs from hermes-data/users.json",
    )
    p.add_argument("--path", type=Path, default=DEFAULT_PATH,
                   help=f"users.json path (default: {DEFAULT_PATH})")
    p.add_argument("--format", choices=("ids", "env", "json"), default="ids",
                   help="ids=comma-separated, env=KEY=val line, json=array of IDs")
    args = p.parse_args()

    if not args.path.exists():
        print(f"Error: {args.path} not found.", file=sys.stderr)
        print("Run scripts/sync-from-vps.ps1 first to pull the latest from the VPS.",
              file=sys.stderr)
        return 1

    with open(args.path) as f:
        users = json.load(f)

    seen, ids = set(), []
    for entry in users.values():
        for tid in entry.get("identities", {}).get("telegram", []):
            if tid not in seen:
                seen.add(tid)
                ids.append(tid)

    if args.format == "ids":
        print(",".join(ids))
    elif args.format == "env":
        print(f"TELEGRAM_ALLOWED_USERS={','.join(ids)}")
    elif args.format == "json":
        print(json.dumps(ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
