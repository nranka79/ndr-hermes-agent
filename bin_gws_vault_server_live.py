#!/usr/bin/env python3
"""
Token Vault Server — secure per-user, per-service OAuth token storage + identity daemon.

Run as a dedicated OS user (gws-vault), separate from the Hermes process.
Hermes cannot directly read the token/identity directory — it must go through this socket.

Token layout: VAULT_TOKEN_DIR/{user_id}/{service}.json
  e.g. /opt/gws-vault/tokens/7449813913/google.json   (Telegram user, numeric ID)
       /opt/gws-vault/tokens/7449813913/kelsa.json
       /opt/gws-vault/tokens/ndr/google.json            (future: alphanumeric user ID)

  Each token also has a sidecar metadata file
  VAULT_TOKEN_DIR/{user_id}/{service}.json.meta
  containing {"created_at": <ISO-UTC>, "updated_at": <ISO-UTC>} so the
  admin panel can show when a token was first generated. The token
  payload itself is never mutated (the .meta file does not match the
  *.json glob, so it is invisible to service listing). For legacy tokens
  written before the sidecar existed, created_at is seeded from the
  token file's mtime on the next set/refresh (best-known approximation,
  surfaced to clients via the "approx" flag).

Identity layout: IDENTITY_DIR/{user_id}.json
  e.g. /opt/gws-vault/identities/ndr@draas.com.json
  The canonical user_id is the primary email. All raw channel identifiers
  (Telegram IDs, secondary emails, draas_user_id slugs) resolve to this.

Identity model:
  The canonical *user_id* is the primary email (e.g. ``ndr@draas.com``).
  A person may have many raw identifiers (Telegram numeric IDs, emails,
  draas_user_id slugs) — the vault maps them all to one canonical user_id
  via the ``identities`` dict in the identity record.

Protocol: newline-delimited JSON over Unix domain socket.

Token operations:

  get       {"op":"get","user_id":"...","service":"...","session_uid":"..."|"vault_secret":"..."}
            → {"ok":true,"token_json":"..."}
            Authorization: session_uid must match user_id (self-read) OR vault_secret
            (admin read, e.g. for app-level credentials stored under a system user).

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
            → {"ok":true,"services":["google","kelsa",...],
               "token_meta":[{"service":"google","created_at":"...","updated_at":"...","approx":false},...]}
            Authorization: session_uid MUST equal user_id.
            token_meta carries per-service generation timestamps (ISO-8601
            UTC). "approx":true means created_at was seeded from the token
            file's mtime for a pre-sidecar legacy token.

  (All token operations also accept ``telegram_id`` as an alias for ``user_id``.)

Identity operations:

  resolve   {"op":"resolve","identity_type":"...","identity_value":"..."}
            → {"ok":true,"user_id":"..."} or {"ok":false,"error":"..."}
            No authorization required (only returns canonical user_id, never secrets).

  add_identity {"op":"add_identity","user_id":"...","identity_type":"...",
                "identity_value":"...","vault_secret":"...",
                "name":"...","role":"...","permissions":{...}}
            → {"ok":true,"identity":{...}}
            Authorization: vault_secret required (admin-only write).
            Creates or updates identity record. Rejects if identity_value
            already belongs to a different user_id.

  remove_identity {"op":"remove_identity","user_id":"...","identity_type":"...",
                   "identity_value":"...","vault_secret":"..."}
            → {"ok":true,"identity":{...}}
            Authorization: vault_secret required (admin-only write).
            Removes one (identity_type, identity_value) pair from the
            user's identity record. Deletes the identity_type key if the
            list becomes empty.

  get_identity {"op":"get_identity","user_id":"...","session_uid":"..."}
            → {"ok":true,"identity":{...}} or {"ok":false,"error":"..."}
            Authorization: session_uid MUST equal user_id (self-read only).

Environment variables:
  GWS_VAULT_TOKEN_DIR    Directory to store tokens (default: /opt/gws-vault/tokens)
  GWS_VAULT_IDENTITY_DIR Directory to store identity records (default: /opt/gws-vault/identities)
  GWS_VAULT_SOCKET       Unix socket path (default: /run/gws-vault/vault.sock)
  GWS_VAULT_SECRET       Shared secret for write operations (required)

Setup on Hetzner:
  useradd -r -s /sbin/nologin gws-vault
  mkdir -p /opt/gws-vault/tokens /opt/gws-vault/identities /run/gws-vault
  chown -R gws-vault:gws-vault /opt/gws-vault /run/gws-vault
  chmod 700 /opt/gws-vault/tokens /opt/gws-vault/identities
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
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VAULT_TOKEN_DIR = os.environ.get("GWS_VAULT_TOKEN_DIR", "/opt/gws-vault/tokens")
VAULT_IDENTITY_DIR = os.environ.get("GWS_VAULT_IDENTITY_DIR", "/opt/gws-vault/identities")
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


def _token_meta_path(user_id: str, service: str) -> pathlib.Path:
    """Sidecar metadata file next to a token: {service}.json.meta.

    Stores {"created_at": ..., "updated_at": ...} so the admin panel can
    show when a token was first generated. Deliberately a *separate* file
    rather than fields injected into the token payload -- token JSON is
    written/read verbatim by clients (google creds, vocab arrays, raw
    Kelsa payloads) and must not be mutated by the vault. The .meta suffix
    does not match the *.json glob, so service listing ignores it.
    """
    return pathlib.Path(str(_token_path(user_id, service)) + ".meta")


def _load_token_meta(user_id: str, service: str) -> dict:
    try:
        return json.loads(_token_meta_path(user_id, service).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_token_meta(user_id: str, service: str, meta: dict) -> None:
    path = _token_meta_path(user_id, service)
    tmp = path.with_suffix(".meta.tmp")
    tmp.write_text(json.dumps(meta), encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _identity_path(user_id: str) -> pathlib.Path:
    if not _valid_uid(user_id):
        raise ValueError(f"Invalid user_id: {user_id!r}")
    return pathlib.Path(VAULT_IDENTITY_DIR) / f"{user_id}.json"


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _load_identity(user_id: str) -> dict:
    """Load identity record for *user_id*, or return empty dict."""
    try:
        return json.loads(_identity_path(user_id).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _scan_identities() -> list[dict]:
    """Return all identity records from the identity store.

    Scans ``IDENTITY_DIR/*.json``.  Returns an empty list if the directory
    doesn't exist or is empty.
    """
    d = pathlib.Path(VAULT_IDENTITY_DIR)
    if not d.exists():
        return []
    results: list[dict] = []
    for p in d.glob("*.json"):
        try:
            results.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return results


def _normalize_phone(raw: str) -> str:
    """Normalize a phone number to a digits-only key for UNIQUENESS
    COMPARISON only -- the value as typed by the admin is still what gets
    stored/displayed verbatim; this is never written back.

    2026-07-30 product decision: phone numbers must be globally unique
    across every user's profile ``phone`` field AND every user's
    ``identities.phone`` list (see ``add_identity``'s phone-conflict check
    below). Since the same real-world number can be entered with or
    without the ISD/country code (e.g. "9876543210" vs "+919876543210" vs
    "919876543210"), compare a normalized form instead of the raw string:
    strip everything but digits, and if what's left is a bare 10-digit
    number (no country code), assume India and prepend "91". Anything
    else (already has a country code, or an unexpected length) is left
    as-is -- this is a deliberately simple heuristic, not full E.164
    validation for every country.
    """
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10:
        digits = "91" + digits
    return digits


def _phone_conflict_owner(user_id: str, phone_value: str) -> str | None:
    """Return the OTHER user_id that already owns *phone_value* (as their
    profile ``phone`` field or an entry in their ``identities.phone``
    list), comparing normalized numbers per ``_normalize_phone``.

    Returns None if the number is unclaimed, or if it's only claimed by
    *user_id* itself (a user may legitimately have the same number in both
    their profile phone and their identities.phone list).
    """
    target = _normalize_phone(phone_value)
    if not target:
        return None
    for rec in _scan_identities():
        other_uid = rec.get("user_id")
        if other_uid == user_id:
            continue
        if _normalize_phone(rec.get("phone") or "") == target:
            return other_uid
        for p in (rec.get("identities", {}).get("phone") or []):
            if _normalize_phone(p) == target:
                return other_uid
    return None


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

    # Ops that don't need a service name
    # 2026-07-30: delete_user and search_identities were missing here --
    # neither op uses/needs a `service` param, but the guard below was
    # rejecting both with "Invalid or missing service name: ''" before
    # they ever reached their own handlers. Found while cleaning up test
    # data from the phone-uniqueness fix's live smoke test.
    _NO_SVC_OPS = frozenset((
        "list_services", "resolve", "add_identity", "get_identity",
        "remove_identity", "list_identities", "delete_user", "search_identities",
    ))
    if op not in _NO_SVC_OPS and not _valid_svc(service):
        return {"ok": False, "error": f"Invalid or missing service name: {service!r}"}

    if op == "get":
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        # Allow either matching session_uid (self-read) or vault_secret (admin read)
        if not _check_secret(req):
            session_uid = str(req.get("session_uid", "")).strip()
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
            # Timestamp bookkeeping -- read any legacy mtime BEFORE the
            # file is overwritten below (replace() bumps mtime to "now").
            now = _utc_now_iso()
            meta = _load_token_meta(user_id, service)
            created = meta.get("created_at")
            if created is None:
                # Legacy token (no sidecar yet): the file's mtime is the
                # best-known approximation of when it was generated.
                try:
                    created = datetime.fromtimestamp(
                        path.stat().st_mtime, timezone.utc
                    ).isoformat(timespec="seconds")
                except OSError:
                    created = now
            path.parent.mkdir(parents=True, exist_ok=True)
            path.parent.chmod(0o700)
            # Atomic write via temp file
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(token_json, encoding="utf-8")
            tmp.chmod(0o600)
            tmp.replace(path)
            _write_token_meta(user_id, service, {"created_at": created, "updated_at": now})
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
            _token_meta_path(user_id, service).unlink(missing_ok=True)
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
            entries = [p for p in user_dir.glob("*.json")] if user_dir.exists() else []
        except Exception:
            entries = []
        services = []
        token_meta = []
        for p in entries:
            svc = p.stem
            services.append(svc)
            meta = _load_token_meta(user_id, svc)
            created = meta.get("created_at")
            updated = meta.get("updated_at")
            approx = False
            if created is None or updated is None:
                try:
                    mtime = datetime.fromtimestamp(
                        p.stat().st_mtime, timezone.utc
                    ).isoformat(timespec="seconds")
                except OSError:
                    mtime = None
                if created is None:
                    created = mtime
                    approx = True
                if updated is None:
                    updated = mtime
            token_meta.append({
                "service": svc,
                "created_at": created,
                "updated_at": updated,
                "approx": approx,
            })
        token_meta.sort(key=lambda m: m["service"])
        return {"ok": True, "services": sorted(services), "token_meta": token_meta}

    # ── Identity operations ──────────────────────────────────────────────────

    elif op == "resolve":
        identity_type = str(req.get("identity_type", "")).strip().lower()
        identity_value = str(req.get("identity_value", "")).strip()
        if not identity_type or not identity_value:
            return {"ok": False, "error": "identity_type and identity_value are required"}
        for rec in _scan_identities():
            ids = rec.get("identities", {})
            values = ids.get(identity_type)
            if isinstance(values, list) and identity_value in values:
                return {"ok": True, "user_id": rec.get("user_id", "")}
        logger.info(
            "Resolve miss: type=%s value=%s (peer_uid=%d)",
            identity_type, identity_value, peer_uid,
        )
        return {"ok": False, "error": f"Identity not found: {identity_type}={identity_value}", "not_found": True}

    elif op == "add_identity":
        if not _check_secret(req):
            logger.warning("Denied add_identity: invalid secret (peer_uid=%d)", peer_uid)
            return {"ok": False, "error": "Unauthorized: invalid vault secret"}
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        identity_type = str(req.get("identity_type", "")).strip().lower()
        identity_value = str(req.get("identity_value", "")).strip()
        if not identity_type or not identity_value:
            return {"ok": False, "error": "identity_type and identity_value are required"}
        name = req.get("name")
        role = req.get("role")
        permissions = req.get("permissions")
        # App-specific fields (2026-07-18 users.json consolidation).
        # Not identity/auth data -- gbrain_home/phone/contacts_sheet_id
        # are per-user application metadata that used to live only in
        # the file registry (tools/_user_registry.py). Migrating them
        # here lets that data get the same admin-secret-gated write
        # protection as everything else in the identity record, instead
        # of sitting in a file the hermes OS user can write directly.
        gbrain_home = req.get("gbrain_home")
        phone = req.get("phone")
        contacts_sheet_id = req.get("contacts_sheet_id")

        # Phone numbers must be globally unique across the entire system --
        # both as a user's profile `phone` field AND as an identities.phone
        # entry -- for any user OTHER than this one. Same user may have the
        # same number in both slots. Checked here (ahead of the generic
        # identity_type/identity_value loop below) so it covers BOTH ways a
        # phone number can be submitted: identity_type=="phone" (the
        # generic "add identity" form) and the special `phone` app-metadata
        # field (create/edit user forms) -- the generic loop below only
        # covers the former and only against other users' identities.phone
        # lists, not their profile phone field.
        if identity_type == "phone":
            owner = _phone_conflict_owner(user_id, identity_value)
            if owner:
                return {
                    "ok": False,
                    "error": f"Conflict: phone={identity_value} already belongs to user {owner}",
                }
        if phone is not None:
            owner = _phone_conflict_owner(user_id, phone)
            if owner:
                return {
                    "ok": False,
                    "error": f"Conflict: phone={phone} already belongs to user {owner}",
                }

        # Check that identity_value doesn't already belong to another user
        for rec in _scan_identities():
            if rec.get("user_id") == user_id:
                continue  # same user — skip conflict check
            ids = rec.get("identities", {})
            values = ids.get(identity_type)
            if isinstance(values, list) and identity_value in values:
                return {
                    "ok": False,
                    "error": (
                        f"Conflict: {identity_type}={identity_value} already "
                        f"belongs to user {rec['user_id']}"
                    ),
                }

        # Load existing identity record or create a new one
        existing = _load_identity(user_id)
        existing.setdefault("identities", {})
        existing.setdefault("user_id", user_id)
        if name is not None:
            existing["name"] = name
        if role is not None:
            existing["role"] = role
        if permissions is not None:
            existing["permissions"] = permissions
        if gbrain_home is not None:
            existing["gbrain_home"] = gbrain_home
        if phone is not None:
            existing["phone"] = phone
            # Also add phone as a searchable identity type for resolve("phone", ...).
            existing.setdefault("identities", {}).setdefault("phone", [])
            if phone not in existing["identities"]["phone"]:
                existing["identities"]["phone"].append(phone)
        if contacts_sheet_id is not None:
            existing["contacts_sheet_id"] = contacts_sheet_id

        existing.setdefault("identities", {}).setdefault(identity_type, [])
        if identity_value not in existing["identities"][identity_type]:
            existing["identities"][identity_type].append(identity_value)

        # Write atomically
        try:
            path = _identity_path(user_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.parent.chmod(0o700)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(existing, indent=2), encoding="utf-8")
            tmp.chmod(0o600)
            tmp.replace(path)
            logger.info(
                "Identity stored: user=%s type=%s value=%s (peer_uid=%d)",
                user_id, identity_type, identity_value, peer_uid,
            )
            return {"ok": True, "identity": existing}
        except Exception as exc:
            logger.error("Failed to store identity: user=%s: %s", user_id, exc)
            return {"ok": False, "error": str(exc)}

    elif op == "get_identity":
        session_uid = str(req.get("session_uid", "")).strip()
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        if not session_uid or session_uid != user_id:
            logger.warning(
                "Denied get_identity: session_uid=%r != user_id=%r (peer_uid=%d)",
                session_uid, user_id, peer_uid,
            )
            return {"ok": False, "error": "Unauthorized: session user does not match requested identity"}
        identity = _load_identity(user_id)
        if not identity:
            return {"ok": False, "error": f"No identity record for user {user_id}", "not_found": True}
        return {"ok": True, "identity": identity}

    elif op == "remove_identity":
        if not _check_secret(req):
            logger.warning("Denied remove_identity: invalid secret (peer_uid=%d)", peer_uid)
            return {"ok": False, "error": "Unauthorized: invalid vault secret"}
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}
        identity_type = str(req.get("identity_type", "")).strip().lower()
        identity_value = str(req.get("identity_value", "")).strip()
        if not identity_type or not identity_value:
            return {"ok": False, "error": "identity_type and identity_value are required"}
        identity = _load_identity(user_id)
        if not identity:
            return {"ok": False, "error": f"No identity record for user {user_id}", "not_found": True}
        ids = identity.get("identities", {})
        values = ids.get(identity_type)
        if not isinstance(values, list) or identity_value not in values:
            return {"ok": False, "error": f"{identity_type}={identity_value} not found for user {user_id}", "not_found": True}
        values.remove(identity_value)
        if not values:
            ids.pop(identity_type, None)
        # Write atomically
        try:
            path = _identity_path(user_id)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(identity, indent=2), encoding="utf-8")
            tmp.chmod(0o600)
            tmp.replace(path)
            logger.info(
                "Identity updated: user=%s removed %s=%s (peer_uid=%d)",
                user_id, identity_type, identity_value, peer_uid,
            )
            return {"ok": True, "identity": identity}
        except Exception as exc:
            logger.error("Failed to update identity: user=%s: %s", user_id, exc)
            return {"ok": False, "error": str(exc)}



    elif op == "delete_user":
        if not _check_secret(req):
            logger.warning("Denied delete_user: invalid secret (peer_uid=%d)", peer_uid)
            return {"ok": False, "error": "Unauthorized: invalid vault secret"}
        if not _valid_uid(user_id):
            return {"ok": False, "error": "Invalid or missing user_id"}

        identity = _load_identity(user_id)
        if not identity:
            return {"ok": False, "error": f"No identity record for user {user_id}", "not_found": True}

        # Remove identity file
        _identity_path(user_id).unlink(missing_ok=True)

        # Remove all token files for this user
        user_token_dir = pathlib.Path(VAULT_TOKEN_DIR) / user_id
        if user_token_dir.exists():
            import shutil
            shutil.rmtree(user_token_dir)

        logger.info(
            "User deleted: user=%s (peer_uid=%d)",
            user_id, peer_uid,
        )
        return {"ok": True, "deleted": True}

    elif op == "list_identities":
        if not _check_secret(req):
            logger.warning("Denied list_identities: invalid secret (peer_uid=%d)", peer_uid)
            return {"ok": False, "error": "Unauthorized: invalid vault secret"}
        try:
            identities = _scan_identities()
            summary = []
            for rec in identities:
                ids = rec.get("identities", {})
                emails = ids.get("email", [])
                telegrams = ids.get("telegram", [])
                slugs = ids.get("slug", [])
                summary.append({
                    "user_id": rec.get("user_id", ""),
                    "name": rec.get("name", ""),
                    "email": emails[0] if emails else "",
                    "telegram": telegrams[0] if telegrams else "",
                    "slug": slugs[0] if slugs else "",
                    "role": rec.get("role", "employee"),
                    "permissions": rec.get("permissions", {}),
                })
            logger.info("list_identities: returned %d records (peer_uid=%d)", len(summary), peer_uid)
            return {"ok": True, "identities": summary}
        except Exception as exc:
            logger.error("list_identities failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    elif op == "search_identities":
        query = str(req.get("query", "")).strip().lower()
        if not query:
            return {"ok": False, "error": "query is required"}
        identity_type = str(req.get("identity_type", "")).strip().lower() or None
        try:
            identities = _scan_identities()
            results = []
            for rec in identities:
                name_raw = rec.get("name", "") or ""
                phones_raw = rec.get("identities", {}).get("phone", [])
                user_id = rec.get("user_id", "")
                ql = query.lower()
                # Match by name (partial, case-insensitive)
                if (not identity_type or identity_type == "name") and ql in name_raw.lower():
                    ids = rec.get("identities", {})
                    results.append({
                        "user_id": user_id,
                        "name": name_raw,
                        "phone": rec.get("phone", ""),
                        "telegram_ids": ids.get("telegram", []),
                        "emails": ids.get("email", []),
                        "matched_field": "name",
                    })
                    continue
                # Match by phone
                if (not identity_type or identity_type == "phone"):
                    clean_query = re.sub(r"\D", "", query)
                    for p in phones_raw:
                        if clean_query and clean_query == re.sub(r"\D", "", p):
                            ids = rec.get("identities", {})
                            results.append({
                                "user_id": user_id,
                                "name": name_raw,
                                "phone": rec.get("phone", ""),
                                "telegram_ids": ids.get("telegram", []),
                                "emails": ids.get("email", []),
                                "matched_field": "phone",
                            })
                            break
            logger.info(
                "search_identities: query=%r returned %d matches (peer_uid=%d)",
                query, len(results), peer_uid,
            )
            return {"ok": True, "results": results}
        except Exception as exc:
            logger.error("search_identities failed: %s", exc)
            return {"ok": False, "error": str(exc)}

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

    identity_dir = pathlib.Path(VAULT_IDENTITY_DIR)
    identity_dir.mkdir(parents=True, exist_ok=True)
    identity_dir.chmod(0o700)

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
