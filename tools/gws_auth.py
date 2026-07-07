"""
Per-user OAuth token manager for Google Workspace (Gmail, Calendar, Drive).

Tokens are stored in the gws-vault daemon (Unix socket) under per-service keys,
NOT on the filesystem.  Each Google account (email) automatically maps to a
distinct service name so multiple accounts per Telegram user never overwrite
each other.

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

# Default service name for backward compatibility.
_DEFAULT_SERVICE = "google"

# Map well-known emails to their vault service names so the agent
# can look up the right token by email address, and so the OAuth
# callback can auto-detect the service name from the id_token email.
EMAIL_TO_SERVICE = {
    "ndr@draas.com":          "google-draas",
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
        telegram_id:  Telegram numeric ID for the user.
        service_name: Vault service key (e.g. ``"google-draas"``).
    """
    from tools import gws_vault_client as vault
    token_json = vault.get_token(
        str(telegram_id), service_name, session_uid=str(telegram_id)
    )
    creds = Credentials.from_authorized_user_info(
        json.loads(token_json), HERMES_GWS_SCOPES
    )
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        vault.set_token(str(telegram_id), service_name, creds.to_json())
    return creds


def save_credentials(telegram_id: str, creds: Credentials, service_name: str = _DEFAULT_SERVICE) -> None:
    """Store OAuth credentials in the gws-vault daemon under the given service key."""
    from tools import gws_vault_client as vault
    vault.set_token(str(telegram_id), service_name, creds.to_json())


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

    When ``service_name`` is ``None`` (the normal callback case), the
    function auto-detects the Google account email from the returned
    ``id_token`` JWT and looks it up in ``EMAIL_TO_SERVICE``.  The token
    is ALWAYS saved (under a suitable key) so the user never needs to
    re-authorize.

    Resolution priority:
      1. If ``service_name`` is given explicitly, use it.
      2. If the email extracted from the ID token is in
         ``EMAIL_TO_SERVICE``, use the mapped service name.
      3. If the email is known but unmapped, use ``google:{email}`` as a
         fallback key and include the email in the returned value.
      4. If no email can be extracted, use the default ``"google"``.

    Returns the chosen service name.  The caller can inspect the return
    value to detect unknown accounts and prompt the user for a proper name.

    Args:
        telegram_id:  Telegram numeric ID of the user.
        code:         OAuth authorization code from Google's redirect.
        service_name: Optional override.  When ``None`` (default), the
                      service is auto-detected from the Google account
                      email found in the ID token.
    """
    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        state=str(telegram_id),
    )
    flow.fetch_token(code=code)

    if service_name is not None:
        save_credentials(telegram_id, flow.credentials, service_name)
        logger.info("GWS token stored for user %s service %s", telegram_id, service_name)
        return service_name

    # Auto-detect: extract email from id_token JWT
    id_token = getattr(flow.credentials, "id_token", None)
    email = _decode_id_token_email(id_token) if id_token else None

    if email:
        svc = EMAIL_TO_SERVICE.get(email)
        if svc:
            save_credentials(telegram_id, flow.credentials, svc)
            logger.info("GWS token stored for user %s service %s (auto-detected from %s)", telegram_id, svc, email)
            return svc

        # Unknown email — store under a fallback key so the token is not lost
        fallback_svc = f"google:{email.replace('@', '_at_')}"
        save_credentials(telegram_id, flow.credentials, fallback_svc)
        logger.info(
            "GWS token stored for user %s under fallback service %s — "
            "email %s is not in EMAIL_TO_SERVICE",
            telegram_id, fallback_svc, email,
        )
        return f"UNKNOWN:{email}:{fallback_svc}"

    # No id_token — fall back to default
    save_credentials(telegram_id, flow.credentials, _DEFAULT_SERVICE)
    logger.warning(
        "No id_token in credentials for user %s — stored under default service '%s'",
        telegram_id, _DEFAULT_SERVICE,
    )
    return _DEFAULT_SERVICE


def has_token(telegram_id: str, service_name: str = _DEFAULT_SERVICE) -> bool:
    """Check if a token exists for the given user and service in the vault."""
    from tools import gws_vault_client as vault
    return vault.has_token(str(telegram_id), service_name, session_uid=str(telegram_id))


def register_email_service(email: str, service_name: str, telegram_id: str) -> str:
    """Register an email-to-service mapping and rename any fallback token.

    Call this when the user tells the agent what service name to use for an
    account that was authorized under a fallback key (``UNKNOWN:...`` result).

    1. Adds ``email -> service_name``  to ``EMAIL_TO_SERVICE``.
    2. If a fallback key ``google:{email_sanitized}`` exists, moves the token
       to the new service name and deletes the fallback.

    Returns a status message.
    """
    from tools import gws_vault_client as vault

    if not email or not service_name:
        return "Both email and service_name are required."

    EMAIL_TO_SERVICE[email] = service_name

    # Check for a fallback key
    fallback_svc = f"google:{email.replace('@', '_at_')}"
    try:
        if vault.has_token(str(telegram_id), fallback_svc, session_uid=str(telegram_id)):
            raw = vault.get_token(str(telegram_id), fallback_svc, session_uid=str(telegram_id))
            vault.set_token(str(telegram_id), service_name, raw)
            vault.delete_token(str(telegram_id), fallback_svc)
            return f"Registered {email} -> {service_name} and moved fallback token."
        else:
            return f"Registered {email} -> {service_name} (no fallback token to rename)."
    except Exception as e:
        return f"Registered {email} -> {service_name} but could not migrate token: {e}"
