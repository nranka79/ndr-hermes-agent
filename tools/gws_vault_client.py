"""
Token vault client — file-based backend.

Tokens are stored at:
    {HERMES_HOME}/users/{user_id}/{service}.json

The vault container (hermes-gws-vault-1) mounts this same directory
read-only at /data/tokens, so it can still serve access-token refreshes
for the gws-service. All writes go directly via this client.

Environment variables:
  HERMES_HOME        Root data dir (default: /data/hermes)
  GWS_VAULT_SECRET   Kept for API compatibility; unused in file backend
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

VAULT_SECRET = os.environ.get("GWS_VAULT_SECRET", "")
_HERMES_HOME = os.environ.get("HERMES_HOME", "/data/hermes")


class VaultError(RuntimeError):
    """Raised when a vault operation fails."""


class VaultUnauthorizedError(VaultError):
    """Raised when access is denied."""


class VaultNoTokenError(VaultError):
    """Raised when no token exists for the requested user/service."""
    needs_auth: bool = True


def _users_dir() -> Path:
    return Path(os.environ.get("HERMES_HOME", _HERMES_HOME)) / "users"


def _token_path(user_id: str, service: str) -> Path:
    """Resolve the on-disk token path for a user+service pair.

    Legacy: bare "gws" or "google" service uses gws_token.json if it exists.
    Named services (e.g. "google-draas") use {service}.json.
    """
    safe_uid = str(user_id).strip()
    safe_svc = str(service).strip()
    user_dir = _users_dir() / safe_uid
    if safe_svc in ("gws", "google"):
        legacy = user_dir / "gws_token.json"
        if legacy.exists():
            return legacy
    return user_dir / f"{safe_svc}.json"


def _current_session_uid() -> str:
    try:
        from gateway.session_context import get_session_env
        uid = get_session_env("HERMES_SESSION_USER_ID", "")
    except Exception:
        uid = os.environ.get("HERMES_SESSION_USER_ID", "")
    return uid.strip()


def get_token(user_id: str, service: str, *, session_uid: Optional[str] = None) -> str:
    """Return the raw stored JSON string for ``user_id``/``service``."""
    del session_uid  # kept for API compatibility with the old socket-based client
    path = _token_path(user_id, service)
    if not path.exists():
        raise VaultNoTokenError(f"No token for user_id={user_id!r} service={service!r}")
    return path.read_text()


def set_token(user_id: str, service: str, token_json: str) -> None:
    """Store ``token_json`` for ``user_id``/``service``."""
    safe_uid = str(user_id).strip()
    safe_svc = str(service).strip()
    user_dir = _users_dir() / safe_uid
    if safe_svc in ("gws", "google"):
        path = user_dir / "gws_token.json"
    else:
        path = user_dir / f"{safe_svc}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token_json)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def delete_token(user_id: str, service: str) -> bool:
    """Delete stored token. Returns True if something was deleted."""
    path = _token_path(user_id, service)
    if path.exists():
        path.unlink()
        return True
    return False


def has_token(user_id: str, service: str, *, session_uid: Optional[str] = None) -> bool:
    """Return True if a token file exists for ``user_id``/``service``."""
    del session_uid
    return _token_path(user_id, service).exists()


def list_services(user_id: str, *, session_uid: Optional[str] = None) -> List[str]:
    """Return service names with stored tokens for ``user_id``."""
    del session_uid
    user_dir = _users_dir() / str(user_id).strip()
    if not user_dir.exists():
        return []
    services = []
    for f in user_dir.glob("*.json"):
        name = f.stem
        if name == "gws_token":
            services.append("gws")
        elif name not in ("identity",):
            services.append(name)
    return sorted(services)


def resolve(_identity_type: str, _identity_value: str) -> Optional[str]:
    """Stub — identity resolution not supported in file backend."""
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
    """Stub — identity provisioning not supported in file backend."""
    del name, role, permissions
    raise VaultError("add_identity not supported in file-based vault backend")


def get_identity(_user_id: str, *, session_uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Stub — identity lookup not supported in file backend."""
    del session_uid
    return None
