import json
import logging
import os
import time
from typing import Optional

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

logger = logging.getLogger("admin-app.auth")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "https://admin.ahfl.in/auth/callback")
ADMIN_EMAILS = set(e.strip() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip())

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


@router.get("/login")
async def login(request: Request):
    if not GOOGLE_CLIENT_ID:
        return _simple_login_page(request)
    auth_params = (
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
    )
    auth_url = GOOGLE_AUTH_URL + auth_params
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    if error:
        return _error_page(request, f"Google rejected login: {error}")
    if not code:
        return _error_page(request, "No authorization code received")

    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })
    if resp.status_code != 200:
        return _error_page(request, f"Token exchange failed: {resp.status_code}")

    tokens = resp.json()
    id_token = tokens.get("id_token")
    if not id_token:
        return _error_page(request, "No id_token in response")

    from jose import jwt
    try:
        claims = jwt.get_unverified_claims(id_token)
    except Exception as e:
        return _error_page(request, f"Invalid id_token: {e}")

    email = claims.get("email", "")
    name = claims.get("name", email)
    picture = claims.get("picture", "")

    if not email:
        return _error_page(request, "No email in Google profile")

    if not _is_authorized(email):
        return _error_page(request, f"Access denied: {email} is not an authorized admin")

    request.session["user"] = {
        "email": email,
        "name": name,
        "picture": picture,
        "login_at": time.time(),
    }
    return RedirectResponse(url="/")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login")


def _is_authorized(email: str) -> bool:
    if email in ADMIN_EMAILS:
        return True
    from .vault_client import VaultClient
    vault = VaultClient()
    try:
        user_id = vault.resolve("email", email)
        if user_id:
            identity = vault.get_identity(user_id)
            if identity and identity.get("permissions", {}).get("vault_admin"):
                return True
    except Exception as e:
        logger.warning(f"Vault auth check failed for {email}: {e}")
    return False


def _simple_login_page(request: Request):
    from .jinja_env import env
    template = env.get_template("login.html")
    from fastapi.responses import HTMLResponse
    return HTMLResponse(template.render(google_configured=False))


def _error_page(request: Request, message: str):
    from .jinja_env import env
    template = env.get_template("login.html")
    from fastapi.responses import HTMLResponse
    return HTMLResponse(template.render(error=message))
