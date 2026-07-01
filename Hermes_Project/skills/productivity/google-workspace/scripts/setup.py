#!/usr/bin/env python3
"""Google Workspace OAuth2 setup for Hermes Agent.

Auth tokens are stored in the Token Vault — NOT in a flat file.
This script wraps the vault-based auth flow for agent use.

Commands:
  setup.py --check                          # Is auth valid for current session user?
  setup.py --check-live                     # Check auth with a real API call
  setup.py --auth-url                       # Print the OAuth URL for user to visit
  setup.py --revoke                         # Revoke and delete vault token for current user
  setup.py --install-deps                   # Install Python dependencies only

Note: --client-secret and --auth-code are no longer supported.
OAuth client credentials come from HERMES_OAUTH_CLIENT_ID / HERMES_OAUTH_CLIENT_SECRET env vars.
The OAuth callback is handled automatically by the Hermes gateway at /gws/auth/callback.
"""

from __future__ import annotations

import argparse
import os
import shutil
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

REQUIRED_PACKAGES = ["google-api-python-client", "google-auth-oauthlib", "google-auth-httplib2"]


def _session_telegram_id() -> str | None:
    """Return HERMES_SESSION_USER_ID from environment (injected by Hermes gateway for subprocesses)."""
    tid = os.environ.get("HERMES_SESSION_USER_ID", "").strip()
    return tid or None


def install_deps():
    """Install Google API packages if missing. Returns True on success."""
    try:
        import googleapiclient  # noqa: F401
        import google_auth_oauthlib  # noqa: F401
        print("Dependencies already installed.")
        return True
    except ImportError:
        pass

    print("Installing Google API dependencies...")

    # First choice: pip in the current interpreter. Works for most installs.
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + REQUIRED_PACKAGES,
            stdout=subprocess.DEVNULL,
        )
        print("Dependencies installed.")
        return True
    except subprocess.CalledProcessError as e:
        pip_error = e

    # Fallback: the interpreter has no pip (the Hermes Docker image's venv is
    # built with `uv sync`, which does not bootstrap pip). `uv pip install
    # --python <interpreter>` installs into that exact interpreter without
    # needing pip present. Targeting sys.executable keeps us on the venv the
    # script is actually running under, rather than guessing.
    uv = shutil.which("uv")
    if uv:
        try:
            subprocess.check_call(
                [uv, "pip", "install", "--python", sys.executable, "--quiet"]
                + REQUIRED_PACKAGES,
                stdout=subprocess.DEVNULL,
            )
            print("Dependencies installed.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install dependencies via uv: {e}")
            print(f"Manually: {uv} pip install --python {sys.executable} {' '.join(REQUIRED_PACKAGES)}")
            return False

    print(f"ERROR: Failed to install dependencies: {pip_error}")
    print(
        "On environments without pip (e.g. Nix, or the Hermes Docker image's "
        "uv-managed venv), install the optional extra instead:"
    )
    print("  pip install 'hermes-agent[google]'")
    print(f"Or manually: {sys.executable} -m pip install {' '.join(REQUIRED_PACKAGES)}")
    return False


def _ensure_deps():
    """Check deps are available, install if not, exit on failure."""
    try:
        import googleapiclient  # noqa: F401
        import google_auth_oauthlib  # noqa: F401
    except ImportError:
        if not install_deps():
            sys.exit(1)


def check_auth(quiet: bool = False):
    """Check if the current session user has a valid vault token."""
    tid = _session_telegram_id()
    if not tid:
        print("NOT_AUTHENTICATED: HERMES_SESSION_USER_ID is not set in this environment.")
        print("Run this script from within a Hermes session (e.g. via the terminal tool).")
        return False

    _ensure_deps()
    try:
        from tools.gws_auth import load_credentials
        creds = load_credentials()
        if creds.valid:
            if not quiet:
                print(f"AUTHENTICATED: Valid Google token in vault for user {tid}")
            return True
        print(f"TOKEN_INVALID: Token for user {tid} is not valid. Re-authorize.")
        return False
    except FileNotFoundError:
        print(f"NOT_AUTHENTICATED: No token in vault for user {tid}.")
        print("Run: token_auth authorize service=google  (in Hermes chat)")
        return False
    except RuntimeError as e:
        print(f"VAULT_ERROR: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def check_auth_live():
    """Check auth with a real API call to detect disabled_client/account issues."""
    if not check_auth(quiet=True):
        return False

    _ensure_deps()
    try:
        from tools.gws_auth import build_service
        service = build_service("calendar", "v3")
        service.calendarList().list(maxResults=1).execute()
        print("LIVE_CHECK_OK: Real API call succeeded.")
        return True
    except Exception as e:
        err_str = str(e).lower()
        if "disabled_client" in err_str or "invalid_client" in err_str:
            print(f"LIVE_CHECK_FAILED: OAuth client or account disabled: {e}")
            print("  Check Google Cloud Console for disabled OAuth client")
        else:
            print(f"LIVE_CHECK_FAILED: {e}")
        return False


def get_auth_url():
    """Print the OAuth authorization URL for the current session user."""
    tid = _session_telegram_id()
    if not tid:
        print("ERROR: HERMES_SESSION_USER_ID is not set. Run from within a Hermes session.")
        sys.exit(1)

    try:
        from tools.gws_auth import get_auth_url as _get_auth_url
        url = _get_auth_url(tid)
        print(url)
    except EnvironmentError as e:
        print(f"ERROR: {e}")
        print("Ensure HERMES_OAUTH_CLIENT_ID and HERMES_OAUTH_CLIENT_SECRET are set.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not generate auth URL: {e}")
        sys.exit(1)


def revoke():
    """Revoke stored token in the vault for the current session user."""
    tid = _session_telegram_id()
    if not tid:
        print("ERROR: HERMES_SESSION_USER_ID is not set. Run from within a Hermes session.")
        sys.exit(1)

    try:
        from tools.gws_vault_client import delete_token
        deleted = delete_token(tid, "google")
        if deleted:
            print(f"OK: Google token revoked for user {tid}")
        else:
            print(f"No token found for user {tid} in vault.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Google Workspace OAuth setup for Hermes")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check if auth is valid (exit 0=yes, 1=no)")
    group.add_argument("--check-live", action="store_true", help="Check auth with a real API call")
    group.add_argument("--auth-url", action="store_true", help="Print OAuth URL for user to visit")
    group.add_argument("--revoke", action="store_true", help="Revoke and delete vault token for current user")
    group.add_argument("--install-deps", action="store_true", help="Install Python dependencies")
    args = parser.parse_args()

    if args.check:
        sys.exit(0 if check_auth() else 1)
    if getattr(args, "check_live", False):
        sys.exit(0 if check_auth_live() else 1)
    elif args.auth_url:
        get_auth_url()
    elif args.revoke:
        revoke()
    elif args.install_deps:
        sys.exit(0 if install_deps() else 1)


if __name__ == "__main__":
    main()
