"""Keep Open WebUI (chat.ahfl.in) in step with the vault's chat allowlist.

Open WebUI sits behind oauth2-proxy and trusts ``X-Forwarded-Email``, so an
account is created there on the user's first visit — but only with whatever
``ui.default_user_role`` and ``ui.default_group_id`` happen to say at that
moment, which used to mean an admin still had to approve the pending user and
hand them the Hermes model by hand.

This module removes both steps:

* ``ensure_chat_defaults`` makes Open WebUI's own defaults right — new users
  land as ``user`` (not ``pending``) and in the Hermes group, and that group
  holds a read grant on the Hermes model(s).
* ``sync_chat_users`` creates the account up front for every vault user who
  has chat access, and suspends the ones who lost it — so ticking and
  unticking "chat" in the admin panel is the only action needed, in both
  directions.

Access to the Hermes model hangs off group membership alone: per-user grants
are removed, because a grant handed out inside Open WebUI would be a second,
silent source of truth for something the vault is supposed to decide.

Everything goes through Open WebUI's admin API, authenticated with a
short-lived JWT signed with ``WEBUI_SECRET_KEY`` — the same secret Open WebUI
signs its own session tokens with — on behalf of the first admin account.  The
only thing read straight from ``webui.db`` is that admin's user id, read-only.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import threading
import time
import uuid
from typing import Any, Optional

import httpx

from .vault_client import app_allowed_users

logger = logging.getLogger("admin-app.openwebui")

OPENWEBUI_URL = os.environ.get("OPENWEBUI_URL", "http://127.0.0.1:8080").rstrip("/")
OPENWEBUI_DB = os.environ.get("OPENWEBUI_DB", "/app/backend/data/webui.db")
CHAT_GROUP_NAME = os.environ.get("OPENWEBUI_CHAT_GROUP", "Hermes Users")
CHAT_GROUP_DESCRIPTION = (
    "Chat users provisioned from the Hermes admin panel. Members get read access to the Hermes model."
)
CHAT_MODEL_IDS = [m.strip() for m in os.environ.get("OPENWEBUI_CHAT_MODELS", "hermes-agent").split(",") if m.strip()]
DEFAULT_USER_ROLE = os.environ.get("OPENWEBUI_DEFAULT_USER_ROLE", "user")
TIMEOUT = 20.0

# Required-string fields of Open WebUI's AdminConfig model: the GET can hand
# back null for these, which the POST would reject, so they are coerced.
_CONFIG_STRING_DEFAULTS = {
    "WEBUI_URL": "",
    "API_KEYS_ALLOWED_ENDPOINTS": "",
    "JWT_EXPIRES_IN": "4w",
    "DEFAULT_USER_ROLE": "pending",
    "DEFAULT_GROUP_ID": "",
    "CHANNEL_MODEL_RESPONSE_MODE": "thread",
}


class OpenWebUIError(RuntimeError):
    pass


def enabled() -> bool:
    return os.environ.get("OPENWEBUI_AUTO_PROVISION", "1").strip().lower() not in ("0", "false", "no", "off")


def _admin_user_id() -> str:
    """Open WebUI's primary admin — the identity the admin API calls run as."""
    forced = os.environ.get("OPENWEBUI_ADMIN_USER_ID", "").strip()
    if forced:
        return forced
    if not os.path.exists(OPENWEBUI_DB):
        raise OpenWebUIError(f"Open WebUI database not found at {OPENWEBUI_DB}")
    conn = sqlite3.connect(f"file:{OPENWEBUI_DB}?mode=ro", uri=True, timeout=5)
    try:
        row = conn.execute("SELECT id FROM user WHERE role = 'admin' ORDER BY created_at LIMIT 1").fetchone()
    finally:
        conn.close()
    if not row:
        raise OpenWebUIError("Open WebUI has no admin user yet")
    return row[0]


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _admin_token(ttl: int = 300) -> str:
    """Mint a short-lived HS256 session token for the primary admin."""
    secret = os.environ.get("WEBUI_SECRET_KEY", "")
    if not secret:
        raise OpenWebUIError("WEBUI_SECRET_KEY not set — cannot authenticate to Open WebUI")
    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = {"id": _admin_user_id(), "jti": str(uuid.uuid4()), "iat": now, "exp": now + ttl}
    payload = _b64(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = _b64(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


class _Api:
    """Thin authenticated wrapper around Open WebUI's REST API."""

    def __init__(self):
        self._client = httpx.Client(
            base_url=OPENWEBUI_URL,
            timeout=TIMEOUT,
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )

    def __enter__(self) -> "_Api":
        return self

    def __exit__(self, *exc_info) -> None:
        self._client.close()

    def _result(self, resp: httpx.Response) -> Any:
        if resp.status_code >= 400:
            raise OpenWebUIError(f"{resp.request.method} {resp.request.url.path} -> {resp.status_code} {resp.text[:200]}")
        return resp.json()

    def get(self, path: str, **params) -> Any:
        return self._result(self._client.get(path, params=params or None))

    def post(self, path: str, payload: Optional[dict] = None) -> Any:
        return self._result(self._client.post(path, json=payload))


def _ensure_group(api: _Api) -> dict:
    for group in api.get("/api/v1/groups/"):
        if group.get("name") == CHAT_GROUP_NAME:
            return group
    logger.info("creating Open WebUI group %r", CHAT_GROUP_NAME)
    group = api.post("/api/v1/groups/create", {"name": CHAT_GROUP_NAME, "description": CHAT_GROUP_DESCRIPTION})
    if not group:
        raise OpenWebUIError(f"could not create Open WebUI group {CHAT_GROUP_NAME!r}")
    return group


def _reconcile_model_grants(api: _Api, group_id: str) -> None:
    """Make the chat group the only thing granting the Hermes model(s).

    Direct per-user grants are dropped: model access has to follow chat access
    in the vault, so removing someone from the group must be enough to take it
    away.  Grants of other kinds are left alone, and the model's owner and
    admins keep access regardless of grants.
    """
    group_grant = {"principal_type": "group", "principal_id": group_id, "permission": "read"}
    for model_id in CHAT_MODEL_IDS:
        try:
            model = api.get("/api/v1/models/model", id=model_id)
        except OpenWebUIError as exc:
            logger.warning("Open WebUI model %r not readable (%s) — skipping grant", model_id, exc)
            continue
        current = [
            {
                "principal_type": g.get("principal_type"),
                "principal_id": g.get("principal_id"),
                "permission": g.get("permission"),
            }
            for g in (model or {}).get("access_grants") or []
        ]
        desired = [g for g in current if g["principal_type"] != "user"]
        if group_grant not in desired:
            desired.append(group_grant)
        if desired == current:
            continue
        api.post("/api/v1/models/model/access/update", {"id": model_id, "access_grants": desired})
        dropped = len(current) - len([g for g in current if g["principal_type"] != "user"])
        logger.info(
            "model %r access is now group %r only (dropped %d direct user grant(s))",
            model_id,
            CHAT_GROUP_NAME,
            dropped,
        )


def _ensure_signup_defaults(api: _Api, group_id: str) -> None:
    """Make new Open WebUI accounts active and in the chat group by default."""
    config = api.get("/api/v1/auths/admin/config")
    desired = dict(config)
    for key, fallback in _CONFIG_STRING_DEFAULTS.items():
        if desired.get(key) is None:
            desired[key] = fallback
    desired["DEFAULT_USER_ROLE"] = DEFAULT_USER_ROLE
    desired["DEFAULT_GROUP_ID"] = group_id
    if desired == config:
        return
    api.post("/api/v1/auths/admin/config", desired)
    logger.info(
        "Open WebUI signup defaults set: role=%r, group=%r (%s)",
        DEFAULT_USER_ROLE,
        CHAT_GROUP_NAME,
        group_id,
    )


def ensure_chat_defaults(api: Optional[_Api] = None) -> str:
    """Create/repair the chat group, its model grants and the signup defaults.

    Returns the group id.  Idempotent: a no-op once everything is in place.
    """
    if api is not None:
        group = _ensure_group(api)
        _reconcile_model_grants(api, group["id"])
        _ensure_signup_defaults(api, group["id"])
        return group["id"]
    with _Api() as client:
        return ensure_chat_defaults(client)


def _generate_password() -> str:
    """Unused-by-design: sign-in is via oauth2-proxy's trusted email header."""
    return f"{secrets.token_urlsafe(24)}aA1!"


def sync_chat_users() -> dict:
    """Mirror the vault's chat allowlist into Open WebUI, both ways.

    Granted chat: the account is created if missing (including for a user's
    alias addresses), activated if it was left ``pending``, and added to the
    chat group, which is what carries the Hermes model.

    Lost chat: the account is suspended — taken out of the group, so the model
    disappears from it, and set back to ``pending``.  Nothing is deleted, so
    their chats survive and re-ticking chat in the admin panel gives the same
    account its access and history back.

    Open WebUI admins are never suspended: locking the panel's own operators
    out of it on a vault hiccup would be worse than the stale access.
    """
    if not enabled():
        return {"skipped": "OPENWEBUI_AUTO_PROVISION disabled"}

    chat_users = app_allowed_users("chat")
    allowed_emails = {email for user in chat_users for email in user["emails"]}

    with _Api() as api:
        group_id = ensure_chat_defaults(api)

        existing = {u["email"].lower(): u for u in api.get("/api/v1/users/all")["users"]}
        created = []
        for user in chat_users:
            if user["email"] in existing:
                continue
            try:
                api.post(
                    "/api/v1/auths/add",
                    {
                        "name": user["name"],
                        "email": user["email"],
                        "password": _generate_password(),
                        "role": DEFAULT_USER_ROLE,
                    },
                )
                created.append(user["email"])
            except OpenWebUIError as exc:
                logger.warning("could not create Open WebUI user %s: %s", user["email"], exc)
        if created:
            logger.info("created Open WebUI users: %s", ", ".join(created))
            existing = {u["email"].lower(): u for u in api.get("/api/v1/users/all")["users"]}

        members = {u["id"] for u in api.post(f"/api/v1/groups/id/{group_id}/users")}
        activated, suspended, to_add, to_remove = [], [], [], []
        for email, user in existing.items():
            if email in allowed_emails:
                if user["role"] == "pending":
                    api.post(f"/api/v1/users/{user['id']}/update", {"role": DEFAULT_USER_ROLE})
                    activated.append(email)
                if user["id"] not in members:
                    to_add.append(user["id"])
            elif user["role"] == "admin":
                logger.info("%s is an Open WebUI admin without chat access in the vault — left as is", email)
            else:
                # Report only accounts this run actually changed, so a steady
                # state logs nothing rather than the whole revoked backlog.
                if user["role"] != "pending":
                    api.post(f"/api/v1/users/{user['id']}/update", {"role": "pending"})
                    suspended.append(email)
                if user["id"] in members:
                    to_remove.append(user["id"])
                    if email not in suspended:
                        suspended.append(email)

        if to_add:
            api.post(f"/api/v1/groups/id/{group_id}/users/add", {"user_ids": to_add})
        if to_remove:
            api.post(f"/api/v1/groups/id/{group_id}/users/remove", {"user_ids": to_remove})

    result = {
        "created": created,
        "activated": activated,
        "suspended": suspended,
        "added_to_group": len(to_add),
        "removed_from_group": len(to_remove),
        "group_id": group_id,
    }
    logger.info("Open WebUI chat sync: %s", result)
    return result


def ensure_chat_defaults_in_background(attempts: int = 6, delay: float = 10.0) -> None:
    """Apply the defaults at admin-app startup, waiting out Open WebUI's boot.

    Both processes come up together under supervisord, so the first attempts
    can legitimately fail with a connection error.
    """
    if not enabled():
        return

    def _run() -> None:
        for attempt in range(1, attempts + 1):
            try:
                ensure_chat_defaults()
                return
            except Exception as exc:  # noqa: BLE001
                logger.log(
                    logging.WARNING if attempt == attempts else logging.DEBUG,
                    "Open WebUI defaults not applied (attempt %d/%d): %s",
                    attempt,
                    attempts,
                    exc,
                )
                time.sleep(delay)

    threading.Thread(target=_run, name="openwebui-defaults", daemon=True).start()
