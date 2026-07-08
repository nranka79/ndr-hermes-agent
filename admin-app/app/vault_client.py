import json
import logging
import os
import socket
from typing import Any, Dict, List, Optional

logger = logging.getLogger("admin-app.vault")


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

    def delete_token(self, user_id: str, service: str) -> bool:
        resp = self._call({"op": "delete", "user_id": user_id, "service": service, "vault_secret": self.secret})
        return resp.get("ok", False)

    def health(self) -> dict:
        try:
            self._call({"op": "list_services", "user_id": "health-check", "session_uid": "health-check"})
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
