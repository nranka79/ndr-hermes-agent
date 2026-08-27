"""
Per-user OAuth token manager for Google Workspace (Gmail, Calendar, Drive).

Tokens are stored in the gws-vault daemon (Unix socket) under per-service keys,
NOT on the filesystem.  Each Google account (email) automatically maps to a
distinct service name so multiple accounts per Telegram user never overwrite
each other.

Tokens are keyed by the **canonical** vault user_id — a channel-agnostic
surrogate (e.g. ``ndr-1000000001``) resolved from the session's raw channel
identifier (Telegram numeric id, SSO email, slug) via the vault ``resolve``
op.  This means a token authorized from any channel is readable from every
channel, and a user with only a phone/Telegram/Slack id (no email) is handled
identically to one with an email.

Service naming convention (``EMAIL_TO_SERVICE``):
    google              — default / legacy / primary
    google-draas        — ndr@draas.com
    google-ahfl         — ndr@ahfl.in
    google-gmail        — nishantranka@gmail.com

When a user authorizes via the OAuth callback, the token's email is extracted
from the Google ``id_token`` (JWT) returned in the token exchange response.
The email is looked up in ``EMAIL_TO_SERVICE``, and the token is automatically
stored under the correct service key.  If the email is not recognised, the
caller is asked to define a new service name — no manual ``service_name``
parameter needed for the default callback flow.

Usage from skill code (terminal or execute_code):
    from tools.gws_auth import build_service, get_auth_url
    svc = build_service("gmail", "v1")                   # default service
    svc = build_service("gmail", "v1", service_name="google-ahfl")
    url = get_auth_url()                                 # default service
    url = get_auth_url(login_hint="user@example.com")

The session user id is read from HERMES_SESSION_USER_ID env var,
which is injected into every subprocess by the gateway. Callers must
NEVER supply a user id -- identity comes from the session context ONLY.

Sandboxed execute_code note (2026-07-18 vault impersonation fix): the
execute_code sandbox no longer has direct socket access to gws-vault
(GWS_VAULT_SOCKET is not in its environment). load_credentials() detects
sandboxed context and routes through the gws_fetch_token RPC tool instead
(see tools/gws_fetch_token_tool.py for the full rationale) -- this function's
own call signature and behavior are unchanged for callers either way.
"""

import base64
import json
import logging
import os
import re

# oauthlib does an exact-string comparison of requested vs granted scope on
# token exchange. Google frequently echoes the granted scopes back in a
# DIFFERENT ORDER than requested (not a real scope change) -- with strict
# comparison this raises 'Scope has changed from ... to ...' and kills the
# /gws/auth/callback request (2026-07-14: broke YouTube scope rollout). Must
# be set before google_auth_oauthlib.flow is imported/used. Same fix already
# proven in plugins/platforms/google_chat/oauth.py and
# skills/productivity/google-workspace/scripts/setup.py -- ported here since
# this module is the sole sanctioned GWS OAuth path (see SOUL.md).
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

logger = logging.getLogger(__name__)

# All scopes granted once; user authorizes the full set at first login.
# NOTE: this list is the target for NEW authorizations only (get_auth_url /
# exchange_and_store below). It is intentionally NOT used to override the
# scopes of an EXISTING stored token in load_credentials() -- see the 2026-07
# fix there. Forcing this list onto every loaded token meant that adding a
# single new scope here broke refresh (and therefore ALL API access, Gmail
# included) for every account that had not yet been individually re-authed,
# because Google's refresh_token grant requires every requested scope to
# already be authorized for that refresh_token or it rejects the whole grant
# with invalid_scope.
HERMES_GWS_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    # Gmail settings (2026-08-27): allows creating/reading/deleting mailbox
    # filters + labels via users.settings.filters.* . Basic = own mailbox only.
    # NOTE: adding a NEW scope requires a fresh OAuth re-consent (prompt=consent);
    # the existing refresh token cannot pick this up (see load_credentials notes).
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    # Google Photos. Post-2025-03-31 the broad photoslibrary scopes no longer
    # exist — reading a user's pre-existing library is Picker-API-only (user
    # selects items in the Google Photos UI), and the Library API only touches
    # app-created content. See tools/gws_skill_bridge.py photos_* operations.
    "https://www.googleapis.com/auth/photospicker.mediaitems.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata",
    # YouTube (2026-07-14): full manage scope, not just youtube.upload --
    # covers upload + read/list/edit/delete of the user's own videos,
    # playlists, comments. This is a Google 'restricted' scope; internal/
    # testing OAuth clients are fine, a public-facing app would need CASA
    # verification before this scope is usable for external users.
    "https://www.googleapis.com/auth/youtube",
]

