"""
Per-user OAuth 2.1 (PKCE, dynamic client registration) token manager for
Kelsa MCP ("Kelsa-Read", https://kelsa.io/mcp).

Mirrors tools/gws_auth.py's shape (public callback endpoint + state-encoded
identity + gws-vault storage) but adapted for Kelsa's MCP-spec-compliant
OAuth server:

  - Dynamic Client Registration (RFC 7591) at POST /oauth/register -- no
    manually-provisioned client_id/secret needed, unlike Google.
  - Public client only (``token_endpoint_auth_methods_supported: ["none"]``),
    so PKCE (S256) is REQUIRED on every authorize + token exchange -- unlike
    Google, where Hermes is a confidential client and PKCE is skipped.
  - Refresh tokens ARE supported (grant_types_supported includes
    "refresh_token").

Confirmed 2026-07-13 against
https://kelsa.io/.well-known/oauth-authorization-server (see investigation
notes in the Hermes session log for that date).

Root cause this fixes: Kelsa-Read was previously configured under
mcp_servers with ``auth: oauth``, which routes through tools/mcp_oauth.py's
*local interactive* flow (opens a browser, listens on a localhost callback
port). That flow cannot complete inside a headless Docker gateway process --
it silently fails with "non-interactive environment and no cached tokens",
the server connection raises, and zero Kelsa tools get registered. This
module instead drives the OAuth dance through Hermes' existing public HTTP
callback + Telegram-delivered link pattern (same one tools/gws_auth.py
uses for Gmail/Calendar/Drive), and stores tokens per-user in the gws-vault
daemon instead of a flat file, so multiple Hermes users can each connect
their own Kelsa account without clobbering each other.

PILOT SCOPE (Phase 1, 2026-07-13): proves the auth loop for a single user.
Token storage/refresh here IS already generically multi-user (vault is
keyed by canonical uid), but the MCP connection layer that consumes these
tokens (tools/kelsa_tool.py) opens one ephemeral connection per call rather
than a pooled persistent connection -- that generalization is Phase 2.

Usage:
    from tools.kelsa_auth import get_auth_url, exchange_and_store, has_token, get_valid_access_token
    url = get_auth_url(telegram_id)                       # send to user
    exchange_and_store(telegram_id, code, code_verifier)   # called by the /kelsa/auth/callback route
    has_token(telegram_id)                                 # bool
    token = get_valid_access_token(telegram_id)            # refreshes if needed
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
import time
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

ISSUER = "https://kelsa.io"
AUTHORIZATION_ENDPOINT = "https://kelsa.io/oauth/authorize"
TOKEN_ENDPOINT = "https://kelsa.io/oauth/token"
REGISTRATION_ENDPOINT = "https://kelsa.io/oauth/register"
MCP_URL = "https://kelsa.io/mcp"

REDIRECT_URI = "https://transcribe.ahfl.in/kelsa/auth/callback"

# "mcp:read" only -- matches the "Kelsa-Read" server name / least privilege.
# Kelsa also advertises mcp:write and mcp:design; not requested here.
SCOPE = "mcp:read"

# Vault service key. Must match ^[a-z][a-z0-9-]{0,49}$ (tools/gws_vault_client.py).
SERVICE_NAME = "mcp-kelsa-read"

# DCR client registration is an app-level credential (one Hermes-wide OAuth
# client, shared across all users -- like a Google client_id/secret pair),
# NOT a per-user secret, so it is cached on disk next to (but distinct from)
# the flat-file MCP OAuth token cache, not in the vault. Kelsa issues a
# client_id only (public client, no client_secret -- see module docstring).
_CLIENT_INFO_FILENAME = "kelsa-read-dcr-client.json"


def _client_info_path():
    from tools.mcp_oauth import _get_token_dir
    return _get_token_dir() / _CLIENT_INFO_FILENAME


def _get_or_register_client() -> str:
    """Return the cached DCR client_id, registering a new one if needed."""
    path = _client_info_path()
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            client_id = data.get("client_id")
            if client_id:
                return client_id
    except Exception:
        logger.warning(
            "Kelsa DCR client info at %s unreadable -- re-registering",
            path, exc_info=True,
        )

    resp = httpx.post(
        REGISTRATION_ENDPOINT,
        json={
            "client_name": "Hermes AI Agent",
            "redirect_uris": [REDIRECT_URI],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        },
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()
    client_id = payload.get("client_id")
    if not client_id:
        raise RuntimeError(f"Kelsa DCR response missing client_id: {payload}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        path.chmod(0o600)
    except Exception:
        pass
    logger.info("Kelsa DCR: registered new client_id=%s", client_id)
    return client_id


def _generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) per RFC 7636 (S256)."""
    verifier = (
        base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode("ascii")
    )
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    return verifier, challenge


