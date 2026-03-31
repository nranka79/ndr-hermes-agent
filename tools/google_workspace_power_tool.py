#!/usr/bin/env python3
"""
Google Workspace Manager Tool — bridges Hermes to the official gws CLI.

The gws binary is installed globally via `npm install -g @googleworkspace/cli`
in nixpacks.toml, landing at /usr/local/bin/gws.  We also check local
node_modules as a fallback.

Key lesson: Python subprocess does NOT automatically inherit the Nix/node
PATH from the Railway build environment. We explicitly augment PATH in every
subprocess call to ensure node-installed binaries are reachable.
"""

import json
import os
import shlex
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Augmented PATH — injected into every subprocess call
# ---------------------------------------------------------------------------

_APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_NODE_BIN_DIRS = [
    "/usr/local/bin",                                        # npm -g install target
    "/usr/bin",
    os.path.join(_APP_ROOT, "node_modules", ".bin"),         # local npm install
    "/app/node_modules/.bin",                                # Railway absolute fallback
]


def _augmented_path() -> str:
    """Return PATH string that includes all known node binary locations."""
    existing = os.environ.get("PATH", "")
    extra = [d for d in _NODE_BIN_DIRS if d not in existing]
    return ":".join(extra + [existing]) if existing else ":".join(extra)


# ---------------------------------------------------------------------------
# Binary path resolution — done ONCE at import time
# ---------------------------------------------------------------------------

def _resolve_gws_binary() -> str | None:
    """Return the absolute path to the gws binary, or None."""
    # 1. Direct file checks (fastest, no PATH dependency)
    candidates = [
        "/usr/local/bin/gws",                                    # npm -g
        os.path.join(_APP_ROOT, "node_modules", ".bin", "gws"),  # local npm
        "/app/node_modules/.bin/gws",                            # Railway fallback
        "/usr/bin/gws",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            logger.debug("gws binary found at %s", c)
            return c

    # 2. shutil.which with augmented PATH
    found = shutil.which("gws", path=_augmented_path())
    if found:
        logger.debug("gws binary found via which: %s", found)
        return found

    logger.warning(
        "gws binary not found. Expected at /usr/local/bin/gws after "
        "'npm install -g @googleworkspace/cli'. Check nixpacks.toml install phase."
    )
    return None


_GWS_BINARY: str | None = _resolve_gws_binary()

# Log at startup so Railway build logs show what was resolved
if _GWS_BINARY:
    logger.info("google_workspace_manager: gws binary = %s", _GWS_BINARY)
else:
    logger.warning("google_workspace_manager: gws binary NOT FOUND — tool will be unavailable")


# ---------------------------------------------------------------------------
# Account credential mapping
# ---------------------------------------------------------------------------

ACCOUNTS = {
    "ndr@draas.com":          "/data/hermes/oauth-draas.json",
    "nishantranka@gmail.com": "/data/hermes/oauth-gmail.json",
    "ndr@ahfl.in":            "/data/hermes/oauth-ahfl.json",
}


def _check_gws_available() -> bool:
    """Tool is available when the binary exists AND the primary credential file exists."""
    return bool(_GWS_BINARY) and os.path.exists(ACCOUNTS["ndr@draas.com"])


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

def _handle_google_workspace_manager(args: dict, **kwargs) -> str:
    """Run a gws CLI command and return the result."""
    command       = args.get("command", "")
    account_email = args.get("account_email") or "ndr@draas.com"
    extra_args    = args.get("args")

    # Resolve credential file
    cred_file = ACCOUNTS.get(account_email)
    if not cred_file:
        return f"Error: Unknown account: {account_email}"
    if not os.path.exists(cred_file):
        return (
            f"Error: Credentials file not found for {account_email} at {cred_file}. "
            "Check Railway env vars (DRAAS_OAUTH_*) and restart the service."
        )

    # Build command — prefer direct binary, fall back to npx
    if _GWS_BINARY:
        cmd = [_GWS_BINARY] + shlex.split(command)
    else:
        # Last resort: try npx with augmented PATH
        npx = shutil.which("npx", path=_augmented_path()) or "npx"
        cmd = [npx, "--yes", "@googleworkspace/cli"] + shlex.split(command)

    if extra_args:
        cmd += shlex.split(extra_args)

    # Subprocess environment: augment PATH so node binaries are reachable
    env = os.environ.copy()
    env["PATH"] = _augmented_path()
    env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = cred_file

    logger.debug("gws exec: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
    except FileNotFoundError:
        return (
            f"Error: gws binary not found at {cmd[0]}. "
            "Ensure 'npm install -g @googleworkspace/cli' ran in the nixpacks build. "
            f"Searched: {_NODE_BIN_DIRS}"
        )
    except subprocess.TimeoutExpired:
        return f"Error: gws command timed out after 60s: {command}"

    if result.returncode == 0:
        try:
            return json.dumps(json.loads(result.stdout), indent=2)
        except Exception:
            return result.stdout or "Success (no output)"

    return (
        f"Error running gws ({command}) [exit {result.returncode}]:\n"
        f"{result.stderr or result.stdout}"
    )


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_GWS_SCHEMA = {
    "name": "google_workspace_manager",
    "description": (
        "CRITICAL: Bridge to the official Google Workspace CLI (gws). "
        "Mandatory for ALL Workspace tasks — Gmail, Drive, Calendar, Sheets, Docs, "
        "Contacts, Tasks, Chat. "
        "Pass the service + subcommand in 'command', e.g. "
        "'gmail messages list', 'drive files list', "
        "'sheets values get --spreadsheetId ID --range Sheet1!A:Z', "
        "'calendar events list --calendarId primary'. "
        "NEVER write custom Python scripts for any Google Workspace operation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": (
                    "The gws subcommand and flags, e.g. "
                    "'gmail messages list --params {\"maxResults\":10}', "
                    "'drive files list --params {\"q\":\"name contains \\\"report\\\"\"}', "
                    "'sheets values get --spreadsheetId SHEET_ID --range contacts!A:Z', "
                    "'calendar events list --calendarId primary --params {\"maxResults\":5}'."
                ),
            },
            "account_email": {
                "type": "string",
                "enum": ["ndr@draas.com", "nishantranka@gmail.com", "ndr@ahfl.in"],
                "description": (
                    "Account to use. Routing: "
                    "ndr@draas.com — default/primary, use for 'my email', 'email', 'inbox', "
                    "'my drive', 'my calendar', 'my documents', or no qualifier; "
                    "also matches voice variants draas/drast/drus/dross/DRaaS. "
                    "ndr@ahfl.in — use for 'AHFL email/drive/calendar' or 'ahfl.in'. "
                    "nishantranka@gmail.com — use for 'gmail', 'personal email', 'my gmail'. "
                    "When ambiguous: ask before proceeding."
                ),
            },
            "args": {
                "type": "string",
                "description": "Extra flags appended verbatim to the command.",
            },
        },
        "required": ["command"],
    },
}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

from tools.registry import registry  # noqa: E402

registry.register(
    name="google_workspace_manager",
    toolset="google_workspace",
    schema=_GWS_SCHEMA,
    handler=_handle_google_workspace_manager,
    check_fn=_check_gws_available,
    requires_env=["DRAAS_OAUTH_REFRESH_TOKEN"],
    is_async=False,
    description=_GWS_SCHEMA["description"],
    emoji="📧",
)