_REDIRECT_URI = "https://transcribe.ahfl.in/gws/auth/callback"

# Default service name — backward-compatible fallback when the OAuth state
# does not include a service name.  In practice the auto-detect path in
# exchange_and_store() uses EMAIL_TO_SERVICE (below) to pick the right key
# from the id_token email, so _DEFAULT_SERVICE is only hit when no id_token
# email is available and the user has no gws_service field in users.json.
_DEFAULT_SERVICE = "google"

# Map well-known emails to their vault service names so the agent
# can look up the right token by email address, and so the OAuth
# callback can auto-detect the service name from the id_token email.
#
# Service-name format is enforced by the vault server at
# tools/gws_vault_client.py:42 — must match ``^[a-z][a-z0-9-]{0,49}$``
# (lowercase, alphanumeric + hyphens only — NO dots, NO underscores).
# This is also the value stored in users.json under "gws_service".
EMAIL_TO_SERVICE = {
    "ndr@draas.com":          "google-draas",
    "psingh@draas.com":       "google-draas",
    "rnr@draas.com":          "google-draas",
    "vkdas@draas.com":        "google-draas",
    "pm2.blr@draas.com":      "google-draas",
    "sales1.blr@draas.com":   "google-draas",
    "ndr@ahfl.in":            "google-ahfl",
    "nishantranka@gmail.com": "google-gmail",
}


class UnknownGoogleAccountError(ValueError):
    """Raised when the authorized Google account's email is not in
    ``EMAIL_TO_SERVICE`` and no fallback key could be used.
    """
    def __init__(self, email: str):
        self.email = email
        super().__init__(
            f"Authorized Google account {email} is not in EMAIL_TO_SERVICE. "
            f"Tell me what vault service name to use (e.g. google-{email.split('@')[0]})."
        )


