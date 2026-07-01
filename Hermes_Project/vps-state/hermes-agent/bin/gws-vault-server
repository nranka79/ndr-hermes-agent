#!/usr/bin/env python3
"""
Token Vault Server — secure per-user, per-service OAuth token storage daemon.

Run as a dedicated OS user (gws-vault), separate from the Hermes process.
Hermes cannot directly read the token directory — it must go through this socket.

Token layout: VAULT_TOKEN_DIR/{user_id}/{service}.json
  e.g. /opt/gws-vault/tokens/7449813913/google.json   (Telegram user, numeric ID)
       /opt/gws-vault/tokens/7449813913/kelsa.json
       /opt/gws-vault/tokens/ndr/google.json            (future: alphanumeric user ID)

Identity model:
  The *user_id* field is the internal user ID from users.json — always the top-level
  key, regardless of which channel (Telegram, OpenUI, WhatsApp, …) the request came
  from. The field ``telegram_id`` is accepted as a legacy alias for ``user_id`` so
  that older Hermes deployments continue to work during the transition period.

Protocol: newline-delimited JSON over Unix domain socket.

Operations:

  get       {"op":"get","user_id":"...","service":"...","session_uid":"..."}
            → {"ok":true,"token_json":"..."}
            Authorization: session_uid MUST equal user_id (no cross-user reads).

  set       {"op":"set","user_id":"...","service":"...","token_json":"...","vault_secret":"..."}
            → {"ok":true}
            Authorization: vault_secret must match GWS_VAULT_SECRET env var.
            Called by the OAuth callback handler after exchanging a code for tokens.
            Hermes NEVER calls this — only the callback endpoint does.

  has_token {"op":"has_token","user_id":"...","service":"...","session_uid":"..."/"vault_secret":"..."}
            → {"ok":true,"has_token":true|false}
            Accepts either session_uid (owner checks own status) or vault_secret.

  delete    {"op":"delete","user_id":"...","service":"...","vault_secret":"..."}
            → {"ok":true,"deleted":true|false}
            Authorization: vault_secret required.

  list_services {"op":"list_services","user_id":"...","session_uid":"..."}
            → {"ok":true,"services":["google","kelsa",...]}
            Authorization: session_uid MUST equal user_id.

  (All operations also accept ``telegram_id`` as an alias for ``user_id``.)

Environment variables:
  GWS_VAULT_TOKEN_DIR   Directory to store tokens (default: /opt/gws-vault/tokens)
  GWS_VAULT_SOCKET      Unix socket path (default: /run/gws-vault/vault.sock)
  GWS_VAULT_SECRET      Shared secret for write operations (required)

Setup on Hetzner:
  useradd -r -s /sbin/nologin gws-vault
  mkdir -p /opt/gws-vault/tokens /run/gws-vault
  chown -R gws-vault:gws-vault /opt/gws-vault /run/gws-vault
  chmod 700 /opt/gws-vault/tokens
  # /etc/gws-vault.env (mode 600, owned gws-vault)
  # systemd service: User=gws-vault
"""

import json
import logging
import os
import pathlib
import re
import socket
import struct
import sys
import threading

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VAULT_TOKEN_DIR = os.environ.get("GWS_VAULT_TOKEN_DIR", "/opt/gws-vault/tokens")
VAULT_SOCKET_PATH = os.environ.get("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")
VAULT_SECRET = os.environ.get("GWS_VAULT_SECRET", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [token-vault] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("token-vault")

# Internal user IDs: alphanumeric, dots, hyphens, underscores, @ and +
# Covers both legacy numeric Telegram IDs (e.g. "7449813913") and future
# alphanumeric IDs (e.g. "ndr", "user.name", "alice+bot").
_UID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._@+\-]{1,63}$")
_SVC_RE = re.compile(r"^[a-z][a-z0-9-]{0,49}$")  # service names: lowercase


def _valid_uid(uid: str) -> bool:
    return bool(uid and _UID_RE.match(str(uid)))


def _valid_svc(svc: str) -> bool:
    return bool(svc and _SVC_RE.match(str(svc)))


def _extract_user_id(req: dict) -> str:
    """
    Extract the internal user ID from a request dict.

    Prefers ``user_id`` (new field). Falls back to ``telegram_id`` (legacy alias)
    so clients that haven't been updated yet continue to work.
    """
    return str(req.get("user_id") or req.get("telegram_id", "")).strip()


def _token_path(user_id: str, service: str) -> pathlib.Path:
    if not _valid_uid(user_id):
        raise ValueError(f"Invalid user_id: {user_id!r}")
    if not _valid_svc(service):
        raise ValueError(f"Invalid service name: {service!r} (use lowercase letters/digits/hyphens)")
    return pathlib.Path(VAULT_TOKEN_DIR) / str(user_id) / f"{service}.json"


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

def _check_secret(req: dict) -> bool:
    provided = req.get("vault_secret", "")
    if not VAULT_SECRET:
        logger.warning("GWS_VAULT_SECRET not set — write operations disabled")
        return False
    return bool(provided) and provided == VAULT_SECRET


