"""Domain-wide-delegation (DWD) admin page.

Manages the vault's ``google-dwd`` service-account key (stored under the
GWS_VAULT_SYSTEM_ADMIN identity) and lets an admin verify the delegation
end-to-end with the "Test as user" box.

Security model:
  - The whole admin-app is already SSO-gated (AuthMiddleware), and every
    logged-in user is a vault admin (role==admin or vault_admin) — see
    auth.py._is_authorized. This page adds no extra auth beyond that; the
    vault's own ``get_gws_credentials`` op independently enforces the
    admin-only rule (fail-closed), so the test box cannot be used even if a
    future route forgets its checks.
  - The SA key is NEVER surfaced here: the status card only reads the
    ``.meta`` sidecar (exists + created_at) via list_services; the test box
    reports mode / resolved email but drops token_json before rendering.
  - Upload validates that the payload parses and carries
    client_email / private_key / client_id, then stores it via the vault
    ``set`` op (vault_secret-gated) — the raw key travels in the POST body
    from the admin's browser to the vault and is never logged.
"""

import json
import logging
import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from .jinja_env import env
from .vault_client import VaultClient, VaultError

router = APIRouter()
logger = logging.getLogger("admin-app.dwd")

SYSTEM_ADMIN = os.environ.get("GWS_VAULT_SYSTEM_ADMIN", "ndr@nishantranka.com")
DWD_SERVICE = "google-dwd"

REQUIRED_SA_FIELDS = ("client_email", "private_key", "client_id")


def _dwd_status(vault: VaultClient) -> dict:
    """Token existence + generation timestamps from the .meta sidecar only.

    Never reads the key payload into this process.
    """
    info = {}
    try:
        for m in vault.list_token_metadata(SYSTEM_ADMIN):
            if m.get("service") == DWD_SERVICE:
                info = m
                break
    except Exception as exc:  # noqa: BLE001
        logger.warning("dwd status read failed: %s", exc)
    return {
        "exists": bool(info),
        "created_at": info.get("created_at"),
        "updated_at": info.get("updated_at"),
        "approx": bool(info.get("approx")),
    }


def _render(request: Request, *, status: dict = None,
            message: str = None, error: str = None,
            test_target: str = "", test_result: dict = None) -> HTMLResponse:
    return HTMLResponse(env.get_template("dwd.html").render(
        user=request.session.get("user"),
        system_admin=SYSTEM_ADMIN,
        status=status or _dwd_status(request.app.state.vault),
        message=message, error=error,
        test_target=test_target, test_result=test_result,
    ))


@router.get("/vault/dwd")
async def dwd_page(request: Request):
    return _render(request)


@router.post("/vault/dwd/upload")
async def dwd_upload(request: Request, token_json: str = Form(...)):
    vault: VaultClient = request.app.state.vault
    token_json = token_json.strip()
    try:
        parsed = json.loads(token_json)
    except json.JSONDecodeError as exc:
        return _render(request, error=f"Invalid JSON: {exc}")
    if not isinstance(parsed, dict):
        return _render(request, error="Service-account key must be a JSON object")
    for field in REQUIRED_SA_FIELDS:
        if not str(parsed.get(field) or "").strip():
            return _render(request, error=f"Missing required field: {field}")
    try:
        vault.set_token(SYSTEM_ADMIN, DWD_SERVICE, json.dumps(parsed))
    except VaultError as exc:
        logger.error("dwd upload failed: %s", exc)
        return _render(request, error=str(exc))
    logger.info("dwd upload: stored google-dwd key for %s (admin=%s)", SYSTEM_ADMIN,
                request.session.get("user", {}).get("email", ""))
    return _render(request, message="DWD service-account key stored in the vault.")


@router.post("/vault/dwd/delete")
async def dwd_delete(request: Request):
    vault: VaultClient = request.app.state.vault
    try:
        deleted = vault.delete_token(SYSTEM_ADMIN, DWD_SERVICE)
    except VaultError as exc:
        logger.error("dwd delete failed: %s", exc)
        return _render(request, error=str(exc))
    if not deleted:
        return _render(request, error="Delete failed — check that GWS_VAULT_SECRET is set in the admin app.")
    logger.info("dwd delete: removed google-dwd key for %s (admin=%s)", SYSTEM_ADMIN,
                request.session.get("user", {}).get("email", ""))
    return _render(request, message="DWD service-account key deleted.")


@router.post("/vault/dwd/test")
async def dwd_test(request: Request, target: str = Form(...)):
    """Resolve a person and report how the vault would credential them.

    Reports mode (user vs dwd) and the resolved email only — token_json is
    deliberately dropped before rendering so the SA key can never reach the
    browser.
    """
    vault: VaultClient = request.app.state.vault
    session_uid = request.session.get("user", {}).get("email", "")
    target = target.strip()
    error = None
    result = None
    try:
        resp = vault.get_gws_credentials(session_uid=session_uid, target=target)
        result = {
            "mode": resp.get("mode"),
            "user_id": resp.get("user_id"),
            "email": resp.get("email"),
            "needs_auth": bool(resp.get("needs_auth")),
        }
        logger.info("dwd test: target=%r mode=%s email=%s (admin=%s)",
                    target, result["mode"], result["email"], session_uid)
    except VaultError as exc:
        error = str(exc)
    return _render(request, error=error, test_target=target, test_result=result)