def _client_config() -> dict:
    client_id = os.environ.get("HERMES_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("HERMES_OAUTH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise EnvironmentError(
            "HERMES_OAUTH_CLIENT_ID and HERMES_OAUTH_CLIENT_SECRET must be set"
        )
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": [_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _current_telegram_id() -> str:
    """Get the raw channel id of the active session user — session context ONLY.

    Uses ``gateway.session_context.get_gws_identity_env`` (per-task ContextVar
    with os.environ fallback for subprocess/sandbox/cron contexts, plus the
    cron job-owner fallback). This is the single source of user identity for
    every GWS token operation; callers must never supply their own id.
    """
    try:
        from gateway.session_context import get_gws_identity_env
        tid = get_gws_identity_env().strip()
    except Exception:
        tid = os.environ.get("HERMES_SESSION_USER_ID", "").strip()
    if not tid:
        raise ValueError(
            "No session user context (HERMES_SESSION_USER_ID not set). "
            "Cannot determine which user's token to load."
        )
    return tid


def canonical_uid(channel_id) -> str:
    """Resolve a raw channel identifier to the canonical vault user_id.

    The canonical user_id is a channel-agnostic surrogate (e.g.
    ``ndr-1000000001``) stored in the vault identity records.  Every raw
    identifier — Telegram numeric id, SSO email, slug — resolves to it via the
    vault ``resolve`` op, so a token written after one channel's OAuth is
    readable from every channel, and the read path can satisfy the vault's
    ``session_uid == user_id`` check by passing the same canonical id as both.

    Falls back to the raw id when the vault can't resolve it, so single-key /
    unmigrated users keep working unchanged.
    """
    cid = str(channel_id or "").strip()
    if not cid:
        return cid
    try:
        from tools import gws_vault_client as vault

        if cid.isdigit():
            uid = vault.resolve("telegram", cid)
        elif "@" in cid:
            uid = vault.resolve("email", cid)
        else:
            uid = vault.resolve("slug", cid) or vault.resolve("draas_user_id", cid)
        if uid:
            return uid
        # Vault reached fine but has no identity mapping for this raw id.
        # Falling back to the raw id here is the #1 cause of false
        # not-authorized reports: if the token was actually stored under a
        # *different* canonical uid, this lookup will silently miss it and
        # look identical to "never authorized". Log at WARNING (not debug)
        # so this is visible in agent.log instead of silently masked.
        logger.warning(
            "canonical_uid: vault has no identity mapping for %r -- "
            "using raw id as fallback key. If the user believes they are "
            "already authorized, this is almost certainly why the lookup "
            "is failing -- do NOT tell the user the vault is down.",
            cid,
        )
    except Exception:
        logger.warning(
            "canonical_uid: vault resolve failed for %r -- falling back to "
            "raw id (may cause false 'not authorized' results)",
            cid, exc_info=True,
        )
    return cid


def _parse_state(state: str) -> tuple[str, str]:
    """Parse the OAuth state parameter.

    Supports two formats:
      ``"1000000001"``                    → (telegram_id, "google")
      ``"1000000001:google-ahfl"``         → (telegram_id, "google-ahfl")

    Returns (telegram_id, service_name).
    """
    if ":" in state:
        tid, svc = state.split(":", 1)
        return tid.strip(), svc.strip()
    return state.strip(), _DEFAULT_SERVICE


def _decode_id_token_email(id_token: str) -> str | None:
    """Decode a Google ID token JWT and return the ``email`` claim.

    The ID token is a three-part JWT (header.payload.signature).  The
    payload is base64url-encoded JSON that contains the ``email`` field
    when the ``email`` scope was granted.
    """
    if not id_token:
        return None
    try:
        parts = id_token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)
        return claims.get("email") or None
    except Exception:
        return None


def _account_email(creds) -> str | None:
    """Return the authoritative email of the authorized Google account.

    Prefers the ``id_token`` email (present only when the ``openid``/``email``
    scope is granted).  Falls back to the Gmail profile — which uses the
    ``gmail.modify`` scope we always request — so the correct account is
    identified even without the ``openid`` scope, and a token is always filed
    under the right service key.
    """
    id_token = getattr(creds, "id_token", None)
    email = _decode_id_token_email(id_token) if id_token else None
    if email:
        return email
    try:
        gm = build("gmail", "v1", credentials=creds)
        return gm.users().getProfile(userId="me").execute().get("emailAddress") or None
    except Exception:
        logger.debug("account email: gmail getProfile fallback failed", exc_info=True)
        return None


def _detect_service_from_credentials(creds: Credentials) -> str | None:
    """Try to determine the vault service name from the credentials.

    Priority:
      1. Extract email from the ID token embedded in the credentials.
      2. Look up the email in ``EMAIL_TO_SERVICE``.

    Returns the service name or ``None`` if unresolvable.
    """
    id_token = getattr(creds, "id_token", None)
    email = _decode_id_token_email(id_token) if id_token else None
    if email:
        svc = EMAIL_TO_SERVICE.get(email)
        if svc:
            return svc
        raise UnknownGoogleAccountError(
            f"Authorized Google account {email} is not in EMAIL_TO_SERVICE. "
            f"Please tell me what service name to use for this account "
            f"(e.g. google-{email.split('@')[0]})."
        )
    return None