def handle_request(req: dict, peer_uid: int) -> dict:
    op = req.get("op", "")
    user_id = _extract_user_id(req)
    service = str(req.get("service", "")).strip().lower()

    # All ops except list_services need service
    if op not in ("list_services",) and not _valid_svc(service):
        return {"ok": False, "error": f"Invalid or missing service name: {service!r}"}

    if op == "get":
        session_uid = str(req.get("session_uid", "")).strip()
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        # Strict: only the session user can read their own token
        if not session_uid or session_uid != user_id:
            logger.warning(
                "Denied get: session_uid=%r != user_id=%r (peer_uid=%d)",
                session_uid, user_id, peer_uid,
            )
            return {
                "ok": False,
                "error": "Unauthorized: session user does not match requested token owner",
            }
        try:
            token_json = _token_path(user_id, service).read_text(encoding="utf-8")
            logger.info(
                "Token retrieved: user=%s service=%s (peer_uid=%d)",
                user_id, service, peer_uid,
            )
            return {"ok": True, "token_json": token_json}
        except FileNotFoundError:
            return {
                "ok": False,
                "error": f"No {service} token for user {user_id}. Authorize first.",
                "needs_auth": True,
            }
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

    elif op == "set":
        if not _check_secret(req):
            logger.warning("Denied set: invalid secret (peer_uid=%d)", peer_uid)
            return {"ok": False, "error": "Unauthorized: invalid vault secret"}
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        token_json = req.get("token_json", "")
        if not token_json:
            return {"ok": False, "error": "token_json is required"}
        try:
            json.loads(token_json)  # validate JSON before storing
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": f"Invalid token_json: {exc}"}
        try:
            path = _token_path(user_id, service)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.parent.chmod(0o700)
            # Atomic write via temp file
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(token_json, encoding="utf-8")
            tmp.chmod(0o600)
            tmp.replace(path)
            logger.info(
                "Token stored: user=%s service=%s (peer_uid=%d)",
                user_id, service, peer_uid,
            )
            return {"ok": True}
        except Exception as exc:
            logger.error("Failed to store token: user=%s service=%s: %s", user_id, service, exc)
            return {"ok": False, "error": str(exc)}

    elif op == "has_token":
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        # Accept either vault_secret (admin) or session_uid matching owner
        if not _check_secret(req):
            session_uid = str(req.get("session_uid", "")).strip()
            if not session_uid or session_uid != user_id:
                return {"ok": False, "error": "Unauthorized"}
        try:
            exists = _token_path(user_id, service).exists()
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "has_token": exists}

    elif op == "delete":
        if not _check_secret(req):
            logger.warning("Denied delete: invalid secret (peer_uid=%d)", peer_uid)
            return {"ok": False, "error": "Unauthorized: invalid vault secret"}
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        try:
            path = _token_path(user_id, service)
            deleted = False
            if path.exists():
                path.unlink()
                deleted = True
            logger.info(
                "Token deleted: user=%s service=%s existed=%s (peer_uid=%d)",
                user_id, service, deleted, peer_uid,
            )
            return {"ok": True, "deleted": deleted}
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

    elif op == "list_services":
        session_uid = str(req.get("session_uid", "")).strip()
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        if not session_uid or session_uid != user_id:
            return {"ok": False, "error": "Unauthorized"}
        user_dir = pathlib.Path(VAULT_TOKEN_DIR) / user_id
        try:
            services = [p.stem for p in user_dir.glob("*.json")] if user_dir.exists() else []
        except Exception:
            services = []
        return {"ok": True, "services": sorted(services)}

    else:
        return {"ok": False, "error": f"Unknown operation: {op!r}"}


# ---------------------------------------------------------------------------
# Socket server
# ---------------------------------------------------------------------------

def _get_peer_uid(conn: socket.socket) -> int:
    """Get the UID of the connecting process via SO_PEERCRED (Linux only)."""
    try:
        cred = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        _pid, uid, _gid = struct.unpack("iII", cred)
        return uid
    except Exception:
        return -1


def _handle_connection(conn: socket.socket) -> None:
    peer_uid = _get_peer_uid(conn)
    try:
        buf = b""
        conn.settimeout(10.0)
        while b"\n" not in buf:
            chunk = conn.recv(65536)
            if not chunk:
                return
            buf += chunk
            if len(buf) > 2_000_000:
                conn.sendall(
                    (json.dumps({"ok": False, "error": "Request too large"}) + "\n").encode()
                )
                return
        line = buf.split(b"\n", 1)[0]
        req = json.loads(line.decode("utf-8"))
        resp = handle_request(req, peer_uid)
        conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
    except json.JSONDecodeError as exc:
        try:
            conn.sendall(
                (json.dumps({"ok": False, "error": f"Invalid JSON: {exc}"}) + "\n").encode()
            )
        except Exception:
            pass
    except Exception as exc:
        logger.error("Connection error (peer_uid=%d): %s", peer_uid, exc)
        try:
            conn.sendall(
                (json.dumps({"ok": False, "error": str(exc)}) + "\n").encode()
            )
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main() -> None:
    if not VAULT_SECRET:
        logger.warning(
            "GWS_VAULT_SECRET is not set — write operations (set/delete) will be disabled."
        )

    token_dir = pathlib.Path(VAULT_TOKEN_DIR)
    token_dir.mkdir(parents=True, exist_ok=True)
    token_dir.chmod(0o700)

    sock_path = pathlib.Path(VAULT_SOCKET_PATH)
    sock_path.parent.mkdir(parents=True, exist_ok=True)

    if sock_path.exists():
        sock_path.unlink()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    # 0o666: any local process can connect; security is per-operation:
    # reads enforce session_uid == user_id (SO_PEERCRED), writes enforce vault_secret.
    sock_path.chmod(0o666)
    server.listen(32)

    logger.info("Token Vault listening at %s (token_dir=%s)", sock_path, token_dir)

    try:
        while True:
            try:
                conn, _ = server.accept()
                t = threading.Thread(target=_handle_connection, args=(conn,), daemon=True)
                t.start()
            except KeyboardInterrupt:
                break
            except Exception as exc:
                logger.error("Accept error: %s", exc)
    finally:
        server.close()
        try:
            sock_path.unlink()
        except Exception:
            pass
        logger.info("Token Vault stopped")


if __name__ == "__main__":
    main()
