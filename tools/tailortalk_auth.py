"""
Per-user OAuth 2.1 (PKCE, dynamic client registration) token manager for
the TailorTalk MCP server (https://api.tailortalk.ai/mcp).

This is the TailorTalk twin of tools/kelsa_auth.py and follows it line for
line wherever the two servers behave the same: identity comes from the
session context only, tokens live in the gws-vault keyed by canonical uid,
the DCR client registration is an app-level credential stored under the
synthetic ``hermes-system`` vault user, the PKCE verifier rides in ``state``
so the HTTPS callback (gateway/platforms/api_server.py,
``_handle_tailortalk_auth_callback``) can finish the exchange in a different
process, and every entry point is guarded against being driven from
execute_code / a shelled-out script instead of the ``tailortalk_login`` tool.

What TailorTalk's OAuth server advertises (probed 2026-10-07):

  - ``GET /.well-known/oauth-protected-resource/mcp`` ->
    ``resource = https://api.tailortalk.ai/mcp``,
    ``authorization_servers = ["https://api.tailortalk.ai/"]``,
    ``scopes_supported = []`` (no scope list is published).
  - ``GET /.well-known/oauth-authorization-server`` ->
    authorize ``/authorize``, token ``/token``, DCR ``/register``,
    revoke ``/revoke``, ``code_challenge_methods_supported = ["S256"]``,
    ``grant_types_supported = ["authorization_code", "refresh_token"]``,
    ``token_endpoint_auth_methods_supported = ["client_secret_post",
    "client_secret_basic"]``.
  - ``POST /register`` with ``token_endpoint_auth_method: "none"`` is
    ACCEPTED and echoes it back with ``application_type: "native"`` and a
    server-assigned ``scope: "mcp"`` -- so, like Kelsa, Hermes registers as
    a public PKCE client. Because the AS metadata lists only secret-based
    methods, the token calls below also send ``client_secret`` whenever the
    DCR response included one, and ``TAILORTALK_TOKEN_AUTH_METHOD`` can be
    flipped to ``client_secret_post`` (forces a re-registration) if the
    public-client exchange is ever rejected.
  - ``GET /authorize`` with the full PKCE + ``resource`` parameter set
    302s to ``https://dashboard.tailortalk.ai/connect?request=...`` (the
    consent page), i.e. a public HTTPS redirect_uri is accepted.

Usage (identity always from the session, never a parameter):
    from tools.tailortalk_auth import get_auth_url, exchange_and_store, has_token, get_valid_access_token
    url = get_auth_url()                 # only callable from tools.tailortalk_tool
    exchange_and_store(code, verifier)   # called by the HTTPS callback handler
    has_token()                          # bool
    token = get_valid_access_token()     # refreshes if needed
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import sys
import time
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

ISSUER = "https://api.tailortalk.ai"
AUTHORIZATION_ENDPOINT = "https://api.tailortalk.ai/authorize"
TOKEN_ENDPOINT = "https://api.tailortalk.ai/token"
REGISTRATION_ENDPOINT = "https://api.tailortalk.ai/register"
MCP_URL = "https://api.tailortalk.ai/mcp"

# Public HTTPS callback, proxied by nginx (transcribe.ahfl.in) to the hermes
# api_server on :8642 -- same arrangement as /kelsa/auth/callback.
# TAILORTALK_REDIRECT_URI overrides it (e.g. for a staging host).
REDIRECT_URI = os.environ.get(
    "TAILORTALK_REDIRECT_URI",
    "https://transcribe.ahfl.in/tailortalk/auth/callback",
)

# TailorTalk publishes no scopes_supported list; "mcp" is the scope its DCR
# endpoint assigns to every registered client, so that is what we ask for.
SCOPE = os.environ.get("TAILORTALK_SCOPE", "mcp")

# How Hermes authenticates to the token endpoint. "none" = public PKCE
# client (accepted by TailorTalk's DCR, mirrors Kelsa). Changing this forces
# a fresh DCR registration (see _get_or_register_client).
TOKEN_AUTH_METHOD = os.environ.get("TAILORTALK_TOKEN_AUTH_METHOD", "none")

# Vault service key. Must match ^[a-z][a-z0-9-]{0,49}$ (tools/gws_vault_client.py).
SERVICE_NAME = "mcp-tailortalk"

# App-level DCR registration, one per Hermes deployment, shared by every
# process that has vault access (the gateway that generates the auth URL and
# the api_server callback that exchanges the code MUST use the same client).
DCR_SERVICE_NAME = "tailortalk-dcr"
_DCR_USER_ID = "hermes-system"

# Auth-URL idempotency cache: user id -> (generated_at, url). Repeated
# tailortalk_login calls inside the cooldown return the same URL (same PKCE
# verifier) instead of spamming the user with buttons.
_auth_url_cache: dict[str, tuple[float, str]] = {}
_AUTH_URL_COOLDOWN_SECONDS = 300

# user id -> {"platform": str, "chat_id": str}; set by tailortalk_login,
# read by the callback handler so the success notice goes back to the
# channel the user started from.
_notify_context: dict[str, dict[str, str]] = {}


# ---------------------------------------------------------------------------
# Small indirections (also what the unit tests monkeypatch)
# ---------------------------------------------------------------------------

def _vault():
    from tools import gws_vault_client as vault
    return vault


def _canonical_uid(channel_id: str) -> str:
    from tools.gws_auth import canonical_uid
    return canonical_uid(channel_id)


def _session_user_id() -> str:
    """Raw channel id of the active session user -- session context ONLY."""
    try:
        from gateway.session_context import get_gws_identity_env
        tid = get_gws_identity_env().strip()
    except Exception:
        tid = os.environ.get("HERMES_SESSION_USER_ID", "").strip()
    if not tid:
        raise ValueError(
            "No session user context (HERMES_SESSION_USER_ID not set). "
            "Cannot determine which user's TailorTalk token to load."
        )
    return tid


# ---------------------------------------------------------------------------
# Guards (same incidents as Kelsa, same answer)
# ---------------------------------------------------------------------------

def _reject_if_not_called_from_tailortalk_tool(op_name: str) -> None:
    """Refuse unless the immediate caller is tools.tailortalk_tool.

    Blocks the "shell out and build the auth URL yourself" anti-pattern that
    bit Kelsa on 2026-07-20: a hand-rolled call bypasses safe delivery, the
    already-authorized short-circuit and the idempotency cache.
    """
    caller_module = sys._getframe(2).f_globals.get("__name__", "")
    if caller_module != "tools.tailortalk_tool":
        raise RuntimeError(
            f"tailortalk_auth.{op_name}() must be called via the tailortalk_login "
            "tool (tools/tailortalk_tool.py), never directly -- not from "
            "execute_code, a shelled-out python3 -c, or any ad-hoc script."
        )


def _reject_if_sandboxed(op_name: str) -> None:
    """Refuse vault-writing operations inside the execute_code sandbox.

    The sandbox has no vault socket (by design), so an exchange run there
    would burn the one-time authorization code and then lose the tokens.
    """
    if "HERMES_RPC_SOCKET" in os.environ:
        raise RuntimeError(
            f"tailortalk_auth.{op_name}() cannot run inside the execute_code "
            "sandbox -- it has no vault socket, so a successful TailorTalk "
            "exchange would be silently lost and the one-time code burned. "
            "Use the tailortalk_login tool instead."
        )


# ---------------------------------------------------------------------------
# Dynamic client registration (app-level, cached in the vault)
# ---------------------------------------------------------------------------

def _load_dcr_from_vault() -> dict | None:
    vault = _vault()
    try:
        return json.loads(vault.get_token(_DCR_USER_ID, DCR_SERVICE_NAME))
    except (vault.VaultNoTokenError, vault.VaultError, json.JSONDecodeError):
        return None


def _store_dcr_in_vault(payload: dict) -> None:
    _vault().set_token(_DCR_USER_ID, DCR_SERVICE_NAME, json.dumps(payload))


def _get_or_register_client() -> dict:
    """Return the cached DCR registration (``client_id`` + optional
    ``client_secret``), registering a new client if there is none or the
    cached one was registered with a different redirect_uri / auth method."""
    cached = _load_dcr_from_vault()
    if cached and cached.get("client_id"):
        same_redirect = cached.get("redirect_uri", "") == REDIRECT_URI
        same_method = cached.get("token_endpoint_auth_method", "none") == TOKEN_AUTH_METHOD
        if same_redirect and same_method:
            return cached
        logger.info(
            "TailorTalk DCR: cached client %s registered with redirect_uri=%r "
            "auth_method=%r, current is %r/%r -- re-registering",
            cached.get("client_id"), cached.get("redirect_uri"),
            cached.get("token_endpoint_auth_method"), REDIRECT_URI, TOKEN_AUTH_METHOD,
        )

    resp = httpx.post(
        REGISTRATION_ENDPOINT,
        json={
            "client_name": "Hermes AI Agent",
            "redirect_uris": [REDIRECT_URI],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": TOKEN_AUTH_METHOD,
            "scope": SCOPE,
        },
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("client_id"):
        raise RuntimeError(f"TailorTalk DCR response missing client_id: {payload}")

    payload["redirect_uri"] = REDIRECT_URI
    payload.setdefault("token_endpoint_auth_method", TOKEN_AUTH_METHOD)
    _store_dcr_in_vault(payload)
    logger.info("TailorTalk DCR: registered new client_id=%s", payload["client_id"])
    return payload


def _client_auth_fields(client: dict) -> dict:
    """Form fields identifying Hermes to the token endpoint."""
    fields = {"client_id": client["client_id"]}
    if client.get("client_secret"):
        fields["client_secret"] = client["client_secret"]
    return fields


# ---------------------------------------------------------------------------
# PKCE / auth URL
# ---------------------------------------------------------------------------

def _generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) per RFC 7636 (S256)."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode("ascii")
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    return verifier, challenge


def _clear_auth_url_cache() -> None:
    _auth_url_cache.pop(_session_user_id(), None)


def _clear_notify_context() -> None:
    _notify_context.pop(_session_user_id(), None)


def _has_valid_cached_url() -> bool:
    cached = _auth_url_cache.get(_session_user_id())
    return bool(cached) and (time.time() - cached[0]) < _AUTH_URL_COOLDOWN_SECONDS


def set_notify_context(platform: str, chat_id: str) -> None:
    tid = _session_user_id()
    _notify_context[tid] = {"platform": platform, "chat_id": chat_id}
    logger.debug("tailortalk notify_context set for %s: platform=%s chat_id=%s", tid, platform, chat_id)


def get_notify_context() -> dict[str, str]:
    return _notify_context.get(_session_user_id(), {})


def get_auth_url() -> str:
    """Build the TailorTalk authorization URL for the current session's user.

    Idempotent within ``_AUTH_URL_COOLDOWN_SECONDS``. The PKCE verifier is
    carried in ``state`` as ``"{user_id}:{code_verifier}"`` so the callback
    handler can complete the exchange out of process; the verifier is
    URL-safe base64 (never contains ':'), so splitting on the first ':' is
    safe.
    """
    _reject_if_not_called_from_tailortalk_tool("get_auth_url")
    tid = _session_user_id()
    now = time.time()
    cached = _auth_url_cache.get(tid)
    if cached and (now - cached[0]) < _AUTH_URL_COOLDOWN_SECONDS:
        logger.info("Reusing cached TailorTalk auth URL for user %s", tid)
        return cached[1]

    client = _get_or_register_client()
    verifier, challenge = _generate_pkce()
    params = {
        "response_type": "code",
        "client_id": client["client_id"],
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": f"{tid}:{verifier}",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        # RFC 8707 resource indicator, required by the MCP authorization
        # spec; value from TailorTalk's protected-resource metadata.
        "resource": MCP_URL,
    }
    url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
    _auth_url_cache[tid] = (now, url)
    logger.info("Generated fresh TailorTalk auth URL for user %s", tid)
    return url


# ---------------------------------------------------------------------------
# Token storage / exchange / refresh
# ---------------------------------------------------------------------------

def _store_token_payload(payload: dict) -> None:
    uid = _canonical_uid(_session_user_id())
    record = dict(payload)
    record["obtained_at"] = time.time()
    _vault().set_token(uid, SERVICE_NAME, json.dumps(record))


def exchange_and_store(code: str, code_verifier: str) -> None:
    """Exchange an authorization code for tokens and store them in the vault.
    Identity is derived from the session context, never from a parameter."""
    _reject_if_sandboxed("exchange_and_store")
    tid = _session_user_id()
    client = _get_or_register_client()
    resp = httpx.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
            "resource": MCP_URL,
            **_client_auth_fields(client),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(
            f"TailorTalk token exchange failed ({resp.status_code}): {resp.text[:500]}"
        )
    payload = resp.json()
    if not payload.get("access_token"):
        raise RuntimeError(f"TailorTalk token response missing access_token: {payload}")

    _store_token_payload(payload)
    _clear_auth_url_cache()
    logger.info("TailorTalk token stored user_id=%s service=%s", _canonical_uid(tid), SERVICE_NAME)


def has_token() -> bool:
    uid = _canonical_uid(_session_user_id())
    return _vault().has_token(uid, SERVICE_NAME, session_uid=uid)


def _refresh(refresh_token: str) -> dict:
    _reject_if_sandboxed("_refresh")
    client = _get_or_register_client()
    resp = httpx.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "resource": MCP_URL,
            **_client_auth_fields(client),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(
            f"TailorTalk token refresh failed ({resp.status_code}): {resp.text[:500]}"
        )
    payload = resp.json()
    if not payload.get("access_token"):
        raise RuntimeError(f"TailorTalk refresh response missing access_token: {payload}")
    # A refresh response without refresh_token means "keep using the old one".
    if not payload.get("refresh_token"):
        payload["refresh_token"] = refresh_token
    _store_token_payload(payload)
    return payload


def get_valid_access_token(*, force_refresh: bool = False) -> str:
    """Return a valid TailorTalk access token for the session user, refreshing
    when expired (or when ``force_refresh`` is set, e.g. after a 401).

    Raises ``tools.gws_vault_client.VaultNoTokenError`` if the user has never
    authorized -- callers direct the user to ``tailortalk_login``.
    """
    uid = _canonical_uid(_session_user_id())
    record = json.loads(_vault().get_token(uid, SERVICE_NAME, session_uid=uid))

    obtained_at = record.get("obtained_at", 0)
    expires_in = record.get("expires_in")
    access_token = record.get("access_token")

    is_expired = False
    if expires_in is not None:
        is_expired = (obtained_at + float(expires_in) - 60) <= time.time()  # 60s skew

    if (is_expired or force_refresh) and record.get("refresh_token"):
        record = _refresh(record["refresh_token"])
        access_token = record.get("access_token")

    if not access_token:
        raise RuntimeError("TailorTalk token record has no access_token -- re-authorize.")
    return access_token
