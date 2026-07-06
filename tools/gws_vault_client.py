"""
Token Vault client library — generic per-user, per-service token store,
plus canonical identity resolution.

Used by ``tools/gws_auth.py`` and any future service-specific module (STT
vocabulary, Slack tokens, Kelsa tokens, browser-use tokens, …) to talk to
the ``gws-vault-server`` daemon over a Unix domain socket.

The vault stores data in a directory that Hermes itself cannot read
directly (owned by the ``gws-vault`` OS user, isolated from the Hermes
process). Hermes accesses it ONLY through this client -> socket -> daemon
path, so:
  - Raw tokens/secrets are never written to HERMES_HOME or any
    Hermes-owned path.
  - Cross-user reads are blocked by the daemon (``session_uid`` must equal
    ``user_id`` — enforced server-side, not by this client).
  - Writes (set/delete/add_identity) require the ``GWS_VAULT_SECRET``
    shared secret, known only to trusted backend processes (the
    ``hermes`` container, the ``free-whisper`` microservice) — never sent
    to the LLM, never given to a browser/frontend.
  - Every call fetches fresh from the vault — nothing is cached across
    calls in this client. Callers should not hold onto raw token values
    beyond the single API call that needs them.

Storage path in vault: ``{VAULT_TOKEN_DIR}/{user_id}/{service}.json``
  e.g. .../7449813913/google.json   (Telegram-registered user)
       .../ndr@draas.com/vocab.json (email-identified user, STT vocab)
       .../ndr@draas.com/identity.json (reserved — see resolve/add_identity/get_identity)

Identity model:
  ``user_id`` is the *canonical internal user ID* for a person — in
  practice, their primary email (e.g. ``ndr@draas.com``). A person may
  have many raw channel identifiers (a Telegram numeric ID, one or more
  emails across domains, a Slack ID, …), all resolving to the same
  canonical ``user_id``.

  The vault itself owns this mapping now (service name ``"identity"``,
  reserved — not accessible via plain get/set/has_token/delete). Any
  microservice, not just Hermes, can turn a raw identifier into the
  canonical ``user_id`` via :func:`resolve`, with zero dependency on
  Hermes's own ``users.json`` or any Hermes-specific code. Only a
  trusted admin-side tool (hardcoded identity check, not just a data
  flag) should ever call :func:`add_identity` to register a new mapping.

Environment variables:
  GWS_VAULT_SOCKET   Unix socket path (default: /run/gws-vault/vault.sock)
  GWS_VAULT_SECRET   Shared secret for write operations (set/delete/add_identity)
"""

from __future__ import annotations

import json
import os
import socket
from typing import Any, Dict, List, Optional

VAULT_SOCKET_PATH = os.environ.get("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")
VAULT_SECRET = os.environ.get("GWS_VAULT_SECRET", "")
_TIMEOUT = 10.0


class VaultError(RuntimeError):
    """Raised when the vault returns an error response."""


class VaultUnauthorizedError(VaultError):
    """Raised when the vault denies access (wrong session user or invalid secret)."""


class VaultNoTokenError(VaultError):
    """Raised when no token/data exists for the requested user/service combination."""
    needs_auth: bool = True


def _call(req: dict) -> dict:
    """Send one newline-delimited-JSON request to the vault daemon."""
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
        if not buf:
            raise VaultError("Vault closed connection without a response")
        return json.loads(buf.decode("utf-8").strip())
    finally:
        try:
            s.close()
        except Exception:
            pass


def _current_session_uid() -> str:
    """
    Return the current session's internal user ID from context vars.

    Reads ``HERMES_SESSION_USER_ID`` via session_context (concurrency-safe
    in the gateway's async event loop) and falls back to ``os.environ``
    (terminal subprocesses, CLI, cron). Callers outside the Hermes gateway
    (e.g. free-whisper-svc) should pass ``session_uid``/``user_id``
    explicitly instead of relying on this fallback.
    """
    try:
        from gateway.session_context import get_session_env
        uid = get_session_env("HERMES_SESSION_USER_ID", "")
    except Exception:
        uid = os.environ.get("HERMES_SESSION_USER_ID", "")
    return uid.strip()


def get_token(user_id: str, service: str, *, session_uid: Optional[str] = None) -> str:
    """Return the raw stored JSON string for ``user_id``/``service``.

    Raises :class:`VaultNoTokenError` if nothing is stored yet, or
    :class:`VaultUnauthorizedError` if ``session_uid`` doesn't match
    ``user_id`` (the vault only allows self-reads).
    """
    uid = session_uid if session_uid is not None else _current_session_uid()
    resp = _call({"op": "get", "user_id": user_id, "service": service, "session_uid": uid})
    if not resp.get("ok"):
        if resp.get("needs_auth"):
            raise VaultNoTokenError(resp.get("error", "No data stored"))
        raise VaultUnauthorizedError(resp.get("error", "Vault get failed"))
    return resp["token_json"]


