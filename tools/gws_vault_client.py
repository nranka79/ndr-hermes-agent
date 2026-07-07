"""
Token vault client — HTTP backend (gws-vault at 127.0.0.1:8000).

Tokens are stored exclusively inside the vault container at
  /data/private-tokens/{user_id}/{service}.json
which maps to the host path /opt/hermes-gws-vault-data/private-tokens/
and is NOT mounted into the hermes container.

All reads and writes go through the vault HTTP API so the hermes process
(and any LLM-generated code it spawns) never touches token files directly.

Environment variables:
  VAULT_URL          Base URL of gws-vault (default: http://127.0.0.1:8000)
  GWS_VAULT_SECRET   Shared secret (X-Vault-Secret header)
  VAULT_SECRET       Fallback name for the same secret
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

VAULT_URL = os.environ.get("VAULT_URL", "http://127.0.0.1:8000")
VAULT_SECRET = (
    os.environ.get("GWS_VAULT_SECRET")
    or os.environ.get("VAULT_SECRET")
    or ""
)


class VaultError(RuntimeError):
    """Raised when a vault operation fails."""


class VaultUnauthorizedError(VaultError):
    """Raised when access is denied (bad vault secret)."""


class VaultNoTokenError(VaultError):
    """Raised when no token exists for the requested user/service."""
    needs_auth: bool = True


def _post(endpoint: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{VAULT_URL}{endpoint}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Vault-Secret": VAULT_SECRET,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        try:
            detail = json.loads(body_bytes).get("detail", body_bytes.decode())
        except Exception:
            detail = body_bytes.decode()
        if e.code == 401 or e.code == 403:
            raise VaultUnauthorizedError(f"Vault auth failed: {detail}")
        if e.code == 404:
            raise VaultNoTokenError(detail)
        raise VaultError(f"Vault HTTP {e.code}: {detail}")
    except Exception as exc:
        raise VaultError(f"Vault unreachable at {VAULT_URL}: {exc}") from exc


def _get(path: str) -> dict:
    req = urllib.request.Request(
        f"{VAULT_URL}{path}",
        headers={"X-Vault-Secret": VAULT_SECRET},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        try:
            detail = json.loads(body_bytes).get("detail", body_bytes.decode())
        except Exception:
            detail = body_bytes.decode()
        if e.code == 404:
            raise VaultNoTokenError(detail)
        raise VaultError(f"Vault HTTP {e.code}: {detail}")
    except Exception as exc:
        raise VaultError(f"Vault unreachable at {VAULT_URL}: {exc}") from exc


def get_token(user_id: str, service: str, *, session_uid: Optional[str] = None) -> str:
    """Return the full stored token JSON string for user_id/service.

    Uses POST /v1/token/raw which returns the complete authorized_user JSON
    (including refresh_token) needed to rebuild google.oauth2.credentials.Credentials.
    """
    del session_uid  # API compat
    result = _post("/v1/token/raw", {
        "vault_user_id": str(user_id).strip(),
        "service": str(service).strip(),
    })
    return json.dumps(result)


def get_access_token(user_id: str, service: str) -> dict:
    """Return a fresh access token dict from vault.

    Vault refreshes the token internally if expired.
    Returns: {"access_token": "ya29...", "expires_at": "...", "scopes": [...]}
    """
    return _post("/v1/token", {
        "vault_user_id": str(user_id).strip(),
        "service": str(service).strip(),
    })


def set_token(user_id: str, service: str, token_json: str) -> None:
    """Store token_json in the vault for user_id/service.

    Uses POST /v1/token/store. The vault writes to its own private
    storage, not to the hermes-data filesystem.
    """
    _post("/v1/token/store", {
        "vault_user_id": str(user_id).strip(),
        "service": str(service).strip(),
        "token": json.loads(token_json),
    })


def delete_token(user_id: str, service: str) -> bool:
    """Delete stored token. Returns True if something was deleted."""
    try:
        _post("/v1/token/delete", {
            "vault_user_id": str(user_id).strip(),
            "service": str(service).strip(),
        })
        return True
    except VaultNoTokenError:
        return False


def has_token(user_id: str, service: str, *, session_uid: Optional[str] = None) -> bool:
    """Return True if a token exists for user_id/service."""
    del session_uid
    try:
        _post("/v1/token/raw", {
            "vault_user_id": str(user_id).strip(),
            "service": str(service).strip(),
        })
        return True
    except VaultNoTokenError:
        return False


def list_services(user_id: str, *, session_uid: Optional[str] = None) -> List[str]:
    """Return service names with stored tokens for user_id."""
    del session_uid
    try:
        result = _get(f"/v1/users/{str(user_id).strip()}/services")
        return result.get("services", [])
    except Exception:
        return []


def resolve(_identity_type: str, _identity_value: str) -> Optional[str]:
    """Stub — use vault identity API directly for identity resolution."""
    return None


def add_identity(
    _user_id: str,
    _identity_type: str,
    _identity_value: str,
    *,
    name: Optional[str] = None,
    role: Optional[str] = None,
    permissions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Stub — identity provisioning not implemented in this client."""
    del name, role, permissions
    raise VaultError("add_identity not implemented in vault HTTP client")


def get_identity(_user_id: str, *, session_uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Stub — identity lookup not implemented in this client."""
    del session_uid
    return None
