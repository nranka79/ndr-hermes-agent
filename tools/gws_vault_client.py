"""
Token vault client — Unix-socket transport to gws-vault-server.

Tokens are stored exclusively inside the vault host process at
  /opt/gws-vault/tokens/{user_id}/{service}.json
on the Hetzner host, and exposed via a Unix domain socket at
  /run/gws-vault/vault.sock
that the hermes container bind-mounts.

Wire protocol: newline-delimited JSON over the socket. One request is one
JSON object terminated with a single ``\\n``; one response is one JSON
object terminated with a single ``\\n``. The server is
``/usr/local/bin/gws-vault-server`` on the host.

Operations:
  get          {"op":"get","user_id":"...","service":"...","session_uid":"..."}
  set          {"op":"set","user_id":"...","service":"...","token_json":"...","vault_secret":"..."}
  has_token    {"op":"has_token","user_id":"...","service":"...","session_uid":"..."|"vault_secret":"..."}
  delete       {"op":"delete","user_id":"...","service":"...","vault_secret":"..."}
  list_services {"op":"list_services","user_id":"...","session_uid":"..."}
  resolve      {"op":"resolve","identity_type":"...","identity_value":"..."}
  add_identity {"op":"add_identity","user_id":"...","identity_type":"...","identity_value":"...","vault_secret":"..."}
  get_identity {"op":"get_identity","user_id":"...","session_uid":"..."}

Authorization:
  * Read ops (``get``, ``list_services``, ``get_identity``) — ``session_uid``
    MUST equal ``user_id``. The server enforces this via ``SO_PEERCRED``.
  * ``has_token`` accepts either ``session_uid`` (self) or ``vault_secret``
    (admin).
  * Write ops (``set``, ``delete``, ``add_identity``) — ``vault_secret`` MUST
    match ``GWS_VAULT_SECRET``. Hermes never calls these directly — only the
    OAuth callback handler does.

All reads and writes go through this client so the hermes process
(and any LLM-generated code it spawns) never touches token files directly.

Environment variables:
  GWS_VAULT_SOCKET   Unix socket path (e.g. /run/gws-vault/vault.sock)
  GWS_VAULT_SECRET   Shared secret for write operations
  VAULT_SECRET       Fallback name for the same secret

Service-name format (enforced by the server): ``^[a-z][a-z0-9-]{0,49}$`` —
lowercase, starts with a letter, alphanumeric + hyphen only. Use
``google-gmail`` / ``google-ahfl`` / etc. The legacy ``gws:user@domain``
format is NOT accepted by the server.
"""

from __future__ import annotations

import json
import os
import socket
from typing import Any, Dict, List, Optional

VAULT_SOCKET = os.environ.get("GWS_VAULT_SOCKET", "").strip()
VAULT_SECRET = (
    os.environ.get("GWS_VAULT_SECRET")
    or os.environ.get("VAULT_SECRET")
    or ""
)


class VaultError(RuntimeError):
    """Raised when a vault operation fails."""


class VaultUnauthorizedError(VaultError):
    """Raised when access is denied (bad vault secret or session mismatch)."""


class VaultNoTokenError(VaultError):
    """Raised when no token exists for the requested user/service."""
    needs_auth: bool = True


def _connect() -> socket.socket:
    """Open a fresh Unix-socket connection. Caller must close()."""
    if not VAULT_SOCKET:
        raise VaultError(
            "GWS_VAULT_SOCKET is not set — cannot reach the vault. "
            "Bind-mount /run/gws-vault and set the env var, or run where the "
            "socket is available."
        )
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(10)
    try:
        s.connect(VAULT_SOCKET)
    except OSError as exc:
        raise VaultError(f"Vault socket unreachable at {VAULT_SOCKET}: {exc}") from exc
    return s