def load_credentials(service_name: str = _DEFAULT_SERVICE) -> Credentials:
    """Load stored OAuth credentials for the current session's user.

    Identity is derived from the session context ONLY -- the session's
    raw channel id (Telegram numeric id, etc.) is resolved to the canonical
    vault user_id internally. Callers must never supply a user id.

    Raises :class:`FileNotFoundError` if no token exists -- caller should
    direct the user to authorize via :func:`get_auth_url`.

    Args:
        service_name: Vault service key (e.g. ``"google-draas"``).

    Sandboxed execute_code dispatch (2026-07-18 vault impersonation fix):
    when running inside the execute_code sandbox (detected via
    ``HERMES_RPC_SOCKET`` in the environment -- the same signal
    tools/code_execution_tool.py sets for every sandboxed child), this
    function has no direct socket to gws-vault at all (GWS_VAULT_SOCKET is
    not passed into the sandbox's environment). Instead it routes through
    the ``gws_fetch_token`` RPC tool (tools/gws_fetch_token_tool.py) over the
    same sandbox<->gateway channel every other sandboxed tool call already
    uses. That tool's handler resolves identity via :func:`_current_telegram_id`
    itself inside the trusted main process. Outside the sandbox (the trusted
    main process), behavior is unchanged: talks to the vault directly.
    """
    if "HERMES_RPC_SOCKET" in os.environ:
        from hermes_tools import gws_fetch_token  # sandbox-generated stub
        resp = gws_fetch_token(service_name=service_name)
        if isinstance(resp, dict) and resp.get("error"):
            if resp.get("needs_auth"):
                raise FileNotFoundError(resp["error"])
            raise RuntimeError(resp["error"])
        token_json = resp["token_json"] if isinstance(resp, dict) else resp
        return Credentials.from_authorized_user_info(json.loads(token_json))
    return _load_credentials_direct(service_name)


def _load_credentials_direct(service_name: str = _DEFAULT_SERVICE) -> Credentials:
    """Load stored OAuth credentials directly from the gws-vault daemon.

    TRUSTED-PROCESS ONLY. Never call this from code that might run inside
    the execute_code sandbox -- use :func:`load_credentials` instead, which
    dispatches correctly for both contexts. This is the implementation
    :func:`load_credentials` uses on its direct path, and what the
    ``gws_fetch_token`` RPC tool's handler calls on behalf of sandboxed
    requests (always with the trusted session's own id, never anything a
    sandboxed caller supplies).

    Scope handling (2026-07 fix): the returned ``Credentials`` use whatever
    scopes are actually stored in the vault token JSON -- ``HERMES_GWS_SCOPES``
    is intentionally NOT forced onto an existing token here. Previously this
    function overrode ``.scopes`` to the current ``HERMES_GWS_SCOPES`` on every
    load, so any token authorized before a scope was added to that constant
    would fail Google's refresh grant with ``invalid_scope`` -- and because
    the request bundles every scope into a single refresh call, that ONE
    missing scope broke refresh (and therefore ALL API access -- Gmail,
    Calendar, Sheets, everything) for that account, not just the feature that
    needed the new scope. Loading with the token's own stored scopes means a
    stale/narrower token still refreshes fine for everything it WAS
    authorized for; only the genuinely new capability is unavailable until
    the user re-authorizes via :func:`get_auth_url` (which does use the full
    current ``HERMES_GWS_SCOPES`` list, since that's a fresh consent grant).
    """
    from tools import gws_vault_client as vault
    tid = _current_telegram_id()
    uid = canonical_uid(tid)
    token_json = vault.get_token(uid, service_name, session_uid=uid)
    creds = Credentials.from_authorized_user_info(json.loads(token_json))
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        try:
            vault.set_token(uid, service_name, creds.to_json())
        except vault.VaultUnauthorizedError:
            # Only reachable if this ever runs somewhere without
            # GWS_VAULT_SECRET (this function is trusted-process-only, which
            # normally has it) -- keep the refreshed creds usable in-memory
            # rather than failing the caller's request over a write-back.
            logger.debug(
                'vault write-back skipped for %s/%s (no vault secret in this '
                'process); using refreshed creds in-memory',
                uid, service_name,
            )
    return creds


def save_credentials(creds: Credentials, service_name: str = _DEFAULT_SERVICE) -> None:
    """Store OAuth credentials in the gws-vault daemon under the given service key.

    The canonical vault user_id is derived from the session context.
    """
    from tools import gws_vault_client as vault
    from tools.gws_auth import canonical_uid
    tid = _current_telegram_id()
    uid = canonical_uid(tid)
    vault.set_token(uid, service_name, creds.to_json())


