"""Device-code OAuth for the Hermes LLM gateway.

Lets a CLI / editor-extension client (opencode plugin, etc.) obtain a
short-lived JWT scoped to the llm-gateway audience, using the SAME Google
account you already sign into admin.ahfl.in with -- no separate credential
to manage. Standard OAuth 2.0 Device Authorization Grant shape (RFC 8628),
minus a couple of optional fields we don't need for a single first-party
client.

Flow:
  1. Client:  POST /auth/device/code            -> device_code, user_code, verification_uri
  2. Human:   opens verification_uri, signs into admin.ahfl.in (existing
              Google login, unchanged), lands on /device (this module),
              approves the code shown.
  3. Client:  polls POST /auth/device/token      -> {access_token, refresh_token}
              until approved (or expired/denied).
  4. Client:  POST /auth/device/refresh          -> new access_token, re-checking
              the llm_gateway permission every time (so a revoked flag takes
              effect on next refresh, not just next full login).

The approval page (GET/POST /device) requires an existing admin-app session
(same Google login as the rest of this panel) -- see AuthMiddleware in
__init__.py. That means, for now, only identities that can already log into
admin.ahfl.in (admins, per _is_authorized in auth.py) can complete a device
approval, even though the actual llm_gateway grant check below is broader
(any vault identity with the flag explicitly set). Extending this to
non-admin employees needs its own separate, non-admin-gated login path --
deliberately NOT done here, flagged as a follow-up rather than bundled in.

State:
  - Pending device codes: in-memory only (admin-app runs a single uvicorn
    worker, no --workers flag -- see __main__.py). A restart drops any
    in-flight (not yet approved) device code; the client just retries.
  - Refresh tokens: persisted to disk (JSON, atomic write) so a normal
    admin-app restart doesn't force every already-logged-in client to
    re-authenticate. Access tokens are never persisted (stateless JWT).
"""

import json
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .jinja_env import env
from .vault_client import VaultClient

router = APIRouter()
logger = logging.getLogger("admin-app.device_auth")

JWT_SECRET = os.environ.get("LLM_GATEWAY_JWT_SECRET", "")
JWT_ISSUER = "https://admin.ahfl.in"
JWT_AUDIENCE = "llm-gateway"

DEVICE_CODE_TTL_SECONDS = 600       # 10 minutes to complete approval
DEVICE_POLL_INTERVAL_SECONDS = 5
ACCESS_TOKEN_TTL_SECONDS = 900      # 15 minutes
REFRESH_STORE_PATH = os.environ.get(
    "LLM_GATEWAY_REFRESH_STORE",
    "/opt/hermes/hermes-data/llm-gateway-refresh-tokens.json",
)

_USER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I

# device_code -> record. In-memory only, see module docstring.
_DEVICE_CODES: dict = {}
# user_code -> device_code, so the approval page (humans only see user_code)
# can find the pending record.
_USER_CODE_INDEX: dict = {}


def _gen_user_code() -> str:
    chars = [secrets.choice(_USER_CODE_ALPHABET) for _ in range(8)]
    return "".join(chars[:4]) + "-" + "".join(chars[4:])


def _prune_expired() -> None:
    now = time.time()
    dead = [dc for dc, rec in _DEVICE_CODES.items() if rec["expires_at"] < now]
    for dc in dead:
        rec = _DEVICE_CODES.pop(dc, None)
        if rec:
            _USER_CODE_INDEX.pop(rec["user_code"], None)


def _load_refresh_store() -> dict:
    try:
        return json.loads(Path(REFRESH_STORE_PATH).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _save_refresh_store(store: dict) -> None:
    path = Path(REFRESH_STORE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(store), encoding="utf-8")
    os.replace(tmp, path)


def _make_access_token(user: dict) -> str:
    from jose import jwt as jose_jwt
    now = int(time.time())
    claims = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "sub": user["email"],
        "user_id": user["user_id"],
        "name": user.get("name") or user["email"],
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL_SECONDS,
    }
    return jose_jwt.encode(claims, JWT_SECRET, algorithm="HS256")


@router.post("/auth/device/code")
async def device_code(request: Request):
    if not JWT_SECRET:
        return JSONResponse(
            {"error": "server_error", "error_description": "LLM_GATEWAY_JWT_SECRET not configured"},
            status_code=500,
        )
    _prune_expired()
    try:
        body = await request.json()
    except Exception:
        body = {}
    client_id = str((body or {}).get("client_id") or "unknown-client")

    device_code_value = secrets.token_urlsafe(32)
    user_code = _gen_user_code()
    now = time.time()
    _DEVICE_CODES[device_code_value] = {
        "user_code": user_code,
        "client_id": client_id,
        "status": "pending",
        "created_at": now,
        "expires_at": now + DEVICE_CODE_TTL_SECONDS,
        "user": None,
    }
    _USER_CODE_INDEX[user_code] = device_code_value

    return JSONResponse({
        "device_code": device_code_value,
        "user_code": user_code,
        "verification_uri": f"{JWT_ISSUER}/device",
        "verification_uri_complete": f"{JWT_ISSUER}/device?user_code={user_code}",
        "expires_in": DEVICE_CODE_TTL_SECONDS,
        "interval": DEVICE_POLL_INTERVAL_SECONDS,
    })


