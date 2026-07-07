"""
Per-user OAuth token manager for Google Workspace (Gmail, Calendar, Drive).

Tokens are stored in the gws-vault daemon (Unix socket) under per-service keys,
NOT on the filesystem.  Each Google account (email) gets its own service name
so multiple accounts per Telegram user do not overwrite each other.

Service naming convention:
    google              — default / legacy / primary
    google-draas        — ndr@draas.com
    google-ahfl         — ndr@ahfl.in
    google-gmail        — nishantranka@gmail.com

Usage from skill code (terminal or execute_code):
    from tools.gws_auth import build_service, get_auth_url
    svc = build_service("gmail", "v1")                   # default service
    svc = build_service("gmail", "v1", service_name="google-ahfl")
    url = get_auth_url(telegram_id)                      # default service
    url = get_auth_url(telegram_id, login_hint="ndr@ahfl.in", service_name="google-ahfl")

The session telegram_id is read from HERMES_SESSION_USER_ID env var,
which is injected into every subprocess by the gateway.
"""

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
# can look up the right token by email address.
EMAIL_TO_SERVICE = {
    "ndr@draas.com":          "google-draas",
    "ndr@ahfl.in":            "google-ahfl",
    "nishantranka@gmail.com": "google-gmail",
}


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


def get_auth_url(telegram_id: str, login_hint: str = None, service_name: str = _DEFAULT_SERVICE) -> str:
    """Generate an OAuth authorization URL for a user.

    Hermes is a confidential server-side client (client_secret never leaves
    the server), so PKCE is not needed and is explicitly disabled to avoid
    library-version quirks in the code_verifier exchange.

    The ``service_name`` is encoded into the OAuth ``state`` parameter so the
    callback handler can store the token under the correct vault key.  When
    omitted, the state is just the telegram_id (backward compatible).

    Args:
        telegram_id:  Telegram numeric ID of the user authorizing.
        login_hint:   Email to pre-fill in Google's login form.  If omitted,
                      uses the user's registered email from the user registry.
        service_name: Vault service key to store the token under.  Defaults to
                      ``"google"``.
    """
    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        autogenerate_code_verifier=False,
    )

    # Encode service_name into the state parameter so the callback knows
    # which vault key to write to.
    state_value = f"{telegram_id}:{service_name}" if service_name != _DEFAULT_SERVICE else str(telegram_id)
    auth_kwargs = {
        "access_type": "offline",
        "prompt": "consent",
        "state": state_value,
    }

    # Pre-fill the email in the Google login form.
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


def exchange_and_store(telegram_id: str, code: str, service_name: str = _DEFAULT_SERVICE) -> None:
    """Exchange an auth code for tokens and store them in the vault.

    Args:
        telegram_id:  Telegram numeric ID of the user.
        code:         OAuth authorization code from Google's redirect.
        service_name: Vault service key to store under.
    """
    state_value = f"{telegram_id}:{service_name}" if service_name != _DEFAULT_SERVICE else str(telegram_id)
    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        state=state_value,
    )
    flow.fetch_token(code=code)
    save_credentials(telegram_id, flow.credentials, service_name)
    logger.info("GWS token stored for user %s service %s", telegram_id, service_name)


def has_token(telegram_id: str, service_name: str = _DEFAULT_SERVICE) -> bool:
    """Check if a token exists for the given user and service in the vault."""
    from tools import gws_vault_client as vault
    return vault.has_token(str(telegram_id), service_name, session_uid=str(telegram_id))
