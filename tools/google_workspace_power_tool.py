#!/usr/bin/env python3
import asyncio
import json
import subprocess
import os
import logging
import sys
import shlex
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Account credential mapping (located in /data/hermes/ on Railway)
ACCOUNTS = {
    "ndr@draas.com": "/data/hermes/oauth-draas.json",
    "nishantranka@gmail.com": "/data/hermes/oauth-gmail.json",
    "ndr@ahfl.in": "/data/hermes/oauth-ahfl.json"
}


def _check_gws_available() -> bool:
    """Return True if at least the primary account credential file exists."""
    return os.path.exists(ACCOUNTS["ndr@draas.com"])


async def _google_workspace_manager_async(
    command: str,
    account_email: Optional[str] = "ndr@draas.com",
    args: Optional[str] = None,
) -> str:
    """
    Universal bridge for the official Google Workspace CLI (gws).
    """
    # 1. Resolve credentials file
    cred_file = ACCOUNTS.get(account_email or "ndr@draas.com")
    if not cred_file:
        return f"Error: Unknown or unconfigured account: {account_email}"

    if not os.path.exists(cred_file):
        return (
            f"Error: Credentials file not found for {account_email} at {cred_file}. "
            "Ensure Railway env vars are set and the service has restarted."
        )

    try:
        # Build the final CLI command
        npx_cmd = ["npx", "--yes", "gws"] + shlex.split(command)

        if args:
            npx_cmd += shlex.split(args)

        # Environment management
        env = os.environ.copy()
        env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = cred_file

        # Execute in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        process = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                npx_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            ),
        )

        # Handle output
        if process.returncode == 0:
            try:
                data = json.loads(process.stdout)
                return json.dumps(data, indent=2)
            except Exception:
                return process.stdout or "Success (No output)"
        else:
            return (
                f"Error executing GWS CLI ({command}) [Exit: {process.returncode}]:\n"
                f"{process.stderr or process.stdout}"
            )

    except subprocess.TimeoutExpired:
        return f"Error: GWS CLI '{command}' timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


def _handle_google_workspace_manager(args: dict, **kwargs) -> str:
    """Sync handler wrapper — bridges async implementation to registry dispatch."""
    command = args.get("command", "")
    account_email = args.get("account_email", "ndr@draas.com")
    extra_args = args.get("args")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    _google_workspace_manager_async(command, account_email, extra_args),
                )
                return future.result(timeout=90)
        else:
            return loop.run_until_complete(
                _google_workspace_manager_async(command, account_email, extra_args)
            )
    except Exception as e:
        return f"Error: {str(e)}"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_GWS_SCHEMA = {
    "name": "google_workspace_manager",
    "description": (
        "CRITICAL: High-performance bridge for the official Google Workspace CLI (gws). "
        "Mandatory for all Workspace tasks (Gmail, Drive, Calendar, Sheets, Docs). "
        "Use the 'command' field to pass the service, resource, and method "
        "(e.g., 'gmail messages list', 'drive files list', 'sheets values get'). "
        "It is strictly forbidden to use custom Python scripts for any Google Workspace task."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": (
                    "The gws command string, e.g. "
                    "'gmail messages list --params {\"maxResults\":10}', "
                    "'drive files list', "
                    "'sheets values get --spreadsheetId SHEET_ID --range Sheet1!A:Z', "
                    "'calendar events list --calendarId primary'."
                ),
            },
            "account_email": {
                "type": "string",
                "enum": ["ndr@draas.com", "nishantranka@gmail.com", "ndr@ahfl.in"],
                "description": (
                    "Which Google Workspace account to use. Routing rules: "
                    "ndr@draas.com = primary/default (use when user says 'email', 'my email', "
                    "'inbox', 'my drive', 'my calendar', or gives no qualifier); "
                    "ndr@ahfl.in = AHFL account (use when user says 'AHFL email', 'AHFL drive', "
                    "or 'ahfl.in'); "
                    "nishantranka@gmail.com = personal Gmail (use when user says 'gmail' or "
                    "'personal email'). "
                    "Defaults to ndr@draas.com."
                ),
            },
            "args": {
                "type": "string",
                "description": "Additional CLI flags appended verbatim, e.g. '--params {}'.",
            },
        },
        "required": ["command"],
    },
}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

from tools.registry import registry

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