def build_service(api: str, version: str, service_name: str = _DEFAULT_SERVICE):
    """
    Build a Google API client using the stored per-user OAuth token.

    Identity comes from the SESSION ONLY (:func:`_current_telegram_id`).
    Callers must never supply a user id.

    Works identically inside or outside the execute_code sandbox --
    :func:`load_credentials` handles the dispatch (direct vault call in the
    trusted process, RPC-mediated fetch inside the sandbox). No caller-facing
    change either way.

    Args:
        api:          e.g. ``"gmail"``, ``"calendar"``, ``"drive"``, ``"sheets"``
        version:      e.g. ``"v1"``, ``"v3"``, ``"v4"``
        service_name: vault service key (e.g. ``"google-draas"``).
    """
    creds = load_credentials(service_name)
    return build(api, version, credentials=creds)


def get_auth_url(login_hint: str = None) -> str:
    """Generate an OAuth authorization URL for the current session's user.

    Identity is derived from the session context ONLY. The callback handler
    will auto-detect which Google account the user authorizes and store the
    token under the correct vault service key -- no need to encode anything
    extra in the OAuth ``state``.

    Hermes is a confidential server-side client (client_secret never leaves
    the server), so PKCE is not needed and is explicitly disabled to avoid
    library-version quirks in the code_verifier exchange.

    Args:
        login_hint:   Email to pre-fill in Google's login form.  If omitted,
                      uses the user's registered email from the user registry.
    """
    tid = _current_telegram_id()

    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        autogenerate_code_verifier=False,
    )

    auth_kwargs = {
        "access_type": "offline",
        "prompt": "consent",
        "state": str(tid),
    }

    if login_hint:
        auth_kwargs["login_hint"] = login_hint
    else:
        try:
            from tools._user_registry import get_user_config
            user = get_user_config(str(tid))
            if user and user.get("email"):
                auth_kwargs["login_hint"] = user["email"]
        except Exception:
            pass

    url, _ = flow.authorization_url(**auth_kwargs)
    return url


def verify_email_ownership(
    account_email: str,
    session_raw_id: str,
) -> bool:
    """Verify that *account_email* belongs to the session user.

    Checks the vault identity record for *session_raw_id*'s canonical uid
    and looks for *account_email* in the record's email list. Returns True
    if the email is associated with the session user, False otherwise.

    This prevents the LLM from using account_email to request another
    user's OAuth token (belt-and-suspenders on top of the vault's own
    session_uid == user_id enforcement at read time).
    """
    try:
        uid = canonical_uid(session_raw_id)
        if not uid:
            return False
        from tools import gws_vault_client as vault
        identity = vault.get_identity(uid, session_uid=uid)
        if not identity:
            return False
        emails = identity.get("identities", {}).get("email", [])
        return account_email in emails
    except Exception:
        logger.debug(
            "verify_email_ownership failed for email=%s session=%s",
            account_email, session_raw_id,
        )
        return False


def _ensure_email_in_identity(uid: str, email: str) -> None:
    """Add *email* to the user's identity record if not already present.

    This ensures secondary authorized emails are linked to the user's
    identity record, which enables ownership checks in tools like
    contact_resolver and gws_resolve_account. Silently skips if the
    vault secret is unavailable (non-admin process).
    """
    if not email or email == uid:
        return
    try:
        from tools import gws_vault_client as vault
        identity = vault.get_identity(uid, session_uid=uid)
        if identity:
            emails = identity.get("identities", {}).get("email", [])
            if email not in emails:
                vault.add_identity(uid, "email", email)
                logger.info(
                    "Linked authorized email %s to user %s", email, uid
                )
    except Exception:
        logger.debug(
            "Could not link email %s to user %s (non-fatal)", email, uid,
        )


