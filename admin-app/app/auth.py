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
GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
JWKS_CACHE_TTL_SECONDS = 3600

# In-memory JWKS cache — module-level so it survives across requests within
# one worker process. Google rotates these keys infrequently; re-fetching on
# every login would be wasteful and adds latency to every callback.
_jwks_cache: dict = {"keys": None, "fetched_at": 0.0}


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
    access_token = tokens.get("access_token")
    if not id_token:
        return _error_page(request, "No id_token in response")

    try:
        claims = await _verify_google_id_token(id_token, access_token)
    except Exception as e:
        logger.warning(f"id_token verification failed: {e}")
        return _error_page(request, "Login verification failed — invalid or tampered token")

    email = claims.get("email", "")
    name = claims.get("name", email)
    picture = claims.get("picture", "")

    if not claims.get("email_verified", False):
        return _error_page(request, f"Access denied: {email} email is not verified by Google")

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


async def _get_google_jwks() -> dict:
    """Fetch (and cache) Google's current JWK set used to sign id_tokens."""
    now = time.time()
    if _jwks_cache["keys"] is None or (now - _jwks_cache["fetched_at"]) > JWKS_CACHE_TTL_SECONDS:
        async with httpx.AsyncClient() as client:
            resp = await client.get(GOOGLE_CERTS_URL, timeout=10)
            resp.raise_for_status()
            _jwks_cache["keys"] = resp.json()
            _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


async def _verify_google_id_token(id_token: str, access_token: Optional[str] = None) -> dict:
    """Verify a Google-issued id_token's signature, audience, and issuer.

    Raises on any failure (bad signature, expired, wrong audience/issuer,
    unknown key id). Only returns claims once cryptographic verification
    has actually passed — replaces the previous ``get_unverified_claims``
    call, which accepted any well-formed JWT regardless of who signed it.

    ``access_token`` is passed through so jose can validate the ``at_hash``
    claim Google embeds in the id_token (a hash of the access_token, proving
    both were issued in the same response). Without it, jose raises rather
    than silently skipping the check.
    """
    from jose import jwt as jose_jwt
    from jose.exceptions import JWTError

    decode_kwargs = dict(
        algorithms=["RS256"],
        audience=GOOGLE_CLIENT_ID,
        options={"verify_iss": False},  # validated manually below (jose's iss check is single-value only)
    )
    if access_token:
        decode_kwargs["access_token"] = access_token

    jwks = await _get_google_jwks()
    try:
        claims = jose_jwt.decode(id_token, jwks, **decode_kwargs)
    except JWTError:
        # Key set may have rotated since our cache was populated — retry once
        # with a forced refresh before giving up.
        _jwks_cache["keys"] = None
        jwks = await _get_google_jwks()
        claims = jose_jwt.decode(id_token, jwks, **decode_kwargs)

    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise ValueError(f"Unexpected issuer: {claims.get('iss')!r}")

    return claims


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