def _send_recv(payload: dict) -> dict:
    """Send one JSON-line request, read one JSON-line response."""
    data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    sock = _connect()
    try:
        sock.sendall(data)
        buf = b""
        # The server sends exactly one JSON line + "\n" per request. Read
        # until we see the newline or the connection closes.
        while b"\n" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
            # Hard cap so a misbehaving server can't OOM us.
            if len(buf) > 2_000_000:
                raise VaultError("Vault response exceeded 2MB safety cap")
    finally:
        try:
            sock.close()
        except Exception:
            pass

    if not buf:
        raise VaultError("Vault closed the connection without sending a response")

    line = buf.split(b"\n", 1)[0]
    try:
        return json.loads(line.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise VaultError(f"Vault sent non-JSON response: {line!r}") from exc


def _is_unauthorized(error_msg: str) -> bool:
    """Heuristic — the server uses several phrasings for auth failures."""
    msg = (error_msg or "").lower()
    return (
        "unauthorized" in msg
        or "invalid vault secret" in msg
        or "session user does not match" in msg
    )


def _raise_for_response(resp: dict) -> None:
    """Map a {"ok": false, "error": "..."} response to the right exception."""
    if resp.get("ok"):
        return
    error = resp.get("error", "unknown vault error")
    if _is_unauthorized(error):
        raise VaultUnauthorizedError(error)
    if resp.get("needs_auth"):
        raise VaultNoTokenError(error)
    raise VaultError(error)


def get_token(user_id: str, service: str, *, session_uid: Optional[str] = None) -> str:
    """Return the full stored token JSON string for user_id/service.

    Authorization: ``session_uid`` MUST equal ``user_id`` (enforced server-side
    via ``SO_PEERCRED``). If ``session_uid`` is not provided, ``user_id`` is
    used as the session — i.e. each user reads their own tokens.

    Raises ``VaultNoTokenError`` if the token doesn't exist (and the response
    carries ``needs_auth=True`` so the caller can drive the OAuth flow).
    """
    uid = str(user_id).strip()
    sess = str(session_uid).strip() if session_uid else uid
    resp = _send_recv({
        "op": "get",
        "user_id": uid,
        "service": str(service).strip(),
        "session_uid": sess,
    })
    _raise_for_response(resp)
    return resp.get("token_json", "")


def get_access_token(user_id: str, service: str) -> dict:
    """Return the full stored token as a dict for user_id/service.

    The vault does not refresh the access token server-side — it returns the
    stored ``token_json`` (which includes ``refresh_token``) and the caller
    is responsible for refreshing via the Google OAuth library when the
    access token expires. This matches the older client semantics where
    callers (e.g. ``noun_resolver.py``) already build a
    ``google.oauth2.credentials.Credentials`` from the dict.
    """
    raw = get_token(user_id, service, session_uid=str(user_id).strip())
    if not raw:
        raise VaultNoTokenError(
            f"Vault returned empty token_json for user={user_id} service={service}"
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VaultError(f"Vault stored invalid JSON for {user_id}/{service}: {exc}") from exc


def set_token(user_id: str, service: str, token_json: str) -> None:
    """Store token_json in the vault for user_id/service.

    Requires ``GWS_VAULT_SECRET`` in the env. Hermes code that needs to write
    a fresh token after an OAuth flow should go through the OAuth callback
    handler, not call this directly.
    """
    resp = _send_recv({
        "op": "set",
        "user_id": str(user_id).strip(),
        "service": str(service).strip(),
        "token_json": token_json,
        "vault_secret": VAULT_SECRET,
    })
    _raise_for_response(resp)


def delete_token(user_id: str, service: str) -> bool:
    """Delete stored token. Returns True if something was deleted.

    Requires ``GWS_VAULT_SECRET``.
    """
    resp = _send_recv({
        "op": "delete",
        "user_id": str(user_id).strip(),
        "service": str(service).strip(),
        "vault_secret": VAULT_SECRET,
    })
    _raise_for_response(resp)
    return bool(resp.get("deleted"))


def has_token(user_id: str, service: str, *, session_uid: Optional[str] = None) -> bool:
    """Return True if a token exists for user_id/service.

    Accepts either ``session_uid`` (self-check) or ``GWS_VAULT_SECRET`` (admin
    check) — the server picks whichever it finds first. If neither is set,
    the server returns Unauthorized.
    """
    uid = str(user_id).strip()
    payload: Dict[str, Any] = {
        "op": "has_token",
        "user_id": uid,
        "service": str(service).strip(),
    }
    if session_uid:
        payload["session_uid"] = str(session_uid).strip()
    elif VAULT_SECRET:
        payload["vault_secret"] = VAULT_SECRET
    else:
        # Default to self-check so callers in normal flow always work.
        payload["session_uid"] = uid

    resp = _send_recv(payload)
    _raise_for_response(resp)
    return bool(resp.get("has_token"))


def list_services(user_id: str, *, session_uid: Optional[str] = None) -> List[str]:
    """Return service names with stored tokens for user_id.

    Authorization: ``session_uid`` MUST equal ``user_id``.
    """
    uid = str(user_id).strip()
    sess = str(session_uid).strip() if session_uid else uid
    resp = _send_recv({
        "op": "list_services",
        "user_id": uid,
        "session_uid": sess,
    })
    _raise_for_response(resp)
    return list(resp.get("services", []))


def resolve(identity_type: str, identity_value: str) -> Optional[str]:
    """Resolve an (identity_type, identity_value) pair to a canonical user_id.

    No auth required — the server only returns a user_id, never a token.
    Returns ``None`` if no match.
    """
    resp = _send_recv({
        "op": "resolve",
        "identity_type": str(identity_type).strip(),
        "identity_value": str(identity_value).strip(),
    })
    if not resp.get("ok"):
        if resp.get("not_found"):
            return None
        _raise_for_response(resp)
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
    """Register an (identity_type, identity_value) alias for user_id.

    Requires ``GWS_VAULT_SECRET``. Returns the updated identity record.
    """
    payload: Dict[str, Any] = {
        "op": "add_identity",
        "user_id": str(user_id).strip(),
        "identity_type": str(identity_type).strip(),
        "identity_value": str(identity_value).strip(),
        "vault_secret": VAULT_SECRET,
    }
    if name is not None:
        payload["name"] = name
    if role is not None:
        payload["role"] = role
    if permissions is not None:
        payload["permissions"] = permissions
    resp = _send_recv(payload)
    _raise_for_response(resp)
    return resp.get("identity", {})


def get_identity(user_id: str, *, session_uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Return the identity record (name, role, permissions, aliases) for user_id.

    Authorization: ``session_uid`` MUST equal ``user_id``. Returns ``None`` if
    the user has no identity record.
    """
    uid = str(user_id).strip()
    sess = str(session_uid).strip() if session_uid else uid
    resp = _send_recv({
        "op": "get_identity",
        "user_id": uid,
        "session_uid": sess,
    })
    if not resp.get("ok"):
        if resp.get("not_found"):
            return None
        _raise_for_response(resp)
    return resp.get("identity")
