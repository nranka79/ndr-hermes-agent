#!/usr/bin/env python3
"""
Google Workspace Manager Tool — bridges Hermes to the official gws CLI.

Invokes the gws binary directly (not via npx) using a path resolved at
import time.  This avoids relying on PATH availability of npx/node inside
the Railway container subprocess environment.

Binary resolution order:
  1. <app_root>/node_modules/.bin/gws   (installed by npm install in nixpacks)
  2. /app/node_modules/.bin/gws          (Railway absolute fallback)
  3. shutil.which("gws")                 (anything on PATH)
  4. npx --yes @googleworkspace/cli      (last resort, downloads if needed)
"""

import json
import os
import shlex
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Binary path resolution — done ONCE at import time
# ---------------------------------------------------------------------------

def _resolve_gws_binary() -> str | None:
    """Return the absolute path to the gws binary, or None if not found."""
    # 1. node_modules relative to this file's app root
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local = os.path.join(app_root, "node_modules", ".bin", "gws")
    if os.path.isfile(local) and os.access(local, os.X_OK):
        logger.debug("gws binary found at %s", local)
        return local

    # 2. Railway always deploys to /app
    railway = "/app/node_modules/.bin/gws"
    if os.path.isfile(railway) and os.access(railway, os.X_OK):
        logger.debug("gws binary found at %s", railway)
        return railway

    # 3. Anything on PATH (e.g. global npm install)
    on_path = shutil.which("gws")
    if on_path:
        logger.debug("gws binary found on PATH at %s", on_path)
        return on_path

    logger.warning(
        "gws binary not found in node_modules or PATH. "
        "Tool will fall back to 'npx --yes @googleworkspace/cli'. "
        "Run 'npm install' in the app root to fix this properly."
    )
    return None


_GWS_BINARY: str | None = _resolve_gws_binary()


# ---------------------------------------------------------------------------
# Account credential mapping
# ---------------------------------------------------------------------------

ACCOUNTS = {
    "ndr@draas.com":          "/data/hermes/oauth-draas.json",
    "nishantranka@gmail.com": "/data/hermes/oauth-gmail.json",
    "ndr@ahfl.in":            "/data/hermes/oauth-ahfl.json",
}


def _check_gws_available() -> bool:
    """Tool is available when the primary credential file exists."""
    return os.path.exists(ACCOUNTS["ndr@draas.com"])


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

def _handle_google_workspace_manager(args: dict, **kwargs) -> str:
    """Run a gws CLI command and return the result as a string."""
    command     = args.get("command", "")
    account_email = args.get("account_email") or "ndr@draas.com"
    extra_args  = args.get("args")

    # Resolve credential file
    cred_file = ACCOUNTS.get(account_email)
    if not cred_file:
        return f"Error: Unknown account: {account_email}"

    if not os.path.exists(cred_file):
        return (
            f"Error: Credentials file not found for {account_email} at {cred_file}. "
            "Check that Railway env vars (DRAAS_OAUTH_*) are set and the service has restarted."
        )

    # Build command
    if _GWS_BINARY:
        cmd = [_GWS_BINARY] + shlex.split(command)
    else:
        # npx fallback — slower, downloads if needed
        npx = shutil.which("npx") or "npx"
        cmd = [npx, "--yes", "@googleworkspace/cli"] + shlex.split(command)

    if extra_args:
        cmd += shlex.split(extra_args)

    env = os.environ.copy()
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
            "Error: gws binary not found. "
            f"Tried: {cmd[0]}. "
            "Ensure npm install ran during build (check nixpacks.toml)."
        )
    except subprocess.TimeoutExpired:
        return f"Error: gws command timed out after 60s: {command}"

    if result.returncode == 0:
        try:
            return json.dumps(json.loads(result.stdout), indent=2)
        except Exception:
            return result.stdout or "Success (no output)"
    else:
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
                    "also matches voice variants: draas/drast/drus/dross/DRaaS. "
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
