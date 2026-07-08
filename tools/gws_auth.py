"""
Per-user OAuth token manager for Google Workspace (Gmail, Calendar, Drive).

Tokens are stored in the gws-vault daemon (Unix socket) under per-service keys,
NOT on the filesystem.  Each Google account (email) automatically maps to a
distinct service name so multiple accounts per Telegram user never overwrite
each other.

Tokens are keyed by the **canonical** vault user_id — a channel-agnostic
surrogate (e.g. ``ndr-7449813913``) resolved from the session's raw channel
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
    url = get_auth_url(telegram_id)                      # default service
    url = get_auth_url(telegram_id, login_hint="ndr@ahfl.in",
                       service_name="google-ahfl")

The session telegram_id is read from HERMES_SESSION_USER_ID env var,
which is injected into every subprocess by the gateway.
"""

import base64
import json
import logging
import os
import re

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

logger = logging.getLogger(__name__)

# All scopes granted once; user authorizes the full set at first login.
HERMES_GWS_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
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
    """Get the telegram_id of the active session user."""
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
    ``ndr-7449813913``) stored in the vault identity records.  Every raw
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
    except Exception:
        logger.debug("canonical_uid: vault resolve failed for %r", cid, exc_info=True)
    return cid


def _parse_state(state: str) -> tuple[str, str]:
    """Parse the OAuth state parameter.

    Supports two formats:
      ``"7449813913"``                    → (telegram_id, "google")
      ``"7449813913:google-ahfl"``         → (telegram_id, "google-ahfl")

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


def load_credentials(telegram_id: str, service_name: str = _DEFAULT_SERVICE) -> Credentials:
    """Load stored OAuth credentials for a user from the gws-vault daemon.

    Raises :class:`FileNotFoundError` if no token exists -- caller should
    direct the user to authorize via :func:`get_auth_url`.

    Args:
        telegram_id:  Session's raw channel id (Telegram numeric id, etc.).
                      Resolved to the canonical vault user_id internally.
        service_name: Vault service key (e.g. ``"google-draas"``).
    """
    from tools import gws_vault_client as vault
    uid = canonical_uid(telegram_id)
    token_json = vault.get_token(uid, service_name, session_uid=uid)
    creds = Credentials.from_authorized_user_info(
        json.loads(token_json), HERMES_GWS_SCOPES
    )
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        vault.set_token(uid, service_name, creds.to_json())
    return creds


def save_credentials(user_id: str, creds: Credentials, service_name: str = _DEFAULT_SERVICE) -> None:
    """Store OAuth credentials in the gws-vault daemon under the given service key.

    ``user_id`` must already be the canonical vault user_id (callers resolve it
    via :func:`canonical_uid` before storing).
    """
    from tools import gws_vault_client as vault
    vault.set_token(str(user_id), service_name, creds.to_json())


def build_service(api: str, version: str, telegram_id: str = None, service_name: str = _DEFAULT_SERVICE):
    """
    Build a Google API client using the stored per-user OAuth token.

    Args:
        api:          e.g. ``"gmail"``, ``"calendar"``, ``"drive"``, ``"sheets"``
        version:      e.g. ``"v1"``, ``"v3"``, ``"v4"``
        telegram_id:  override; defaults to ``HERMES_SESSION_USER_ID`` env var
        service_name: vault service key (e.g. ``"google-draas"``).
    """
    tid = telegram_id or _current_telegram_id()
    creds = load_credentials(tid, service_name)
    return build(api, version, credentials=creds)


def get_auth_url(telegram_id: str, login_hint: str = None) -> str:
    """Generate an OAuth authorization URL for a user.

    Hermes is a confidential server-side client (client_secret never leaves
    the server), so PKCE is not needed and is explicitly disabled to avoid
    library-version quirks in the code_verifier exchange.

    The callback handler will auto-detect which Google account the user
    authorizes and store the token under the correct vault service key --
    no need to encode anything extra in the OAuth ``state``.

    Args:
        telegram_id:  Telegram numeric ID of the user authorizing.
        login_hint:   Email to pre-fill in Google's login form.  If omitted,
                      uses the user's registered email from the user registry.
    """
    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        autogenerate_code_verifier=False,
    )

    auth_kwargs = {
        "access_type": "offline",
        "prompt": "consent",
        "state": str(telegram_id),
    }

    if login_hint:
        auth_kwargs["login_hint"] = login_hint
    else:
        try:
            from tools._user_registry import get_user_config
            user = get_user_config(str(telegram_id))
            if user and user.get("email"):
                auth_kwargs["login_hint"] = user["email"]
        except Exception:
            pass

    url, _ = flow.authorization_url(**auth_kwargs)
    return url


def exchange_and_store(telegram_id: str, code: str, service_name: str | None = None) -> str:
    """Exchange an auth code for tokens and store them in the vault.

    Tokens are keyed by the **canonical** vault user_id (resolved from the
    session's raw channel id via :func:`canonical_uid`), so a token authorized
    from any channel (Telegram, Open WebUI) is readable from every channel and
    the read path can satisfy the vault's ``session_uid == user_id`` check.

    The vault service key is chosen from the *authorized* Google account's
    email (decoded from the id_token) via ``EMAIL_TO_SERVICE`` — NOT from any
    profile default — so authorizing a second account never overwrites the
    first.

    Returns the chosen service name (or ``UNKNOWN:{email}:{svc}`` for accounts
    not yet mapped in ``EMAIL_TO_SERVICE``).
    """
    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        state=str(telegram_id),
    )
    flow.fetch_token(code=code)

    # Resolve the session's raw channel id → canonical vault user_id.
    uid = canonical_uid(telegram_id)

    if service_name is not None:
        save_credentials(uid, flow.credentials, service_name)
        logger.info("GWS token stored user_id=%s service=%s", uid, service_name)
        return service_name

    # Service is chosen from the AUTHORIZED account's email so a second
    # account never clobbers the first.
    id_token = getattr(flow.credentials, "id_token", None)
    email = _decode_id_token_email(id_token) if id_token else None

    if email:
        svc = EMAIL_TO_SERVICE.get(email)
        if svc:
            save_credentials(uid, flow.credentials, svc)
            logger.info(
                "GWS token stored user_id=%s service=%s (email=%s)", uid, svc, email
            )
            return svc

        # Unknown email — store under a vault-valid fallback key so the token
        # is never lost.  Service names must match ^[a-z][a-z0-9-]{0,49}$.
        local = re.sub(r"[^a-z0-9-]+", "-", email.split("@")[0].lower()).strip("-") or "acct"
        fallback_svc = f"google-{local}"
        save_credentials(uid, flow.credentials, fallback_svc)
        logger.info(
            "GWS token stored user_id=%s fallback_service=%s email=%s",
            uid, fallback_svc, email,
        )
        return f"UNKNOWN:{email}:{fallback_svc}"

    # No id_token at all — last resort default key.
    save_credentials(uid, flow.credentials, _DEFAULT_SERVICE)
    logger.warning(
        "No id_token for telegram_id=%s — stored user_id=%s service=%s",
        telegram_id, uid, _DEFAULT_SERVICE,
    )
    return _DEFAULT_SERVICE


def has_token(telegram_id: str, service_name: str = _DEFAULT_SERVICE) -> bool:
    """Check if a token exists for the given user and service in the vault."""
    from tools import gws_vault_client as vault
    uid = canonical_uid(telegram_id)
    return vault.has_token(uid, service_name, session_uid=uid)


def register_email_service(email: str, service_name: str, telegram_id: str) -> str:
    """Register an email-to-service mapping and rename any fallback token.

    Call this when the user tells the agent what service name to use for an
    account that was authorized under a fallback key (``UNKNOWN:...`` result).

    1. Adds ``email -> service_name``  to ``EMAIL_TO_SERVICE``.
    2. If a fallback key ``google-{local}`` exists, moves the token
       to the new service name and deletes the fallback.

    Returns a status message.
    """
    from tools import gws_vault_client as vault

    if not email or not service_name:
        return "Both email and service_name are required."

    EMAIL_TO_SERVICE[email] = service_name

    uid = canonical_uid(telegram_id)

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