def exchange_and_store(code: str, service_name: str | None = None) -> str:
    """Exchange an auth code for tokens and store them in the vault.

    Identity is derived from the session context ONLY. Tokens are keyed by
    the **canonical** vault user_id (resolved from the session's raw channel
    id via :func:`canonical_uid`), so a token authorized from any channel
    (Telegram, Open Web UI) is readable from every channel and the read path
    can satisfy the vault's ``session_uid == user_id`` check.

    The vault service key is chosen from the *authorized* Google account's
    email (decoded from the id_token) via ``EMAIL_TO_SERVICE`` — NOT from any
    profile default — so authorizing a second account never overwrites the
    first.

    Returns the chosen service name (or ``UNKNOWN:{email}:{svc}`` for accounts
    not yet mapped in ``EMAIL_TO_SERVICE``).
    """
    tid = _current_telegram_id()

    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        state=str(tid),
    )
    flow.fetch_token(code=code)

    # Resolve the session's raw channel id → canonical vault user_id.
    uid = canonical_uid(tid)

    # Extract the authorized email from the credentials for ownership tracking.
    authorized_email = _account_email(flow.credentials)

    if service_name is not None:
        save_credentials(flow.credentials, service_name)
        logger.info("GWS token stored user_id=%s service=%s", uid, service_name)
        if authorized_email:
            _ensure_email_in_identity(uid, authorized_email)
        return service_name

    # Service is chosen from the AUTHORIZED account's email so a second
    # account never clobbers the first.  Uses id_token when the openid scope
    # is present, else falls back to the Gmail profile (gmail.modify scope).
    email = authorized_email

    if email:
        svc = EMAIL_TO_SERVICE.get(email)
        if svc:
            save_credentials(flow.credentials, svc)
            _ensure_email_in_identity(uid, email)
            logger.info(
                "GWS token stored user_id=%s service=%s (email=%s)", uid, svc, email
            )
            return svc

        # Unknown email — store under a vault-valid fallback key so the token
        # is never lost.  Service names must match ^[a-z][a-z0-9-]{0,49}$.
        local = re.sub(r"[^a-z0-9-]+", "-", email.split("@")[0].lower()).strip("-") or "acct"
        fallback_svc = f"google-{local}"
        save_credentials(flow.credentials, fallback_svc)
        _ensure_email_in_identity(uid, email)
        logger.info(
            "GWS token stored user_id=%s fallback_service=%s email=%s",
            uid, fallback_svc, email,
        )
        return f"UNKNOWN:{email}:{fallback_svc}"

    # No id_token at all — last resort default key.
    save_credentials(flow.credentials, _DEFAULT_SERVICE)
    logger.warning(
        "No id_token for user_id=%s — stored service=%s",
        uid, _DEFAULT_SERVICE,
    )
    return _DEFAULT_SERVICE


def has_token(service_name: str = _DEFAULT_SERVICE) -> bool:
    """Check if a token exists for the current session's user in the vault.
    Identity is derived from the session context ONLY."""
    from tools import gws_vault_client as vault
    tid = _current_telegram_id()
    uid = canonical_uid(tid)
    return vault.has_token(uid, service_name, session_uid=uid)


def register_email_service(email: str, service_name: str) -> str:
    """Register an email-to-service mapping and rename any fallback token.

    Call this when the user tells the agent what service name to use for an
    account that was authorized under a fallback key (``UNKNOWN:...`` result).
    Identity is derived from the session context ONLY.

    1. Adds ``email -> service_name``  to ``EMAIL_TO_SERVICE``.
    2. If a fallback key ``google-{local}`` exists, moves the token
       to the new service name and deletes the fallback.

    Returns a status message.
    """
    from tools import gws_vault_client as vault

    if not email or not service_name:
        return "Both email and service_name are required."

    EMAIL_TO_SERVICE[email] = service_name

    tid = _current_telegram_id()
    uid = canonical_uid(tid)

    # Check for a fallback key (must match the vault-valid form used above).
    local = re.sub(r"[^a-z0-9-]+", "-", email.split("@")[0].lower()).strip("-") or "acct"
    fallback_svc = f"google-{local}"
    try:
        if vault.has_token(uid, fallback_svc, session_uid=uid):
            raw = vault.get_token(uid, fallback_svc, session_uid=uid)
            vault.set_token(uid, service_name, raw)
            vault.delete_token(uid, fallback_svc)
            return f"Registered {email} -> {service_name} and moved fallback token."
        else:
            return f"Registered {email} -> {service_name} (no fallback token to rename)."
    except Exception as e:
        return f"Registered {email} -> {service_name} but could not migrate token: {e}"
