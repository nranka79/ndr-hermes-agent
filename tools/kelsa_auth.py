"""
Per-user OAuth 2.1 (PKCE, dynamic client registration) token manager for
Kelsa MCP ("Kelsa-Read", https://kelsa.io/mcp).

Mirrors tools/gws_auth.py's shape (state-encoded identity + gws-vault
storage) but adapted for Kelsa's MCP-spec-compliant OAuth server:

  - Dynamic Client Registration (RFC 7591) at POST /oauth/register -- no
    manually-provisioned client_id/secret needed, unlike Google.
  - Public client only (``token_endpoint_auth_methods_supported: ["none"]``),
    so PKCE (S256) is REQUIRED on every authorize + token exchange -- unlike
    Google, where Hermes is a confidential client and PKCE is skipped.
  - Refresh tokens ARE supported (grant_types_supported includes
    "refresh_token").
  - RFC 8707 resource indicator required (Kelsa's consent page silently
    no-ops on "Authorize" without it -- confirmed 2026-07-13).
  - **localhost-only redirect_uri.** Kelsa's OAuth server does not accept a
    public HTTPS redirect_uri at all -- confirmed 2026-07-13 by a hung
    consent page with zero request ever reaching our server, then found
    documented in skills/productivity/kelsa-mcp/SKILL.md ("Kelsa accepts
    http://127.0.0.1:<port>/callback -- no HTTPS tunnel or public URL
    needed"), from earlier real operational experience with Kelsa predating
    this pilot. Confirmed 2026-07-13 against
    https://kelsa.io/.well-known/oauth-authorization-server for the rest of
    the metadata.

Root cause this pilot originally fixed: Kelsa-Read was previously configured
under mcp_servers with ``auth: oauth``, which routes through
tools/mcp_oauth.py's *local interactive* flow (opens a browser, listens on a
localhost callback port). That flow cannot complete inside a headless Docker
gateway process -- it silently fails with "non-interactive environment and
no cached tokens", the server connection raises, and zero Kelsa tools get
registered.

Because Kelsa rejects non-localhost redirects outright, a fully automatic
public-callback flow (like tools/gws_auth.py uses for Google) is not
possible here. Instead: the redirect_uri is a fixed, never-listened-on
``http://127.0.0.1:<PSEUDO_PORT>/callback`` placeholder. After the user
authorizes, their OWN browser tries to load that URL, fails to connect
(nothing listens on their machine), but the address bar still shows the
full redirect URL with ``code=`` and ``state=`` -- the user copies that and
pastes it back into Telegram. tools/kelsa_tool.py's ``kelsa_complete_login``
tool parses the paste and finishes the exchange. This is the same
paste-back mechanism tools/mcp_oauth.py's interactive CLI flow already uses
for this exact server (see the SKILL.md "OAuth in a Non-Interactive
(Headless) Environment" section) -- reimplemented here so it can be driven
per-user, from Telegram, with vault-backed storage instead of a single
shared flat-file token.

PILOT SCOPE (Phase 1, 2026-07-13): proves the auth loop for a single user.
    Token storage/refresh here IS already generically multi-user (vault is
    keyed by canonical uid), but the MCP connection layer that consumes these
    tokens (tools/kelsa_tool.py) opens one ephemeral connection per call rather
    than a pooled persistent connection -- that generalization is Phase 2.

2026-07-19 three-layer fix for duplicate-button problem:

  **Layer 1 (tools/kelsa_auth.py):** ``get_auth_url()`` is now idempotent
  within a 5-minute cooldown. Repeated calls for the same user return the
  same URL with the same PKCE verifier. The ``REDIRECT_URI`` is configurable
  via ``KELSA_REDIRECT_URI`` env var (defaults to the 127.0.0.1 placeholder)
  for when Kelsa eventually supports public HTTPS callbacks.

  **Layer 2 (tools/kelsa_tool.py):** ``_not_authorized_result()`` no longer
  auto-generates auth URLs. ``kelsa_list_tools`` and ``kelsa_call_tool``
  return a clear error directing the caller to use ``kelsa_login`` instead.

  **Layer 3 (tools/kelsa_tool.py):** A process-global ``_pending_auth`` set
  prevents a second ``kelsa_login`` from generating a new URL while a
  previous auth is still outstanding for the same user.

Usage:
    from tools.kelsa_auth import get_auth_url, exchange_and_store, has_token, get_valid_access_token, parse_callback_paste
    url = get_auth_url(telegram_id)                            # send to user
    code, state = parse_callback_paste(pasted_text)             # from kelsa_complete_login
    exchange_and_store(telegram_id, code, code_verifier)        # code_verifier extracted from state
    has_token(telegram_id)                                      # bool
    token = get_valid_access_token(telegram_id)                 # refreshes if needed
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import time
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

logger = logging.getLogger(__name__)

ISSUER = "https://kelsa.io"
AUTHORIZATION_ENDPOINT = "https://kelsa.io/oauth/authorize"
TOKEN_ENDPOINT = "https://kelsa.io/oauth/token"
REGISTRATION_ENDPOINT = "https://kelsa.io/oauth/register"
MCP_URL = "https://kelsa.io/mcp"

# Configurable via KELSA_REDIRECT_URI env var. When Kelsa's OAuth server
# eventually supports public HTTPS redirect URIs (it currently does not --
# see module docstring), set this to your public callback URL:
#
#   KELSA_REDIRECT_URI=https://transcribe.ahfl.in/kelsa/auth/callback
#
# Until then, this stays as the 127.0.0.1 placeholder that satisfies
# Kelsa's redirect_uri validation. The user's browser will fail to
# connect here after authorizing; that's expected -- they copy the URL
# from the address bar and paste it back (paste-back flow).
REDIRECT_URI = os.environ.get(
    "KELSA_REDIRECT_URI",
    "http://127.0.0.1:47562/callback",
)

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
#
# Filename bumped to v2 (2026-07-13) -- the v1 file cached a client
# registered against the old, non-working public HTTPS redirect_uri. Rather
# than migrate/validate the old file, just start clean under a new name so
# there's no chance of silently reusing a stale registration.
_CLIENT_INFO_FILENAME = "kelsa-read-dcr-client-v2.json"

# Auth URL idempotency cache (Layer 1 of the duplicate-button fix).
# Maps telegram_id -> (generated_at_timestamp, url). Prevents
# get_auth_url() from generating a new PKCE verifier + URL if the
# user already has a valid one outstanding.
_auth_url_cache: dict[str, tuple[float, str]] = {}
# How long a cached auth URL remains valid before a fresh one is
# generated (seconds). 5 minutes should be more than enough for
# the user to click the button and authorize.
_AUTH_URL_COOLDOWN_SECONDS = 300

# Notification context for the callback handler. Maps telegram_id ->
# {"platform": str, "chat_id": str}. Set when kelsa_login delivers an
# auth URL (tools/kelsa_tool.py), consumed by the callback handler
# (gateway/platforms/api_server.py) so the success notification goes
# back through the same channel the user initiated from (Telegram,
# Open Web UI, CLI, WhatsApp, Slack, etc.).
_notify_context: dict[str, dict[str, str]] = {}


def _client_info_path():
    from tools.mcp_oauth import _get_token_dir
    return _get_token_dir() / _CLIENT_INFO_FILENAME


def _clear_auth_url_cache(telegram_id: str) -> None:
    """Remove the cached auth URL for this user, forcing the next call to
    ``get_auth_url()`` to generate a fresh PKCE challenge + URL.

    Called after a successful token exchange (the cached URL is one-time use)
    or when a cooldown timeout is desired (e.g. user wants a fresh URL).
    """
    _auth_url_cache.pop(telegram_id, None)
    _notify_context.pop(telegram_id, None)


def _has_valid_cached_url(telegram_id: str) -> bool:
    """Return True if there is a non-expired cached auth URL for this user.

    Used by ``kelsa_tool._pending_auth`` guard to avoid blocking a fresh
    ``kelsa_login`` when the previous auth attempt's cache has expired but
    the ``_pending_auth`` set still has the user's id (e.g. the user
    abandoned the first attempt and came back later).
    """
    cached = _auth_url_cache.get(telegram_id)
    if cached is None:
        return False
    return (time.time() - cached[0]) < _AUTH_URL_COOLDOWN_SECONDS


def set_notify_context(telegram_id: str, platform: str, chat_id: str) -> None:
    """Record which platform + chat the user initiated the Kelsa auth from.

    The callback handler (api_server.py) reads this to send the success
    notification back through the same channel (Telegram, Open Web UI,
    CLI, WhatsApp, Slack, etc.) instead of always using Telegram.
    """
    _notify_context[telegram_id] = {"platform": platform, "chat_id": chat_id}
    logger.debug("notify_context set for %s: platform=%s chat_id=%s", telegram_id, platform, chat_id)


def get_notify_context(telegram_id: str) -> dict[str, str]:
    """Return the notification context for this user, or an empty dict.

    Called by the callback handler after a successful token exchange to
    determine where to send the "authorized" message.
    """
    return _notify_context.get(telegram_id, {})


def _get_or_register_client() -> str:
    """Return the cached DCR client_id, registering a new one if needed.

    If the cached client was registered with a different redirect_uri than
    the current ``REDIRECT_URI`` (e.g. after switching from the 127.0.0.1
    placeholder to a public HTTPS callback), the stale cache is discarded
    and a new DCR registration is performed automatically.
    """
    path = _client_info_path()
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            client_id = data.get("client_id")
            cached_redirect = data.get("redirect_uri", "")
            if client_id and cached_redirect == REDIRECT_URI:
                return client_id
            if client_id and cached_redirect != REDIRECT_URI:
                logger.info(
                    "Kelsa DCR: cached redirect_uri %r differs from current %r "
                    "-- discarding stale client_id %s and re-registering",
                    cached_redirect, REDIRECT_URI, client_id,
                )
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
    payload["redirect_uri"] = REDIRECT_URI
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


def _reject_if_sandboxed(op_name: str) -> None:
    """Refuse to run a vault-writing Kelsa OAuth operation from inside the
    execute_code sandbox.

    2026-07-19 incident: in a session where kelsa_login/kelsa_complete_login
    were not available as real tools (see tools/kelsa_tool.py, toolsets.py),
    the agent hand-rolled this exchange via execute_code instead. The httpx
    call to Kelsa's token endpoint succeeded -- burning the one-time
    authorization code -- but the vault write then crashed with
    "GWS_VAULT_SOCKET is not set" (the sandbox has no direct vault socket by
    design; see tools/gws_auth.py's 2026-07-18 vault impersonation fix). The
    freshly-granted tokens were silently lost, and a retry with the same
    (now-dead) code failed with invalid_grant -- the user had to authorize
    Kelsa again from scratch. This guard fails BEFORE calling Kelsa at all,
    so a one-time authorization code is never burned for nothing. Callers
    must go through the trusted-process kelsa_login / kelsa_complete_login
    tools (tools/kelsa_tool.py), never call tools.kelsa_auth functions
    directly inside execute_code.
    """
    if "HERMES_RPC_SOCKET" in os.environ:
        raise RuntimeError(
            f"kelsa_auth.{op_name}() cannot run inside the execute_code "
            "sandbox -- it has no direct vault socket, so a successful "
            "Kelsa exchange would be silently lost and the one-time code "
            "burned for nothing. Use the kelsa_login / kelsa_complete_login "
            "tools instead (they run in the trusted main process with real "
            "vault access)."
        )


def get_auth_url(telegram_id: str) -> str:
    """Build a Kelsa OAuth authorization URL for a user.

    **Idempotent:** if called again for the same ``telegram_id`` within
    ``_AUTH_URL_COOLDOWN_SECONDS`` (5 minutes), returns the **same** URL
    with the **same** PKCE code_challenge. This prevents the LLM from
    generating multiple auth buttons per user (Layer 1 of the
    duplicate-button fix).

    The PKCE code_verifier is encoded into ``state`` as
    ``"{telegram_id}:{code_verifier}"`` because the code exchange happens
    later, out of process (the user pastes the failed-redirect URL back into
    Telegram, potentially in a different gateway worker) -- the same trick
    tools/gws_auth.py uses to carry the service_name through state, adapted
    here to carry the PKCE verifier instead. The verifier is opaque URL-safe
    base64 (no ':'), so splitting on the first ':' when parsing is safe.
    """
    now = time.time()
    cached = _auth_url_cache.get(telegram_id)
    if cached and (now - cached[0]) < _AUTH_URL_COOLDOWN_SECONDS:
        logger.info(
            "Reusing cached Kelsa auth URL for user %s "
            "(%.0f seconds remaining in cooldown)",
            telegram_id,
            _AUTH_URL_COOLDOWN_SECONDS - (now - cached[0]),
        )
        return cached[1]

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
        # RFC 8707 resource indicator -- required by MCP's Authorization
        # spec (2025-06-18) so the server knows which protected resource
        # (this MCP endpoint) the grant is for. Omitting it caused Kelsa's
        # consent page to silently no-op on "Authorize" (confirmed
        # 2026-07-13 against the reference mcp SDK's OAuthClientProvider
        # flow, which always includes this param).
        "resource": MCP_URL,
    }
    url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
    _auth_url_cache[telegram_id] = (time.time(), url)
    logger.info(
        "Generated fresh Kelsa auth URL for user %s (cache expires in %ds)",
        telegram_id, _AUTH_URL_COOLDOWN_SECONDS,
    )
    return url


def parse_callback_paste(pasted: str) -> tuple[str, str]:
    """Extract (code, state) from whatever the user pasted back.

    Accepts either a full failed-redirect URL
    (``http://127.0.0.1:47562/callback?code=...&state=...``) or just the
    query-string portion (``code=...&state=...`` or ``?code=...&state=...``).

    Raises ValueError with a clear message if code/state can't be found.
    """
    text = (pasted or "").strip()
    if not text:
        raise ValueError("Nothing was pasted.")

    if "://" in text:
        query = urlparse(text).query
    else:
        query = text.lstrip("?")

    parsed = parse_qs(query)
    code = (parsed.get("code") or [None])[0]
    state = (parsed.get("state") or [None])[0]

    if not code or not state:
        raise ValueError(
            "Could not find both 'code' and 'state' in the pasted text. "
            "Paste the full URL from the browser's address bar after "
            "authorizing (it will look like a connection-error page at "
            "127.0.0.1 -- that's expected, the URL itself is what matters)."
        )
    return code, state


def _store_token_payload(telegram_id: str, payload: dict) -> None:
    from tools import gws_vault_client as vault
    from tools.gws_auth import canonical_uid

    uid = canonical_uid(telegram_id)
    record = dict(payload)
    record["obtained_at"] = time.time()
    vault.set_token(uid, SERVICE_NAME, json.dumps(record))


def exchange_and_store(telegram_id: str, code: str, code_verifier: str) -> None:
    """Exchange an authorization code for tokens and store them in the vault."""
    _reject_if_sandboxed("exchange_and_store")
    client_id = _get_or_register_client()
    resp = httpx.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "code_verifier": code_verifier,
            "resource": MCP_URL,
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
    _clear_auth_url_cache(telegram_id)
    logger.info("Kelsa token stored user_id=%s service=%s", uid, SERVICE_NAME)


def has_token(telegram_id: str) -> bool:
    from tools import gws_vault_client as vault
    from tools.gws_auth import canonical_uid

    uid = canonical_uid(telegram_id)
    return vault.has_token(uid, SERVICE_NAME, session_uid=uid)


def _refresh(telegram_id: str, refresh_token: str) -> dict:
    _reject_if_sandboxed("_refresh")
    client_id = _get_or_register_client()
    resp = httpx.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "resource": MCP_URL,
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
