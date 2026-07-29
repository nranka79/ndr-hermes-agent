import json
import logging
import os
import socket
from typing import Any, Dict, List, Optional

logger = logging.getLogger("admin-app.vault")

# App-access permission keys managed by the admin panel. Extend this list to
# add a new gated app (e.g. a future "monitor" dashboard) — the toggle UI and
# the enforcement side (gateway/identity_resolver) both key off these names.
MANAGED_APPS = ["telegram", "voice", "chat"]


class VaultError(RuntimeError):
    pass


class VaultClient:
    def __init__(self):
        self.socket_path = os.environ.get("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")
        self.secret = os.environ.get("GWS_VAULT_SECRET", "")

    def _call(self, payload: dict) -> dict:
        if not self.socket_path or not os.path.exists(self.socket_path):
            raise VaultError(f"Vault socket not found at {self.socket_path}")
        data = (json.dumps(payload) + "\n").encode("utf-8")
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(10)
        try:
            s.connect(self.socket_path)
            s.sendall(data)
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
            if not buf:
                raise VaultError("Vault closed connection without response")
            return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
        finally:
            try:
                s.close()
            except Exception:
                pass

    def resolve(self, identity_type: str, identity_value: str) -> Optional[str]:
        resp = self._call({"op": "resolve", "identity_type": identity_type, "identity_value": identity_value})
        if resp.get("ok"):
            return resp.get("user_id")
        return None

    def get_identity(self, user_id: str) -> Optional[Dict[str, Any]]:
        resp = self._call({"op": "get_identity", "user_id": user_id, "session_uid": user_id})
        if resp.get("ok"):
            return resp.get("identity")
        return None

    def add_identity(self, user_id: str, identity_type: str, identity_value: str,
                     name: Optional[str] = None, role: Optional[str] = None,
                     permissions: Optional[Dict] = None) -> Dict:
        payload = {
            "op": "add_identity",
            "user_id": user_id,
            "identity_type": identity_type,
            "identity_value": identity_value,
            "vault_secret": self.secret,
        }
        if name is not None:
            payload["name"] = name
        if role is not None:
            payload["role"] = role
        if permissions is not None:
            payload["permissions"] = permissions
        resp = self._call(payload)
        if not resp.get("ok"):
            raise VaultError(resp.get("error", "add_identity failed"))
        return resp.get("identity", {})

    def set_app_permissions(self, user_id: str, apps: Dict[str, bool]) -> Dict:
        """Merge per-app access flags into the user's permissions, preserving
        every other permission (vault_admin, manage_users, etc.).

        The vault server REPLACES the whole permissions dict on add_identity
        (verified 2026-07-10), so this MUST read-modify-write: read the current
        record, deep-merge the app toggles into permissions.apps, and re-send
        the full permissions dict against an existing alias (which updates the
        record in place — name/role are preserved when omitted).
        """
        identity = self.get_identity(user_id)
        if not identity:
            raise VaultError(f"User {user_id} not found")

        # Pick an existing alias to key the update against (must already be
        # owned by this user, else the server would create a new alias).
        aliases = identity.get("identities", {}) or {}
        anchor_type = None
        anchor_value = None
        for t in ("email", "telegram", "slug", "draas_user_id"):
            vals = aliases.get(t)
            if vals:
                anchor_type, anchor_value = t, vals[0]
                break
        if not anchor_type:
            raise VaultError(f"User {user_id} has no identity aliases to anchor the update")

        permissions = dict(identity.get("permissions", {}) or {})
        current_apps = dict(permissions.get("apps", {}) or {})
        current_apps.update(apps)
        permissions["apps"] = current_apps

        return self.add_identity(
            user_id=user_id,
            identity_type=anchor_type,
            identity_value=anchor_value,
            permissions=permissions,
        )

    def remove_identity(self, user_id: str, identity_type: str, identity_value: str) -> Optional[Dict]:
        resp = self._call({
            "op": "remove_identity",
            "user_id": user_id,
            "identity_type": identity_type,
            "identity_value": identity_value,
            "vault_secret": self.secret,
        })
        if resp.get("ok"):
            return resp.get("identity")
        if resp.get("not_found"):
            return None
        raise VaultError(resp.get("error", "remove_identity failed"))

    def list_users(self) -> List[Dict]:
        """Scan identity store for all users (admin-only, uses vault_secret)."""
        resp = self._call({
            "op": "list_identities",
            "vault_secret": self.secret,
        })
        if resp.get("ok"):
            return resp.get("identities", [])
        raise VaultError(resp.get("error", "list_identities failed"))

    def list_token_services(self, user_id: str) -> List[str]:
        resp = self._call({"op": "list_services", "user_id": user_id, "session_uid": user_id})
        if resp.get("ok"):
            return resp.get("services", [])
        return []

    def get_token(self, user_id: str, service: str) -> Optional[str]:
        resp = self._call({"op": "get", "user_id": user_id, "service": service, "session_uid": user_id})
        if resp.get("ok"):
            return resp.get("token_json")
        return None

    def set_token(self, user_id: str, service: str, token_json: str) -> None:
        """Write token_json for user_id/service. Admin op — uses vault_secret.

        Used by the vocab editor to persist a user's STT vocabulary list
        (stored as a JSON array string under service ``vocab``).
        """
        resp = self._call({
            "op": "set",
            "user_id": user_id,
            "service": service,
            "token_json": token_json,
            "vault_secret": self.secret,
        })
        if not resp.get("ok"):
            raise VaultError(resp.get("error", "set_token failed"))

    def delete_token(self, user_id: str, service: str) -> bool:
        resp = self._call({"op": "delete", "user_id": user_id, "service": service, "vault_secret": self.secret})
        return resp.get("ok", False)

    def delete_user(self, user_id: str) -> bool:
        """Delete a user's entire identity record and all tokens.

        Requires vault_secret. Returns True if the user existed.
        """
        resp = self._call({
            "op": "delete_user",
            "user_id": user_id,
            "vault_secret": self.secret,
        })
        if resp.get("ok"):
            return True
        if resp.get("not_found"):
            return False
        raise VaultError(resp.get("error", "delete_user failed"))

    def health(self) -> dict:
        try:
            self._call({"op": "list_services", "user_id": "health-check", "session_uid": "health-check"})
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