def set_token(user_id: str, service: str, token_json: str) -> None:
    """Store ``token_json`` for ``user_id``/``service``. Requires GWS_VAULT_SECRET."""
    resp = _call({
        "op": "set",
        "user_id": user_id,
        "service": service,
        "token_json": token_json,
        "vault_secret": VAULT_SECRET,
    })
    if not resp.get("ok"):
        raise VaultError(resp.get("error", "Vault set failed"))


def delete_token(user_id: str, service: str) -> bool:
    """Delete stored data for ``user_id``/``service``. Requires GWS_VAULT_SECRET.

    Returns True if something was actually deleted, False if nothing existed.
    """
    resp = _call({
        "op": "delete",
        "user_id": user_id,
        "service": service,
        "vault_secret": VAULT_SECRET,
    })
    if not resp.get("ok"):
        raise VaultError(resp.get("error", "Vault delete failed"))
    return bool(resp.get("deleted", False))


def has_token(user_id: str, service: str, *, session_uid: Optional[str] = None) -> bool:
    """Return True if data exists for ``user_id``/``service``.

    Never raises on the "not authorized" / "not found" cases — returns
    False instead, since this is meant for cheap existence checks.
    """
    uid = session_uid if session_uid is not None else _current_session_uid()
    resp = _call({"op": "has_token", "user_id": user_id, "service": service, "session_uid": uid})
    if not resp.get("ok"):
        return False
    return bool(resp.get("has_token", False))


def list_services(user_id: str, *, session_uid: Optional[str] = None) -> List[str]:
    """Return the sorted list of service names stored for ``user_id``.

    Never includes the reserved ``"identity"`` entry — see
    :func:`get_identity` for that.
    """
    uid = session_uid if session_uid is not None else _current_session_uid()
    resp = _call({"op": "list_services", "user_id": user_id, "session_uid": uid})
    if not resp.get("ok"):
        raise VaultUnauthorizedError(resp.get("error", "Vault list_services failed"))
    return resp.get("services", [])


def resolve(identity_type: str, identity_value: str) -> Optional[str]:
    """Resolve a raw identifier (telegram/email/slack/draas_user_id) to the
    canonical ``user_id`` that owns it, or None if not found.

    No authorization required — this only ever returns a canonical
    user_id, never token/secret material. Any microservice can call this
    directly; the real security boundary stays at :func:`get_token`
    (session_uid must equal the resolved user_id).
    """
    resp = _call({"op": "resolve", "identity_type": identity_type, "identity_value": identity_value})
    if not resp.get("ok"):
        return None
    return resp.get("user_id")


def add_identity(
    user_id: str,
    identity_type: str,
    identity_value: str,
    *,
    name: Optional[str] = None,
    role: Optional[str] = None,
    permissions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Associate a new raw identifier with ``user_id``. Requires GWS_VAULT_SECRET.

    Creates the user's identity record if it doesn't exist yet. Rejects
    the call if ``identity_value`` already belongs to a *different*
    user_id (raises :class:`VaultError`).

    This is an admin-provisioning operation. The vault_secret gates it at
    the transport level, but callers (e.g. a Hermes ``manage_user``-style
    tool) should ALSO independently hard-check the calling session against
    a specific, hardcoded admin identity before ever reaching this call —
    the shared secret alone should not be the only gate for a
    user-facing/LLM-facing tool.
    """
    req: Dict[str, Any] = {
        "op": "add_identity",
        "user_id": user_id,
        "identity_type": identity_type,
        "identity_value": identity_value,
        "vault_secret": VAULT_SECRET,
    }
    if name is not None:
        req["name"] = name
    if role is not None:
        req["role"] = role
    if permissions is not None:
        req["permissions"] = permissions
    resp = _call(req)
    if not resp.get("ok"):
        raise VaultError(resp.get("error", "Vault add_identity failed"))
    return resp.get("identity", {})


def get_identity(user_id: str, *, session_uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Return the caller's own identity/profile record (name, role,
    permissions, all known aliases), or None if not found.

    Self-service only — same session_uid==user_id rule as :func:`get_token`.
    """
    uid = session_uid if session_uid is not None else _current_session_uid()
    resp = _call({"op": "get_identity", "user_id": user_id, "session_uid": uid})
    if not resp.get("ok"):
        return None
    return resp.get("identity")
