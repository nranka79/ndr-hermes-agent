#!/usr/bin/env python3
"""
THROWAWAY — one-time migration: copy identity records from users.json into the vault.

Usage:
    python3 scripts/migrate_users_json_to_vault.py --secret SECRET [--users-json PATH] [--vault-socket PATH]

Default users.json path: $HERMES_HOME/users.json
Default vault socket: /run/gws-vault/vault.sock
"""

import argparse
import json
import os
import sys
from pathlib import Path

from tools import gws_vault_client as vault


def load_users_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def migrate() -> None:
    parser = argparse.ArgumentParser(description="Migrate users.json identities to vault")
    default_home = os.environ.get("HERMES_HOME", "")
    parser.add_argument("--users-json", default=os.path.join(default_home, "users.json"))
    parser.add_argument("--vault-socket", default="/run/gws-vault/vault.sock")
    parser.add_argument("--secret", default=os.environ.get("GWS_VAULT_SECRET", ""))
    args = parser.parse_args()

    vault.VAULT_SOCKET_PATH = args.vault_socket
    vault.VAULT_SECRET = args.secret

    if not args.secret:
        print("ERROR: GWS_VAULT_SECRET is required (--secret or env var)")
        sys.exit(1)

    users_path = Path(args.users_json)
    if not users_path.exists():
        print(f"ERROR: users.json not found at {users_path}")
        sys.exit(1)

    users = load_users_json(str(users_path))
    print(f"Loaded {len(users)} user records from {users_path}\n")

    success = 0
    errors = 0

    for email_key, record in users.items():
        if not isinstance(record, dict):
            print(f"  SKIP {email_key}: not a dict record")
            continue

        user_id = record.get("email") or email_key
        name = record.get("name", "")
        role = record.get("role", "employee")
        permissions = record.get("permissions", {})
        draas_id = record.get("draas_user_id", "")

        identities = record.get("identities", {})
        if not isinstance(identities, dict):
            identities = {}

        print(f"\n  User: {name} ({user_id})")

        try:
            vault.add_identity(
                user_id=user_id,
                identity_type="email",
                identity_value=user_id,
                name=name,
                role=role,
                permissions=permissions,
            )
            print(f"    ok  canonical email: {user_id}")
        except vault.VaultError as e:
            print(f"    ERR canonical email: {e}")
            errors += 1
            continue

        if draas_id and draas_id != user_id:
            try:
                vault.add_identity(
                    user_id=user_id,
                    identity_type="draas_user_id",
                    identity_value=draas_id,
                )
                print(f"    ok  draas_user_id: {draas_id}")
            except vault.VaultError as e:
                print(f"    ERR draas_user_id: {e}")
                errors += 1

        for id_type, id_values in identities.items():
            if not isinstance(id_values, list):
                continue
            for id_val in id_values:
                if not id_val or id_val == user_id:
                    continue
                try:
                    vault.add_identity(
                        user_id=user_id,
                        identity_type=id_type,
                        identity_value=id_val,
                    )
                    print(f"    ok  {id_type}: {id_val}")
                except vault.VaultError as e:
                    print(f"    ERR {id_type}: {e}")
                    errors += 1

        success += 1

    print(f"\n{'='*50}")
    print(f"Done: {success} users migrated, {errors} errors")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    migrate()
