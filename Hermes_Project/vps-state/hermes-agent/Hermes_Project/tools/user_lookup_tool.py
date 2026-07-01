#!/usr/bin/env python3
"""
User Lookup Tool — employee directory backed by the gws_oauth_tokens table in n8n.

Allows the agent to:
  - Find a colleague's Telegram ID and email by name or username.
  - Get the current user's own Telegram ID and username from session env vars.

The agent uses this when it needs to send a Telegram message to another employee,
look up an email address, or resolve a name to a Telegram identity.

Registered as: user_lookup_tool
Toolset: messaging
"""

import json
import logging
import os
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

_N8N_BASE_URL = os.environ.get("HERMES_N8N_BASE_URL", "https://transcribe.ahfl.in")


def _handle_user_lookup_tool(args: dict, **kwargs) -> str:
    operation = (args.get("operation") or "").strip()

    if operation == "whoami":
        return _whoami()

    if operation == "find":
        query = (args.get("query") or "").strip()
        if not query:
            return json.dumps({"error": "Missing required argument: query"})
        return _find_user(query)

    if operation == "list_all":
        return _list_all()

    return json.dumps({"error": f"Unknown operation '{operation}'. Valid: whoami | find | list_all"})


def _whoami() -> str:
    """Return the current Telegram user's identity from session env vars."""
    user_id = os.environ.get("HERMES_SESSION_USER_ID", "")
    user_name = os.environ.get("HERMES_SESSION_USER_NAME", "")
    if not user_id:
        return json.dumps({"error": "No active Telegram session — user_id not available."})
    return json.dumps({
        "telegram_id": user_id,
        "telegram_username": user_name or None,
    })


def _call_n8n_user_lookup(payload: dict) -> str:
    url = f"{_N8N_BASE_URL}/webhook/hermes-user-lookup"
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        logger.error("hermes-user-lookup HTTP %d: %s", e.code, err_body[:300])
        return json.dumps({"error": f"Lookup service returned HTTP {e.code}", "detail": err_body[:300]})
    except urllib.error.URLError as e:
        logger.error("hermes-user-lookup connection error: %s", e.reason)
        return json.dumps({"error": f"Could not reach lookup service: {e.reason}"})
    except Exception as e:
        logger.error("hermes-user-lookup unexpected error: %s", e)
        return json.dumps({"error": str(e)})


def _find_user(query: str) -> str:
    """Search the employee registry by name, username, or email fragment."""
    return _call_n8n_user_lookup({"operation": "find", "query": query})


def _list_all() -> str:
    """Return all registered employees (telegram_id, username, email, display_name)."""
    return _call_n8n_user_lookup({"operation": "list_all"})


_USER_LOOKUP_TOOL_SCHEMA = {
    "name": "user_lookup_tool",
    "description": (
        "Employee directory tool. Look up colleagues by name/username to get their "
        "Telegram ID and email. Also returns the current user's own identity.\n\n"
        "Operations:\n"
        "  whoami      — return the current user's own telegram_id and username "
        "(no network call, reads from session context)\n"
        "  find        — search all registered employees by name, username, or email fragment; "
        "returns [{telegram_id, email, display_name, telegram_username}]\n"
        "  list_all    — return every registered employee\n\n"
        "Use telegram_id from find/whoami as the chat_id when sending Telegram messages to colleagues."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["whoami", "find", "list_all"],
                "description": "Operation to perform.",
            },
            "query": {
                "type": "string",
                "description": "Name, username, or email fragment to search for (required for find).",
            },
        },
        "required": ["operation"],
    },
}


def _check_available() -> bool:
    try:
        req = urllib.request.Request(
            f"{_N8N_BASE_URL}/healthz",
            headers={"User-Agent": "hermes-healthcheck"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def _register():
    from tools.registry import registry
    registry.register(
        name="user_lookup_tool",
        schema=_USER_LOOKUP_TOOL_SCHEMA,
        handler=_handle_user_lookup_tool,
        toolset="messaging",
        check_fn=_check_available,
        description="Employee directory: look up colleagues by name to get Telegram ID and email.",
    )


_register()