@router.post("/auth/device/token")
async def device_token(request: Request):
    _prune_expired()
    try:
        body = await request.json()
    except Exception:
        body = {}
    device_code_value = str((body or {}).get("device_code") or "")
    rec = _DEVICE_CODES.get(device_code_value)
    if rec is None:
        return JSONResponse({"error": "expired_token"}, status_code=400)
    if rec["status"] == "pending":
        return JSONResponse({"error": "authorization_pending"}, status_code=400)
    if rec["status"] == "denied":
        _DEVICE_CODES.pop(device_code_value, None)
        _USER_CODE_INDEX.pop(rec["user_code"], None)
        return JSONResponse({"error": "access_denied"}, status_code=400)

    user = rec["user"]
    access_token = _make_access_token(user)
    refresh_token = secrets.token_urlsafe(32)
    store = _load_refresh_store()
    store[refresh_token] = {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name") or user["email"],
        "created_at": time.time(),
    }
    _save_refresh_store(store)

    _DEVICE_CODES.pop(device_code_value, None)
    _USER_CODE_INDEX.pop(rec["user_code"], None)

    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
        "refresh_token": refresh_token,
    })


@router.post("/auth/device/refresh")
async def device_refresh(request: Request):
    if not JWT_SECRET:
        return JSONResponse({"error": "server_error"}, status_code=500)
    try:
        body = await request.json()
    except Exception:
        body = {}
    refresh_token = str((body or {}).get("refresh_token") or "")
    store = _load_refresh_store()
    rec = store.get(refresh_token)
    if not rec:
        return JSONResponse({"error": "invalid_grant"}, status_code=401)

    vault: VaultClient = request.app.state.vault
    try:
        allowed = vault.check_access("email", rec["email"], "llm_gateway")
    except Exception as e:
        logger.warning(f"refresh: vault check_access failed for {rec['email']}: {e}")
        allowed = False
    if not allowed:
        store.pop(refresh_token, None)
        _save_refresh_store(store)
        return JSONResponse(
            {"error": "access_denied", "error_description": "llm_gateway access has been revoked"},
            status_code=401,
        )

    access_token = _make_access_token(rec)
    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
    })


@router.get("/device")
async def device_approval_page(request: Request, user_code: Optional[str] = None):
    # AuthMiddleware guarantees one of these two session keys is set.
    # Either a full admin session or the lightweight device_user session
    # (any known vault identity, set by the "device:" branch in auth.py)
    # may reach this page -- the actual llm_gateway permission is still
    # checked below before anything is approved.
    user = request.session.get("device_user") or request.session.get("user")
    _prune_expired()
    return HTMLResponse(env.get_template("device.html").render(
        user=user, user_code=(user_code or "").upper(), error=None, approved=False,
    ))


@router.post("/device/approve")
async def device_approve(request: Request):
    # Either a full admin session or the lightweight device_user session
    # (any known vault identity, set by the "device:" branch in auth.py)
    # may reach this page -- the actual llm_gateway permission is still
    # checked below before anything is approved.
    user = request.session.get("device_user") or request.session.get("user")
    form = await request.form()
    submitted_code = str(form.get("user_code") or "").strip().upper()
    action = str(form.get("action") or "approve")

    _prune_expired()
    device_code_value = _USER_CODE_INDEX.get(submitted_code)
    rec = _DEVICE_CODES.get(device_code_value) if device_code_value else None
    if rec is None:
        return HTMLResponse(env.get_template("device.html").render(
            user=user, user_code=submitted_code, approved=False,
            error="That code has expired or was already used. Go back to your device and try again.",
        ))

    if action == "deny":
        rec["status"] = "denied"
        return HTMLResponse(env.get_template("device.html").render(
            user=user, user_code=submitted_code, approved=False,
            error="Request denied. You can close this window.",
        ))

    vault: VaultClient = request.app.state.vault
    email = user["email"]
    try:
        allowed = vault.check_access("email", email, "llm_gateway")
    except Exception as e:
        logger.warning(f"device approve: vault check_access failed for {email}: {e}")
        allowed = False
    if not allowed:
        return HTMLResponse(env.get_template("device.html").render(
            user=user, user_code=submitted_code, approved=False,
            error=(
                f"LLM Gateway access is not enabled for {email}. "
                "Ask an admin to enable it under Users → (you) → LLM Gateway Access."
            ),
        ))

    user_id = vault.resolve("email", email) or email
    rec["status"] = "approved"
    rec["user"] = {"email": email, "user_id": user_id, "name": user.get("name") or email}

    return HTMLResponse(env.get_template("device.html").render(
        user=user, user_code=submitted_code, approved=True, error=None,
    ))
