#!/usr/bin/env python3
"""
One-time cleanup: merge vault token data written under a user's RAW channel
id (e.g. the bare Telegram numeric id) into their CANONICAL vault user_id
(e.g. ``ndr-7449813913``).

Background
----------
``tools/gws_auth.py`` was fixed (2026-07-08) to resolve every raw channel id
through ``canonical_uid()`` before reading/writing a token. Some other vault
callers (``tools/user_vocab.py``, fixed alongside this script) were not,
and wrote data under the raw id instead. Result: the same physical user ends
up with token/vocab data split across two vault keys, and reads through the
now-canonicalized path silently miss data that's still sitting under the old
raw-id key. Confirmed live on the Hetzner vault
(``/opt/gws-vault/tokens/7449813913/`` vs
``/opt/gws-vault/tokens/ndr-7449813913/``) -- see ``.plans/`` for the full
root-cause writeup.

What this script does
----------------------
For each known (raw_id, canonical_id) pair below, for every vault service
found under the RAW id:
  * If that service does NOT also exist under the canonical id -> this is a
    clean migration. With ``--execute``, the token is read from the raw key,
    written to the canonical key, then deleted from the raw key.
  * If it exists under BOTH -> this is a conflict (two different, possibly
    diverging copies of the same data). This script NEVER auto-resolves a
    conflict -- it only reports it. Resolve manually (e.g. via the CLI /
    admin tooling) once you've decided which copy is authoritative.

Safety
------
* Defaults to ``--dry-run`` (the default action if you omit ``--execute``) --
  prints exactly what it *would* do without writing anything.
* Only ever deletes a raw-id token after successfully writing it to the
  canonical key (read -> write -> verify write -> delete raw), never the
  reverse order.
* Never touches a (user, service) pair that exists under both keys.

Usage (run on the Hetzner host, where the vault socket is reachable):
    python3 scripts/migrate_orphaned_vault_keys.py --secret SECRET            # dry run (report only)
    python3 scripts/migrate_orphaned_vault_keys.py --secret SECRET --execute  # perform clean migrations
"""

import argparse
import os
import sys

from tools import gws_vault_client as vault

# Known (raw_telegram_id, canonical_vault_user_id, display_name) triples,
# sourced directly from the live identity records under
# /opt/gws-vault/identities/*.json at investigation time (2026-07-10). This
# is a one-time, hand-verified list rather than a dynamic identity scan --
# there is no vault server op to enumerate identities without adding new
# server-side surface area, and for a one-time cleanup of exactly 6 known
# users that isn't worth the extra deploy. If more users are added later,
# extend this list (or add a proper ``list_identities`` client wrapper if
# this kind of cleanup becomes routine).
KNOWN_USERS = [
    ("7449813913", "ndr-7449813913", "Nishant Ranka"),
    ("7281906252", "pm2.blr-7281906252", "pm2.blr"),
    ("8502281203", "psingh-8502281203", "psingh"),
    ("7245204091", "rnr-7245204091", "Ruhaan Ranka"),
    ("8717455402", "sales1.blr-8717455402", "sales1.blr"),
    ("8654428154", "vkdas-8654428154", "vkdas"),
]


def _list_services(user_id: str) -> list:
    """List services for user_id, self-authorized (session_uid == user_id).

    Returns [] (not an error) if the user has no token directory at all --
    the vault server returns an empty list for that case, not a 404.
    """
    try:
        return vault.list_services(user_id, session_uid=user_id)
    except vault.VaultError as exc:
        print(f"    WARN: could not list services for {user_id!r}: {exc}")
        return []


def migrate(execute: bool) -> int:
    total_clean = 0
    total_conflicts = 0
    total_errors = 0

    for raw_id, canonical_id, name in KNOWN_USERS:
        if raw_id == canonical_id:
            continue  # nothing to do -- already canonical

        raw_services = set(_list_services(raw_id))
        if not raw_services:
            continue  # nothing orphaned under the raw key for this user

        canonical_services = set(_list_services(canonical_id))

        print(f"\n{name} ({raw_id} -> {canonical_id})")
        for service in sorted(raw_services):
            if service in canonical_services:
                print(f"    CONFLICT service={service!r}: exists under BOTH "
                      f"{raw_id!r} and {canonical_id!r} -- not touched, "
                      f"resolve manually")
                total_conflicts += 1
                continue

            if not execute:
                print(f"    WOULD MIGRATE service={service!r}: "
                      f"{raw_id} -> {canonical_id}")
                total_clean += 1
                continue

            try:
                token_json = vault.get_token(raw_id, service, session_uid=raw_id)
                vault.set_token(canonical_id, service, token_json)
                # Verify the write landed before deleting the only other copy.
                if service not in set(_list_services(canonical_id)):
                    raise vault.VaultError(
                        f"post-write verification failed for {service!r}"
                    )
                vault.delete_token(raw_id, service)
                print(f"    OK migrated service={service!r}: "
                      f"{raw_id} -> {canonical_id}")
                total_clean += 1
            except vault.VaultError as exc:
                print(f"    ERROR migrating service={service!r}: {exc}")
                total_errors += 1

    print(f"\n{'=' * 60}")
    mode = "EXECUTED" if execute else "DRY RUN (no changes made -- rerun with --execute)"
    print(f"{mode}: {total_clean} clean migration(s), "
          f"{total_conflicts} conflict(s) needing manual review, "
          f"{total_errors} error(s)")
    return 1 if total_errors else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-socket", default=os.environ.get(
        "GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock"))
    parser.add_argument("--secret", default=os.environ.get("GWS_VAULT_SECRET", ""))
    parser.add_argument("--execute", action="store_true",
                         help="Actually perform clean migrations (default: dry run)")
    args = parser.parse_args()

    vault.VAULT_SOCKET = args.vault_socket
    vault.VAULT_SECRET = args.secret

    if not args.secret:
        print("ERROR: GWS_VAULT_SECRET is required (--secret or env var)")
        sys.exit(1)

    sys.exit(migrate(execute=args.execute))


if __name__ == "__main__":
    main()