def get_auth_url(telegram_id: str) -> str:
    """Build a Kelsa OAuth authorization URL for a user.

    The PKCE code_verifier is encoded into ``state`` as
    ``"{telegram_id}:{code_verifier}"`` because the code exchange happens in
    a *separate* request (the public /kelsa/auth/callback route, likely a
    different process/worker) with no shared memory of this call -- the
    same trick tools/gws_auth.py uses to carry the service_name through
    state, adapted here to carry the PKCE verifier instead. The verifier is
    opaque URL-safe base64 (no ':'), so splitting on the first ':' in the
    callback is safe.
    """
    client_id = _get_or_register_client()
    verifier, challenge = _generate_pkce()
    state = f"{telegram_id}:{verifier}"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def _store_token_payload(telegram_id: str, payload: dict) -> None:
    from tools import gws_vault_client as vault
    from tools.gws_auth import canonical_uid

    uid = canonical_uid(telegram_id)
    record = dict(payload)
    record["obtained_at"] = time.time()
    vault.set_token(uid, SERVICE_NAME, json.dumps(record))


def exchange_and_store(telegram_id: str, code: str, code_verifier: str) -> None:
    """Exchange an authorization code for tokens and store them in the vault."""
    client_id = _get_or_register_client()
    resp = httpx.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "code_verifier": code_verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(
            f"Kelsa token exchange failed ({resp.status_code}): {resp.text[:500]}"
        )
    payload = resp.json()
    if not payload.get("access_token"):
        raise RuntimeError(f"Kelsa token response missing access_token: {payload}")

    from tools.gws_auth import canonical_uid
    uid = canonical_uid(telegram_id)
    _store_token_payload(telegram_id, payload)
    logger.info("Kelsa token stored user_id=%s service=%s", uid, SERVICE_NAME)


def has_token(telegram_id: str) -> bool:
    from tools import gws_vault_client as vault
    from tools.gws_auth import canonical_uid

    uid = canonical_uid(telegram_id)
    return vault.has_token(uid, SERVICE_NAME, session_uid=uid)


def _refresh(telegram_id: str, refresh_token: str) -> dict:
    client_id = _get_or_register_client()
    resp = httpx.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(
            f"Kelsa token refresh failed ({resp.status_code}): {resp.text[:500]}"
        )
    payload = resp.json()
    if not payload.get("access_token"):
        raise RuntimeError(f"Kelsa refresh response missing access_token: {payload}")
    # Some OAuth servers omit refresh_token on a refresh response, meaning
    # "keep using the same one" (it wasn't rotated).
    if not payload.get("refresh_token"):
        payload["refresh_token"] = refresh_token
    _store_token_payload(telegram_id, payload)
    return payload


def get_valid_access_token(telegram_id: str) -> str:
    """Return a valid Kelsa access token for the user, refreshing if needed.

    Raises ``tools.gws_vault_client.VaultNoTokenError`` if the user has
    never authorized -- callers should catch that and direct the user to
    :func:`get_auth_url`.
    """
    from tools import gws_vault_client as vault
    from tools.gws_auth import canonical_uid

    uid = canonical_uid(telegram_id)
    raw = vault.get_token(uid, SERVICE_NAME, session_uid=uid)
    record = json.loads(raw)

    obtained_at = record.get("obtained_at", 0)
    expires_in = record.get("expires_in")
    access_token = record.get("access_token")

    is_expired = False
    if expires_in is not None:
        is_expired = (obtained_at + float(expires_in) - 60) <= time.time()  # 60s skew

    if is_expired and record.get("refresh_token"):
        record = _refresh(telegram_id, record["refresh_token"])
        access_token = record.get("access_token")

    if not access_token:
        raise RuntimeError("Kelsa token record has no access_token -- re-authorize.")
    return access_token
