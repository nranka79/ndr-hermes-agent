"""
token_auth tool — agent-facing interface for checking and initiating OAuth authorization.

This tool lets the agent:
  1. Check whether the current session user has a valid token for a given service.
  2. Obtain an OAuth URL so the user can authorize access.
  3. List which services the current user has authorized.
  4. Revoke the current user's own token for a service.

## Multi-account Google support

A user can authorize multiple Google accounts under different labels:
  - Primary account: service="google" (no account_label)
  - Secondary accounts: service="google" + account_label="gmail"|"ahfl"|"work"|...

Each label creates a separate vault slot (e.g. google-gmail, google-ahfl).

## Permission guardrails

Authorizing a secondary Google account (account_label provided) requires
  permissions.multi_google=true  in the user's registry entry.
Only ndr@draas.com and rnr@draas.com currently have this permission.

## Security design

The user identity is NEVER exposed as a tool parameter.
It is always read from HERMES_SESSION_USER_ID, which the gateway injects:
  - Telegram channel: injected by the Telegram platform handler
  - API / OpenUI: injected from X-Hermes-User-Email / X-Hermes-User-Id header
  - Terminal subprocesses: injected into os.environ by terminal_tool.py

This makes it architecturally impossible for the LLM to be prompt-injected into
accessing another user's tokens. The LLM can only check/authorize/revoke for
the currently authenticated session user.

The raw token is NEVER returned to the conversation. The vault daemon enforces
this at the protocol level — only the service-specific credential modules
(gws_auth.py, etc.) call vault.get_token(), and they use the token internally.
"""

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

# Valid account_label: lowercase alphanumeric + hyphens, 1-40 chars
_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")

# ---------------------------------------------------------------------------
# Tool schema — NO telegram_id or user_id parameter (by design)
# ---------------------------------------------------------------------------

TOKEN_AUTH_SCHEMA = {
    "name": "token_auth",
    "description": (
        "Check OAuth authorization status for the current user, get an authorization URL, "
        "list connected services, or revoke access for a specific service. "
        "Supported services: 'google' (Gmail, Calendar, Drive), 'kelsa', 'aws', and others. "
        "For users with multi-account Google permission, additional Google accounts can be "
        "authorized using the optional account_label parameter. "
        "Always check status before attempting to use a service. "
        "The user identity is determined automatically from the session — never specify it."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "op": {
                "type": "string",
                "enum": ["check", "authorize", "list", "revoke"],
                "description": (
                    "check — is the current user authorized for this service? "
                    "authorize — get the OAuth URL the user must open in a browser. "
                    "list — list all services this user has authorized. "
                    "revoke — delete the current user's token for this service."
                ),
            },
            "service": {
                "type": "string",
                "description": (
                    "The service to act on. Examples: 'google', 'kelsa', 'aws'. "
                    "Required for check, authorize, revoke. Optional for list."
                ),
            },
            "account_label": {
                "type": "string",
                "description": (
                    "For service='google' only: a short label for a secondary Google account "
                    "slot (e.g. 'gmail' for nishantranka@gmail.com, 'ahfl' for ndr@ahfl.in, "
                    "'work' for a work account). "
                    "Omit to use the primary Google account. "
                    "Only users with multi_google permission may use this parameter. "
                    "Use lowercase letters, digits and hyphens only."
                ),
            },
        },
        "required": ["op"],
    },
}


# ---------------------------------------------------------------------------
# Session identity helper
# ---------------------------------------------------------------------------

def _get_session_user_id() -> str | None:
    """
    Return the canonical user ID (primary email) for the current session.

    Reads HERMES_SESSION_USER_ID injected by the gateway — NEVER from tool arguments.
    Returns None if not set (unauthenticated / no session context).
    """
    try:
        from gateway.session_context import get_session_env
        uid = get_session_env("HERMES_SESSION_USER_ID", "")
    except Exception:
        uid = os.environ.get("HERMES_SESSION_USER_ID", "")
    return uid.strip() or None


# Backward-compat alias (used internally and imported by older code)
_get_session_telegram_id = _get_session_user_id


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

def _has_permission(user_id: str, permission: str) -> bool:
    """Return True if user_id has the named permission in their registry entry."""
    try:
        from tools._user_registry import get_user_config
        return bool(get_user_config(user_id).get("permissions", {}).get(permission, False))
    except Exception:
        return False


def _effective_service_key(service: str, account_label: str | None) -> tuple[str, str | None]:
    """Compute the vault service key from service name + optional account_label.

    Returns (vault_service_key, error_message_or_None).
    """
    if service != "google" or not account_label:
        return service, None

    label = account_label.strip().lower()
    # Normalize: strip "google-" prefix if user included it
    if label.startswith("google-"):
        label = label[len("google-"):]

    if not _LABEL_RE.match(label):
        return service, (
            f"Invalid account_label {account_label!r}. "
            "Use lowercase letters, digits and hyphens only (1-40 chars). "
            "Examples: 'gmail', 'ahfl', 'work'."
        )
    return f"google-{label}", None


# ---------------------------------------------------------------------------
# Tool handler
# ---------------------------------------------------------------------------

