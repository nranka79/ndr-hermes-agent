#!/usr/bin/env python3
"""Bridge between Hermes vault-based OAuth token and gws CLI.

Loads the current session user's Google OAuth credentials from the Token Vault,
then executes gws with a valid access token. The user identity is read from
HERMES_SESSION_USER_ID in the environment (injected by the Hermes gateway).
"""
import os
import subprocess
import sys
from pathlib import Path

# Ensure sibling modules are importable when run standalone.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# Add Hermes root so that tools.gws_auth is importable from subprocess context.
_HERMES_ROOT = str(Path(__file__).resolve().parents[4])
if _HERMES_ROOT not in sys.path:
    sys.path.insert(0, _HERMES_ROOT)


def get_valid_token() -> str:
    """Return a valid access token for the current session user from the Token Vault."""
    from tools.gws_auth import load_credentials
    creds = load_credentials()
    if not creds.token:
        print("ERROR: No access token available after loading credentials.", file=sys.stderr)
        sys.exit(1)
    return creds.token


def main():
    """Load vault token for current user, then exec gws with remaining args."""
    if len(sys.argv) < 2:
        print("Usage: gws_bridge.py <gws args...>", file=sys.stderr)
        sys.exit(1)

    access_token = get_valid_token()
    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_TOKEN"] = access_token

    result = subprocess.run(["gws"] + sys.argv[1:], env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
