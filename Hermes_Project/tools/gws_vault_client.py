"""
Token Vault client library — generic per-user, per-service OAuth token store.

Used by gws_auth.py and any future service-specific auth modules to communicate
with the token-vault-server daemon over a Unix domain socket.

The vault stores tokens in a directory that Hermes itself cannot read directly
(owned by the gws-vault OS user). Hermes accesses tokens ONLY through this
client → socket → daemon path, so:
  - Tokens are never written to HERMES_HOME or any Hermes-owned path.
  - Cross-user access is blocked by the daemon (session_uid must match user_id).
  - Write access requires the GWS_VAULT_SECRET shared secret.
  - The LLM never sees raw token JSON — it goes through service-specific wrappers.

Token path in vault: {VAULT_TOKEN_DIR}/{user_id}/{service}.json
  e.g. .../7449813913/google.json   (existing Telegram-registered user)
       .../7449813913/kelsa.json

Identity model:
  HERMES_SESSION_USER_ID always holds the *internal user ID* (resolved from
  whichever channel the request arrived on — Telegram, OpenUI/email, Slack, …).
  The vault uses this internal user ID as its storage key. Channel-specific
  identifiers (telegram numeric ID, email, etc.) are resolved to the internal
  user ID by _identity_resolver.resolve_user_id() before reaching this module.

Environment variables:
  GWS_VAULT_SOCKET   Unix socket path (default: /run/gws-vault/vault.sock)
  GWS_VAULT_SECRET   Shared secret for write operations
"""

import json
import os
import socket
from typing import List, Optional

VAULT_SOCKET_PATH = os.environ.get("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")
VAULT_SECRET = os.environ.get("GWS_VAULT_SECRET", "")
_TIMEOUT = 10.0


class VaultError(RuntimeError):
    """Raised when the vault returns an error response."""


class VaultUnauthorizedError(VaultError):
    """Raised when the vault denies access (wrong session user or invalid secret)."""


class VaultNoTokenError(VaultError):
    """Raised when no token exists for the requested user/service combination."""
    needs_auth: bool = True


def _call(req: dict) -> dict:
    """Send one request to the vault and return the response dict."""
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(_TIMEOUT)
    try:
        s.connect(VAULT_SOCKET_PATH)
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        return json.loads(buf.decode("utf-8").strip())
    finally:
        try:
            s.close()
        except Exception:
            pass


def _current_session_uid() -> str:
    """
    Return the current session's internal user ID from context vars.

    Reads HERMES_SESSION_USER_ID via session_context (concurrency-safe in the
    gateway's async event loop) and falls back to os.environ (terminal
    subprocesses, CLI, cron). This value is ALWAYS the internal user ID
    resolved from the originating channel — never a raw channel identifier.
    """
    try:
        from gateway.session_context import get_session_env
        uid = get_session_env("HERMES_SESSION_USER_ID", "")
    except Exception:
        uid = os.environ.get("HERMES_SESSION_USER_ID", "")
    return uid.strip()


def _build_uid_fields(user_id: str) -> dict:
    """Return the user identity fields for a vault protocol request.

    Sends both ``user_id`` (new) and ``telegram_id`` (legacy alias) so the
    request works with both the current vault server and any older deployment
    that hasn't been updated yet.
    """
    return {"user_id": user_id, "telegram_id": user_id}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_token(user_id: str, service: str, session_uid: Optional[str] = None) -> str:
    """
    Retrieve the stored token JSON for *user_id* / *service*.

    *user_id* is the internal user ID (from HERMES_SESSION_USER_ID).
    *session_uid* defaults to the current HERMES_SESSION_USER_ID.
    The vault blocks the request unless session_uid == user_id.

    Returns the raw token JSON string.
    Raises VaultNoTokenError      — no token; user must authorize
    Raises VaultUnauthorizedError — session user != requested user
    Raises VaultError             — other vault errors
    Raises ConnectionRefusedError / FileNotFoundError — vault not running
    """
    uid = session_uid if session_uid is not None else _current_session_uid()
    resp = _call({
        "op": "get",
        **_build_uid_fields(str(user_id)),
        "service": str(service),
        "session_uid": uid,
    })
    if resp.get("ok"):
        return resp["token_json"]
    if resp.get("needs_auth"):
        err = VaultNoTokenError(resp.get("error", "No token — user must authorize"))
        err.needs_auth = True
        raise err
    if "Unauthorized" in resp.get("error", ""):
        raise VaultUnauthorizedError(resp.get("error", "Unauthorized"))
    raise VaultError(resp.get("error", "Vault error"))


def set_token(
    user_id: str,
    service: str,
    token_json: str,
    vault_secret: Optional[str] = None,
) -> None:
    """
    Store (or replace) the token for *user_id* / *service*.

    Requires the GWS_VAULT_SECRET shared secret (read from env by default).
    Called by the OAuth callback handler AFTER the token exchange — the LLM
    never calls this function directly.
    """
    secret = vault_secret if vault_secret is not None else VAULT_SECRET
    resp = _call({
        "op": "set",
        **_build_uid_fields(str(user_id)),
        "service": str(service),
        "token_json": token_json,
        "vault_secret": secret,
    })
    if not resp.get("ok"):
        if "Unauthorized" in resp.get("error", ""):
            raise VaultUnauthorizedError(resp.get("error", "Unauthorized"))
        raise VaultError(resp.get("error", "Vault error"))


def has_token(
    user_id: str,
    service: str,
    session_uid: Optional[str] = None,
    vault_secret: Optional[str] = None,
) -> bool:
    """
    Return True if a token exists for *user_id* / *service*.

    Accepts either session_uid (owner checking own status) or vault_secret
    (admin / callback handler). Returns False if vault is unreachable (fail-open).
    """
    uid = session_uid if session_uid is not None else _current_session_uid()
    secret = vault_secret if vault_secret is not None else VAULT_SECRET
    try:
        resp = _call({
            "op": "has_token",
            **_build_uid_fields(str(user_id)),
            "service": str(service),
            "session_uid": uid,
            "vault_secret": secret,
        })
        return bool(resp.get("has_token"))
    except Exception:
        return False


def delete_token(
    user_id: str,
    service: str,
    vault_secret: Optional[str] = None,
) -> bool:
    """
    Delete the token for *user_id* / *service*. Requires vault_secret.
    Returns True if a token existed and was deleted.
    """
    secret = vault_secret if vault_secret is not None else VAULT_SECRET
    resp = _call({
        "op": "delete",
        **_build_uid_fields(str(user_id)),
        "service": str(service),
        "vault_secret": secret,
    })
    if not resp.get("ok"):
        raise VaultError(resp.get("error", "Vault error"))
    return bool(resp.get("deleted"))


def list_services(user_id: str, session_uid: Optional[str] = None) -> List[str]:
    """
    List service names that have stored tokens for *user_id*.
    Returns [] if vault is unreachable (fail-open).
    """
    uid = session_uid if session_uid is not None else _current_session_uid()
    try:
        resp = _call({
            "op": "list_services",
            **_build_uid_fields(str(user_id)),
            "session_uid": uid,
        })
        return resp.get("services", []) if resp.get("ok") else []
    except Exception:
        return []


def vault_is_available() -> bool:
    """Return True if the vault daemon is running and responsive."""
    if not os.path.exists(VAULT_SOCKET_PATH):
        return False
    try:
        resp = _call({
            "op": "has_token",
            "user_id": "000000",
            "telegram_id": "000000",
            "service": "ping",
            "vault_secret": "__ping__",
        })
        return isinstance(resp, dict)
    except Exception:
        return False