def token_auth_tool(op: str, service: str | None = None, account_label: str | None = None) -> str:
    """
    Handle a token_auth tool call from the agent.

    Returns a JSON string with the result. Raw tokens are NEVER included.
    The user identity comes exclusively from the session context.
    """
    uid = _get_session_user_id()
    if not uid:
        return json.dumps({
            "success": False,
            "error": (
                "No session identity found (HERMES_SESSION_USER_ID is not set). "
                "Via API/OpenUI: ensure X-Hermes-User-Email or X-Hermes-User-Id "
                "is sent in the request header. Via Telegram: this is injected automatically."
            ),
        })

    try:
        from tools.gws_vault_client import (
            has_token, delete_token, list_services, vault_is_available,
        )
    except ImportError as exc:
        return json.dumps({"success": False, "error": f"Vault client not available: {exc}"})

    if not vault_is_available():
        return json.dumps({
            "success": False,
            "error": "Token Vault daemon is not running. Start it: systemctl start gws-vault",
        })

    # ------------------------------------------------------------------
    # check: is the current user authorized for a service?
    # ------------------------------------------------------------------
    if op == "check":
        if not service:
            return json.dumps({"success": False, "error": "'service' is required for op=check"})
        service = service.lower().strip()

        vault_key, err = _effective_service_key(service, account_label)
        if err:
            return json.dumps({"success": False, "error": err})

        # Permission check for secondary Google accounts
        if vault_key != service and not _has_permission(uid, "multi_google"):
            return json.dumps({
                "success": False,
                "error": (
                    "Multi-account Google OAuth is not enabled for your account. "
                    "Contact an admin to enable it."
                ),
            })

        token_exists = has_token(uid, vault_key, session_uid=uid)

        if not token_exists:
            auth_url = _get_auth_url_if_supported(service, uid, vault_key)
            result = {
                "success": True,
                "authorized": False,
                "service": service,
                "vault_key": vault_key,
                "message": f"No {vault_key} token found. The user needs to authorize.",
            }
            if auth_url:
                result["auth_url"] = auth_url
                result["message"] += " Share the auth_url with the user."
            return json.dumps(result)

        return json.dumps({
            "success": True,
            "authorized": True,
            "service": service,
            "vault_key": vault_key,
            "message": f"{vault_key} is connected and ready.",
        })

    # ------------------------------------------------------------------
    # authorize: return the OAuth URL the user should open
    # ------------------------------------------------------------------
    elif op == "authorize":
        if not service:
            return json.dumps({"success": False, "error": "'service' is required for op=authorize"})
        service = service.lower().strip()

        vault_key, err = _effective_service_key(service, account_label)
        if err:
            return json.dumps({"success": False, "error": err})

        # Permission check for secondary Google accounts
        if vault_key != service and not _has_permission(uid, "multi_google"):
            return json.dumps({
                "success": False,
                "error": (
                    "Multi-account Google OAuth is not enabled for your account. "
                    "Contact an admin (ndr@draas.com or rnr@draas.com) to enable it."
                ),
            })

        auth_url = _get_auth_url_if_supported(service, uid, vault_key)
        if not auth_url:
            return json.dumps({
                "success": False,
                "error": (
                    f"OAuth authorization is not configured for service '{service}'. "
                    "Supported services: google. Others require manual token setup."
                ),
            })
        instructions = (
            "Send this URL to the user. After they open it and grant access, "
            "Google will redirect to the callback URL and the token will be stored "
            f"automatically under slot '{vault_key}'. "
            "Run token_auth check afterward to confirm."
        )
        return json.dumps({
            "success": True,
            "service": service,
            "vault_key": vault_key,
            "auth_url": auth_url,
            "instructions": instructions,
        })

    # ------------------------------------------------------------------
    # list: which services does the current user have tokens for?
    # ------------------------------------------------------------------
    elif op == "list":
        services = list_services(uid, session_uid=uid)
        return json.dumps({
            "success": True,
            "connected_services": services,
            "message": (
                f"This user has tokens for: {', '.join(services)}"
                if services else "No services connected yet."
            ),
        })

    # ------------------------------------------------------------------
    # revoke: delete the current user's own token for a service
    # ------------------------------------------------------------------
    elif op == "revoke":
        if not service:
            return json.dumps({"success": False, "error": "'service' is required for op=revoke"})
        service = service.lower().strip()

        vault_key, err = _effective_service_key(service, account_label)
        if err:
            return json.dumps({"success": False, "error": err})

        # Only allow revoking own token — the session user IS the target
        # (no way for LLM to revoke another user's token: no user param in schema)
        try:
            deleted = delete_token(uid, vault_key)
            return json.dumps({
                "success": True,
                "service": service,
                "vault_key": vault_key,
                "deleted": deleted,
                "message": (
                    f"{vault_key} token revoked."
                    if deleted else
                    f"No {vault_key} token was stored."
                ),
            })
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Failed to revoke {vault_key} token: {exc}"})

    else:
        return json.dumps({"success": False, "error": f"Unknown op: {op!r}"})


def _get_auth_url_if_supported(
    service: str,
    user_id: str,
    vault_key: str | None = None,
) -> str | None:
    """
    Return an OAuth authorization URL for *service* if automated OAuth is configured.
    Returns None if the service requires manual token setup.

    Args:
        service:   Top-level service name, e.g. "google".
        user_id:   Canonical user ID from session (HERMES_SESSION_USER_ID).
        vault_key: Full vault service key, e.g. "google-gmail". Defaults to service.
    """
    service_key = vault_key or service
    if service == "google":
        try:
            from tools.gws_auth import get_auth_url
            return get_auth_url(user_id, service_key)
        except Exception as exc:
            logger.warning("Could not generate Google auth URL: %s", exc)
            return None
    return None


from tools.registry import registry

registry.register(
    name="token_auth",
    toolset="gws",
    schema=TOKEN_AUTH_SCHEMA,
    handler=lambda args, **kw: token_auth_tool(
        op=args.get("op", ""),
        service=args.get("service"),
        account_label=args.get("account_label"),
    ),
    emoji="🔑",
)
