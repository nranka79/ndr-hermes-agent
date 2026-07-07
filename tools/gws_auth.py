"""
Per-user OAuth token manager for Google Workspace (Gmail, Calendar, Drive).

Tokens are stored in the gws-vault daemon (Unix socket), NOT on the filesystem.
Read/write access goes through gws_vault_client.py.

Usage from skill code (terminal or execute_code):
    from tools.gws_auth import build_service, get_auth_url
    svc = build_service("gmail", "v1")          # uses current session user
    svc = build_service("calendar", "v3")
    url = get_auth_url(telegram_id)             # generate auth link

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


def load_credentials(telegram_id: str) -> Credentials:
    """Load stored OAuth credentials for a user from the gws-vault daemon.

    Raises FileNotFoundError if no token exists -- caller should direct
    the user to authorize via get_auth_url().
    """
    from tools import gws_vault_client as vault
    token_json = vault.get_token(
        str(telegram_id), "google", session_uid=str(telegram_id)
    )
    creds = Credentials.from_authorized_user_info(
        json.loads(token_json), HERMES_GWS_SCOPES
    )
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        vault.set_token(str(telegram_id), "google", creds.to_json())
    return creds


def save_credentials(telegram_id: str, creds: Credentials) -> None:
    """Store OAuth credentials in the gws-vault daemon."""
    from tools import gws_vault_client as vault
    vault.set_token(str(telegram_id), "google", creds.to_json())


def build_service(api: str, version: str, telegram_id: str = None):
    """
    Build a Google API client using the stored per-user OAuth token.

    Args:
        api:         e.g. "gmail", "calendar", "drive", "sheets"
        version:     e.g. "v1", "v3", "v4"
        telegram_id: override; defaults to HERMES_SESSION_USER_ID env var
    """
    tid = telegram_id or _current_telegram_id()
    creds = load_credentials(tid)
    return build(api, version, credentials=creds)


def get_auth_url(telegram_id: str) -> str:
    """Generate an OAuth authorization URL for a user.

    Hermes is a confidential server-side client (client_secret never leaves
    the server), so PKCE is not needed and is explicitly disabled to avoid
    library-version quirks in the code_verifier exchange.
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
    # Pre-fill the user's @draas.com email in the Google login form if known.
    try:
        from tools._user_registry import get_user_config
        user = get_user_config(str(telegram_id))
        if user and user.get("email"):
            auth_kwargs["login_hint"] = user["email"]
    except Exception:
        pass

    url, _ = flow.authorization_url(**auth_kwargs)
    return url


def exchange_and_store(telegram_id: str, code: str) -> None:
    """Exchange an auth code for tokens and store them in the vault."""
    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        state=str(telegram_id),
    )
    flow.fetch_token(code=code)
    save_credentials(telegram_id, flow.credentials)
    logger.info("GWS token stored for user %s", telegram_id)


def has_token(telegram_id: str) -> bool:
    """Check if a token exists for the given user in the vault."""
    from tools import gws_vault_client as vault
    return vault.has_token(str(telegram_id), "google", session_uid=str(telegram_id))
